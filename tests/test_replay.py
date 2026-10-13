"""The replay on a copy (bot spec §8, D55, D56): the pool by join date, carried and compared orders, filing days,
outcomes, checkpoints and scores. Built on synthetic API replies; pure."""

from __future__ import annotations

from datetime import date, datetime

from scrumbot.model_board import TECH_MANAGER_LIST
from scrumbot.rules.replay import joined, percent, replay_assignments
from scrumbot.rules.replay_risks import lead_days, replay_risks, scores
from scrumbot.sources.api_reader import read_board
from tests.api_builders import AN, LINH, MINH, POOL, TIEN, history, item, orders, sprint, sprints

S9 = sprint("S9", "Sprint 9 (9/21 - 10/2)", date(2026, 9, 21), date(2026, 10, 2), archived=True, total=2)
S10 = sprint("S10", "Sprint 10 (10/6 - 10/17)", date(2026, 10, 6), date(2026, 10, 17), total=3)
ROBLOX = item("a", "1.0.4", people=(AN,), app="Roblox", status="done", created=datetime(2026, 9, 20, 9))
PS = item("b", "1.1.1", people=(MINH, LINH), app="PS Remote", status="in progress", created=datetime(2026, 9, 19, 9))
NEXT = item("c", "1.0.5", people=(AN,), app="Roblox", status="done", created=datetime(2026, 10, 1, 9))
LATE = item(
    "d",
    "1.0.0",
    people=(TIEN,),
    app="New",
    status="ready to progress",
    priority="urgent",
    due=date(2026, 10, 9),
    created=datetime(2026, 10, 8, 9),
)


def _board():
    return read_board(
        sprints(S9, S10),
        {
            "S9": orders(ROBLOX, PS),
            "S10": orders(PS, NEXT, LATE),
            TECH_MANAGER_LIST: orders(ROBLOX, PS, NEXT, LATE),
        },
        history(("c", "in progress", "done", datetime(2026, 10, 20, 10))),
        datetime(2026, 10, 21, 9),
        "Bản sao test",
    )


def test_a_dev_joins_the_pool_with_the_first_sprint_where_they_are_pic() -> None:
    assert joined(_board(), POOL) == {
        "AnTD": date(2026, 9, 21),
        "MinhNM": date(2026, 9, 21),
        "LinhNV": date(2026, 9, 21),
        "TiếnBV": date(2026, 10, 6),
    }


def test_assignments_compare_new_orders_keep_carried_ones_and_follow_familiarity() -> None:
    s9, s10 = replay_assignments(_board(), POOL, (), {})

    assert s9.pool == ("LinhNV", "MinhNM", "AnTD") and s9.kept == 0
    assert [(r.order.row.id, r.tm_codes) for r in s9.orders] == [("b", ("LinhNV", "MinhNM")), ("a", ("AnTD",))]
    assert s10.pool == ("LinhNV", "MinhNM", "AnTD", "TiếnBV") and s10.kept == 1  # PS Remote carried from Sprint 9
    by_id = {r.order.row.id: r for r in s10.orders}
    assert list(by_id) == ["c", "d"]  # filed 01/10 (assigned on 06/10), then 08/10
    assert by_id["c"].assignment.pic_codes == ("AnTD",) and by_id["c"].matched  # built Roblox 1.0.4
    assert by_id["c"].assignment.reason.startswith("Làm version gần nhất của Roblox (Sprint 9 (9/21 - 10/2): 1.0.4)")


def test_risks_flag_the_overdue_order_at_the_checkpoint_after_it_was_filed_and_score_it() -> None:
    (s10,) = replay_risks(_board(), POOL, (), {}, only=next(s for s in _board().sprints if s.id == "S10"))

    assert [point.at for point in s10.checkpoints] == [
        datetime(2026, 10, 6, 8, 30),
        datetime(2026, 10, 12, 8, 30),
        datetime(2026, 10, 14, 8, 30),
    ]
    outcomes = {item.order.row.id: item for item in s10.outcomes}
    assert outcomes["c"].reasons == ("xong sau ngày kết thúc",)
    assert outcomes["d"].reasons == ("chưa xong",)
    assert ("DUE-AT-RISK", date(2026, 10, 12)) in outcomes["d"].flagged
    assert s10.has_history

    rows = {score.code: score for score in scores((s10,))}
    due = rows["DUE-AT-RISK"]
    assert (due.flagged, due.flagged_bad, due.bad_flagged, due.lead_median) == (1, 1, 1, 5.0)
    assert rows["Mọi loại"].bad == 3  # c done after the end; d and the carried b not done
    assert lead_days(date(2026, 10, 12), date(2026, 10, 17)) == 5


def test_percent_rounds_half_up() -> None:
    assert (percent(5, 8), percent(1, 3), percent(2, 3)) == (63, 33, 67)
