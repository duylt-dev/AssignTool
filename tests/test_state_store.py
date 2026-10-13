"""The memory between runs (bot spec §5, A51): each table round-trips through a real SQLite file."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from scrumbot.actions.state_store import StateStore
from scrumbot.model import Size, SizeEstimate
from scrumbot.model_risk import KeptProposal, OrderMark, Outcome

AT = datetime(2026, 10, 13, 9, 30)


def test_proposals_round_trip_and_can_be_forgotten(tmp_path: Path) -> None:
    store = StateStore(tmp_path)
    store.save_proposals("S10", (KeptProposal("o1", "LinhNV", "lý do", ("MinhNM", "AnTD"), AT),))
    store.save_proposals("S10", (KeptProposal("o1", "AnTD", "mới", (), AT),))  # replaced, not doubled

    assert StateStore(tmp_path).proposals("S10") == (KeptProposal("o1", "AnTD", "mới", (), AT),)
    store.forget_proposals(("o1",))
    assert store.proposals("S10") == ()


def test_ai_answers_are_found_by_id_and_title_casefolded_and_defaults_are_never_kept(tmp_path: Path) -> None:
    store = StateStore(tmp_path)
    store.save_ai_answers(
        {
            ("o1", "1.0.1 - Add Ads"): SizeEstimate(Size.L, "Thêm ads", False, "ads", ("Add ads",), ("SDK mới",)),
            ("o2", "x"): SizeEstimate(Size.M, "", True),
        },
        "agy",
        AT,
    )

    found = store.ai_answers([("o1", "1.0.1 -   add ads"), ("o1", "1.0.2 - Add ads"), ("o2", "x")])

    assert found == {
        ("o1", "1.0.1 -   add ads"): SizeEstimate(Size.L, "Thêm ads", False, "ads", ("Add ads",), ("SDK mới",), True)
    }


def test_the_baseline_is_the_latest_state_before_today_and_only_two_days_are_kept(tmp_path: Path) -> None:
    store = StateStore(tmp_path)
    for day in (10, 11, 12, 13):
        store.save_marks(
            "S10", (OrderMark("o1", f"day {day}", "", date(2026, 10, 17), ("LinhNV",)),), datetime(2026, 10, day, 9)
        )

    marks, stored_at = store.baseline("S10", date(2026, 10, 13))

    assert [mark.title for mark in marks] == ["day 12"] and stored_at == datetime(2026, 10, 12, 9)
    assert store.baseline("S10", date(2026, 10, 12)) is None  # day 11 was pruned: only 12 and 13 remain
    assert store.baseline("S9", date(2026, 10, 13)) is None


def test_outcomes_runs_and_sprint_ends(tmp_path: Path) -> None:
    store = StateStore(tmp_path)
    store.save_outcomes("S10", (Outcome("o1", "Order 1", "LinhNV", ("LinhNV",), AT),))
    store.record_run("S10", "full", "fp1", ("CAPACITY-DEV|LinhNV",), ("o1",), "a.xlsx", AT)
    store.record_run("S10", "quick", "fp1", (), (), "", datetime(2026, 10, 13, 10))

    assert store.outcomes("S10", date(2026, 10, 13)) == (Outcome("o1", "Order 1", "LinhNV", ("LinhNV",), AT),)
    assert store.outcomes("S10", date(2026, 10, 14)) == ()
    assert store.full_run_on(date(2026, 10, 13)) and not store.full_run_on(date(2026, 10, 14))
    assert store.last_report("S10") == ("fp1", ("CAPACITY-DEV|LinhNV",), ("o1",))
    assert not store.sprint_end_done("S9")
    store.record_sprint_end("S9", "end.xlsx", AT)
    assert store.sprint_end_done("S9")
