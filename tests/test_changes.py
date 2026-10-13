"""The change log and memory rules (bot spec §5): the "Thay đổi" rows, the stored state, kept proposals. Pure."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime

from scrumbot.model import Assignment, Order, Priority, Size, SizeEstimate, Source, SprintRow
from scrumbot.model_risk import ChangeKind, KeptProposal, OrderMark, Outcome
from scrumbot.rules.changes import change_rows, marks
from scrumbot.rules.proposals import restore, settle, with_kept
from tests.api_builders import AN, LINH, MINH, OUTSIDER, POOL

AT = datetime(2026, 10, 13, 9, 30)


def order(stt: int, *, people: tuple[str, ...] = (), title: str | None = None, priority: str = "", due=None) -> Order:
    row = SprintRow(
        stt, title or f"Order {stt}", "Task", "Demo", people, "", priority, due, None, "", (), None, f"o{stt}"
    )
    return Order(row, Priority.NORMAL)


def held(item: Order, source: Source = Source.PREASSIGNED, codes: tuple[str, ...] = ()) -> Assignment:
    return Assignment(item, SizeEstimate(Size.M, "", False), source, item.row.assignees, codes, "r", ())


def test_change_rows_report_each_kind_with_codes_only() -> None:
    now = (
        held(order(1, people=(LINH,), priority="urgent")),  # priority changed
        held(order(2, people=(MINH, OUTSIDER), due=date(2026, 10, 15))),  # due changed, people changed
        held(order(3, title="1.0.2")),  # renamed
        held(order(4)),  # new
        held(order(5, people=(AN,))),  # proposed before, now assigned by the TM
        held(order(6, people=(OUTSIDER,))),  # only people outside the pool changed: silent (D14)
    )
    stored = (
        OrderMark("o1", "Order 1", "", None, ("LinhNV",)),
        OrderMark("o2", "Order 2", "", None, ()),
        OrderMark("o3", "1.0.1", "", None, ()),
        OrderMark("o5", "Order 5", "", None, ()),
        OrderMark("o6", "Order 6", "", None, ()),
        OrderMark("o9", "Gone", "", None, ()),
    )
    outcomes = (Outcome("o5", "Order 5", "MinhNM", ("AnTD",), AT),)

    rows = [(c.kind, c.order, c.before, c.after) for c in change_rows(now, stored, outcomes, POOL)]

    assert rows == [
        (ChangeKind.NEW, "STT 4 · Order 4", "—", "Order 4 [M]"),
        (ChangeKind.REMOVED, "Gone", "Gone", "—"),
        (ChangeKind.PRIORITY, "STT 1 · Order 1", "trống", "urgent"),
        (ChangeKind.DUE, "STT 2 · Order 2", "trống", "15/10/2026"),
        (ChangeKind.TITLE, "STT 3 · 1.0.2", "1.0.1", "1.0.2"),
        (ChangeKind.TM_ASSIGNED, "STT 5 · Order 5", "MinhNM", "AnTD (khác đề xuất)"),
        (ChangeKind.PEOPLE, "STT 2 · Order 2", "trống", "MinhNM"),
    ]


def test_marks_store_title_priority_due_and_pool_codes_of_orders_with_an_id() -> None:
    item = held(order(1, people=(LINH, OUTSIDER), priority="high", due=date(2026, 10, 15)))
    no_id = held(Order(replace(order(2).row, id=""), Priority.NORMAL))

    assert marks((item, no_id), POOL) == (OrderMark("o1", "Order 1", "high", date(2026, 10, 15), ("LinhNV",)),)


def test_settle_keeps_standing_proposals_and_turns_assigned_ones_into_outcomes() -> None:
    kept = (
        KeptProposal("o1", "LinhNV", "why", ("MinhNM",), AT),
        KeptProposal("o2", "AnTD", "why", (), AT),
        KeptProposal("o9", "AnTD", "why", (), AT),  # the order left the sprint
    )
    orders = (order(1), order(2, people=(AN,)))

    standing, outcomes = settle(kept, orders, POOL, AT)

    assert list(standing) == [1]
    assert outcomes == (Outcome("o2", "Order 2", "AnTD", ("AnTD",), AT),) and outcomes[0].matched


def test_a_kept_proposal_enters_section_7_as_preassigned_and_comes_back_as_a_proposal() -> None:
    proposal = KeptProposal("o1", "LinhNV", "Làm version gần nhất", ("MinhNM",), AT)
    orders = (order(1), order(2))

    for_rule, used = with_kept(orders, {1: proposal}, POOL)
    restored = restore(tuple(held(o, codes=("LinhNV",) if o.row.assignees else ()) for o in for_rule), orders, used)

    assert for_rule[0].row.assignees == (LINH,) and not for_rule[1].row.assignees
    first = restored[0]
    assert (first.source, first.kept, first.backups, first.order.row.assignees) == (
        Source.PROPOSED,
        True,
        ("MinhNM",),
        (),
    )
    assert first.reason == "Giữ đề xuất từ 13/10/2026 09:30 · Làm version gần nhất"
    assert with_kept(orders, {1: replace(proposal, code="Nobody")}, POOL)[1] == {}  # dev left the pool: chosen again
