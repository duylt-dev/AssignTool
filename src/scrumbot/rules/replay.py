"""The replay on a copy of old data (bot spec §8.1, D55): assign every Maintain sprint again and compare with the TM.
The risk half is in `replay_risks.py`. Pure."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from datetime import date, datetime, time

from scrumbot.model import (
    Dev,
    Order,
    Priority,
    Size,
    SizeEstimate,
    SprintRow,
    TeamRule,
)
from scrumbot.model_board import Board, SprintInfo
from scrumbot.model_risk import (
    ReplayOrder,
    ReplaySprint,
)
from scrumbot.normalize import parse_priority, text_key
from scrumbot.rules.assign import assign
from scrumbot.rules.board import history_orders, label_of, maintain_sprints, previous_of, sprint_sheet
from scrumbot.rules.familiarity import FamiliarityIndex
from scrumbot.rules.history_window import history_for
from scrumbot.rules.leave import leave_count, on_leave_all_sprint, working_days
from scrumbot.rules.team_rules import in_force
from scrumbot.rules.timeline import carry_at

PREV_FALLBACK = "sprint trước"

Sizes = Mapping[str, SizeEstimate]  # order id -> size; missing ids are M (A69)
_DEFAULT = SizeEstimate(Size.M, "", True)


def percent(matched: int, total: int) -> int:
    """Rate rounded half up (5/8 -> 63), unlike round()'s half-to-even."""
    return (200 * matched + total) // (2 * total)


def joined(board: Board, devs: tuple[Dev, ...]) -> dict[str, date]:
    """The start of the first sprint in which each active dev is PIC on a root order (D55)."""
    first: dict[str, date] = {}
    for sprint in maintain_sprints(board.sprints):
        sheet = sprint_sheet(board, sprint)
        for row in sheet.rows:
            if row.kind != "Task":
                continue
            names = {text_key(name) for name in row.assignees}
            for dev in devs:
                if dev.active and text_key(dev.name) in names and dev.code not in first:
                    first[dev.code] = sprint.start  # type: ignore[assignment]
    return first


def replay_assignments(
    board: Board, devs: tuple[Dev, ...], rules: tuple[TeamRule, ...], sizes: Sizes
) -> tuple[ReplaySprint, ...]:
    """Bot spec §8.1, oldest sprint first."""
    sprints = maintain_sprints(board.sprints)
    history = history_orders(board)
    first = joined(board, devs)
    seen: set[str] = set()
    results = []
    for sprint in sprints:
        sheet = sprint_sheet(board, sprint)
        roots = [row for row in sheet.rows if row.kind == "Task"]
        members = pool_members(devs, first, sprint)
        named = [row for row in roots if codes_of(row.assignees, members)]
        kept = [row for row in named if row.id in seen]
        replayed = [row for row in named if row.id not in seen]
        seen.update(row.id for row in roots)
        days = working_days(sprint.start, sprint.end)
        pool = tuple(dev for dev in members if not on_leave_all_sprint(dev, days))
        label = label_of(sprint)
        if not pool:
            results.append(ReplaySprint(label, (), (), len(kept)))
            continue
        leave = {dev.code: leave_count(dev, days) for dev in members}
        previous = previous_of(board.sprints, sprint)
        start = datetime.combine(sprint.start, time())  # type: ignore[arg-type]
        carry = carry_at(
            sprint_sheet(board, previous) if previous else None,
            start,
            members,
            {row.id for row in roots},
            board.status_kinds,
        )
        prev_name = previous.name if previous else PREV_FALLBACK
        chosen: dict[int, str] = {}
        compared: list[ReplayOrder] = []
        for day, batch in _batches(replayed, sprint.start):  # type: ignore[arg-type]
            fam = FamiliarityIndex.build(history_for(history, label.number, sprint.start, sprint.end, day), pool)
            orders = (
                *(order_of(row, row.assignees) for row in kept),
                *(order_of(row, (chosen[row.stt],)) for row in replayed if row.stt in chosen),
                *(order_of(row, ()) for row in batch),
            )
            by_stt = {
                item.order.row.stt: item
                for item in assign(
                    orders, sizes_of(orders, sizes), pool, fam, carry, leave, prev_name, in_force(rules, day)
                )
            }
            for row in batch:
                item = by_stt[row.stt]
                chosen[row.stt] = item.pic_names[0]
                compared.append(ReplayOrder(order_of(row, row.assignees), codes_of(row.assignees, members), item))
        results.append(ReplaySprint(label, tuple(dev.code for dev in pool), tuple(compared), len(kept)))
    return tuple(results)


def pool_members(devs: tuple[Dev, ...], first: dict[str, date], sprint: SprintInfo) -> tuple[Dev, ...]:
    return tuple(
        dev
        for dev in devs
        if dev.active and dev.code in first and sprint.start is not None and first[dev.code] <= sprint.start
    )


def codes_of(names: tuple[str, ...], devs: tuple[Dev, ...]) -> tuple[str, ...]:
    keys = {text_key(name) for name in names}
    return tuple(dev.code for dev in devs if text_key(dev.name) in keys)


def order_of(row: SprintRow, assignees: tuple[str, ...]) -> Order:
    priority = parse_priority(row.priority_raw)  # not `or`: Priority.URGENT is 0, so falsy
    return Order(replace(row, assignees=assignees), Priority.NORMAL if priority is None else priority)


def sizes_of(orders: tuple[Order, ...], sizes: Sizes) -> dict[int, SizeEstimate]:
    return {order.row.stt: sizes.get(order.row.id, _DEFAULT) for order in orders}


def _batches(rows: list[SprintRow], start: date) -> list[tuple[date, list[SprintRow]]]:
    """One run per filing day (D2); orders filed before the sprint starts are all assigned on its first day."""
    groups: dict[date, list[SprintRow]] = {}
    for row in sorted(rows, key=lambda item: (item.created_at or datetime.min, item.stt)):
        groups.setdefault(max(row.created or start, start), []).append(row)
    return sorted(groups.items())
