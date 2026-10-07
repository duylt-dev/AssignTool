"""Backtest (D22, A29): replay every Maintain sprint of the history file and compare the tool with the TM. Pure."""

from __future__ import annotations

from datetime import date

from assigntool.model import BacktestOrder, BacktestSprint, Dev, HistoryOrder, Order, Priority, SprintLabel, SprintRow
from assigntool.normalize import parse_priority, text_key
from assigntool.rules.assign import assign
from assigntool.rules.familiarity import FamiliarityIndex
from assigntool.rules.history_window import history_for
from assigntool.rules.leave import leave_count, on_leave_all_sprint, working_days
from assigntool.rules.sizing import default_sizes

MAINTAIN_MAX_DAYS = 21  # A21: Maintain sprints last 4–17 days in the data, MVP / research sprints 27–54
PREV_NAME = "sprint trước"  # carry-over is 0 in a backtest (A29); this only fills the reason text

_Item = tuple[int, HistoryOrder]  # (STT given to the order in the replay, order)


def percent(matched: int, total: int) -> int:
    """Match rate rounded half up (5/8 -> 63), unlike round()'s half-to-even."""
    return (200 * matched + total) // (2 * total)


def is_maintain(label: SprintLabel) -> bool:
    return (label.end - label.start).days <= MAINTAIN_MAX_DAYS


def maintain_sprints(history: tuple[HistoryOrder, ...]) -> tuple[SprintLabel, ...]:
    """Every distinct Maintain sprint named in the history, oldest first."""
    labels = {label for order in history for label in order.sprints if is_maintain(label)}
    return tuple(sorted(labels, key=lambda label: (label.start, label.end, label.number)))


def backtest(history: tuple[HistoryOrder, ...], devs: tuple[Dev, ...]) -> tuple[BacktestSprint, ...]:
    return tuple(_replay(label, history, devs) for label in maintain_sprints(history))


def _replay(label: SprintLabel, history: tuple[HistoryOrder, ...], devs: tuple[Dev, ...]) -> BacktestSprint:
    days = working_days(label.start, label.end)
    active = tuple(dev for dev in devs if dev.active)
    pool = tuple(dev for dev in active if not on_leave_all_sprint(dev, days))
    members = [(stt, order) for stt, order in enumerate(history, start=1) if label in order.sprints]
    named = [(stt, order) for stt, order in members if _codes(order, active)]
    kept = [item for item in named if _carried(item[1], label)]
    replayed = [item for item in named if not _carried(item[1], label)]
    if not pool:
        return BacktestSprint(label, (), len(kept))

    leave = {dev.code: leave_count(dev, days) for dev in active}
    carry = {dev.code: 0 for dev in active}
    chosen: dict[int, str] = {}  # STT -> full name of the dev the tool chose
    results: list[BacktestOrder] = []
    for day, batch in _batches(replayed, label.start):
        fam = FamiliarityIndex.build(history_for(history, label.number, label.start, label.end, day), pool)
        orders = (
            *(_order(stt, order, order.assignees) for stt, order in kept),
            *(_order(stt, order, (chosen[stt],)) for stt, order in replayed if stt in chosen),
            *(_order(stt, order, ()) for stt, order in batch),
        )
        by_stt = {
            item.order.row.stt: item
            for item in assign(orders, default_sizes(orders), pool, fam, carry, leave, PREV_NAME)
        }
        for stt, order in sorted(batch, key=lambda item: (item[1].created, item[0])):
            assignment = by_stt[stt]
            chosen[stt] = assignment.pic_names[0]
            results.append(BacktestOrder(order, _codes(order, active), assignment))
    return BacktestSprint(label, tuple(results), len(kept))


def _batches(items: list[_Item], start: date) -> list[tuple[date, list[_Item]]]:
    """One run per filing day (D2); orders filed before the sprint starts are all assigned on its first day."""
    groups: dict[date, list[_Item]] = {}
    for item in items:
        groups.setdefault(max(item[1].created, start), []).append(item)
    return sorted(groups.items())


def _carried(order: HistoryOrder, label: SprintLabel) -> bool:
    """The order was already in an earlier Maintain sprint, so the TM did not assign it for this one."""
    return any(is_maintain(other) and other.start < label.start for other in order.sprints)


def _codes(order: HistoryOrder, devs: tuple[Dev, ...]) -> tuple[str, ...]:
    names = {text_key(name) for name in order.assignees}
    return tuple(dev.code for dev in devs if text_key(dev.name) in names)


def _order(stt: int, order: HistoryOrder, assignees: tuple[str, ...]) -> Order:
    row = SprintRow(
        stt, order.title, "Task", order.app, assignees, "", order.priority_raw, order.due, order.created, "", ()
    )
    priority = parse_priority(order.priority_raw)  # not `or`: Priority.URGENT is 0, so falsy
    return Order(row, Priority.NORMAL if priority is None else priority)
