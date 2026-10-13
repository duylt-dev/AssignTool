"""The risk half of the replay (bot spec §8.2, D56): the register at three checkpoints of every past sprint, the
real outcome of each order, and the scores per code. Pure."""

from __future__ import annotations

from datetime import date, datetime
from statistics import median

from scrumbot.model import Assignment, Dev, HistoryOrder, Source, SprintSheet, TeamRule
from scrumbot.model_board import Board, SprintInfo
from scrumbot.model_risk import Checkpoint, CodeScore, OrderOutcome, Risk, RiskLevel, RiskSprint
from scrumbot.rules.board import history_orders, label_of, maintain_sprints, previous_of, sprint_sheet
from scrumbot.rules.familiarity import FamiliarityIndex
from scrumbot.rules.history_window import history_for
from scrumbot.rules.leave import leave_count, on_leave_all_sprint, working_days
from scrumbot.rules.pic_risks import suggester
from scrumbot.rules.replay import PREV_FALLBACK, Sizes, codes_of, joined, order_of, pool_members, sizes_of
from scrumbot.rules.risk_register import RiskContext, register
from scrumbot.rules.team_rules import in_force
from scrumbot.rules.timeline import by_task, carry_at, checkpoints, outcome, view_at
from scrumbot.rules.validate import orders_and_findings

ALL_CODES = "Mọi loại"


def replay_risks(
    board: Board,
    devs: tuple[Dev, ...],
    rules: tuple[TeamRule, ...],
    sizes: Sizes,
    only: SprintInfo | None = None,
    ended_before: date | None = None,
) -> tuple[RiskSprint, ...]:
    """Bot spec §8.2: the register at each checkpoint, and the outcome of every root order with a pool dev. A sprint
    still running at `ended_before` has no outcome yet and is left out."""
    sprints = maintain_sprints(board.sprints)
    history = history_orders(board)
    first = joined(board, devs)
    kinds = board.status_kinds
    results = []
    for index, sprint in enumerate(sprints):
        if only is not None and sprint.id != only.id:
            continue
        if ended_before is not None and sprint.end is not None and sprint.end >= ended_before:
            continue
        sheet = sprint_sheet(board, sprint)
        later = {
            task.id
            for other in sprints[index + 1 :]
            for task in board.lists.get(other.id, ())
            if not task.parent_id and not task.is_bug
        }
        members = pool_members(devs, first, sprint)
        roots = [row for row in sheet.rows if row.kind == "Task"]
        universe = [row for row in roots if codes_of(row.assignees, members)]
        previous = previous_of(board.sprints, sprint)
        prev_sheet = sprint_sheet(board, previous) if previous else None
        points = tuple(
            Checkpoint(at, _register_at(board, sheet, prev_sheet, previous, members, history, rules, sizes, at))
            for at in checkpoints(sheet)
        )
        changes = by_task(sheet.changes)
        outcomes = tuple(
            OrderOutcome(
                order_of(row, row.assignees),
                codes_of(row.assignees, members),
                outcome(row, sheet, later, changes, kinds),
                _flagged(row.stt, points),
            )
            for row in universe
        )
        has_history = any(row.id in changes for row in roots)
        results.append(RiskSprint(label_of(sprint), has_history, points, outcomes))
    return tuple(results)


def scores(sprints: tuple[RiskSprint, ...]) -> tuple[CodeScore, ...]:
    """One row per code that covered an order, then "Mọi loại" (bot spec §8.2)."""
    codes = sorted({code for sprint in sprints for item in sprint.outcomes for code, _ in item.flagged})
    rows = [_score(code, sprints, {code}) for code in codes]
    rows.append(_score(ALL_CODES, sprints, set(codes)))
    return tuple(rows)


def lead_days(day: date, end: date) -> int:
    """Working days from a checkpoint day to the sprint's end, both included."""
    return len(working_days(day, end))


def _score(name: str, sprints: tuple[RiskSprint, ...], codes: set[str]) -> CodeScore:
    flagged = flagged_bad = bad = bad_flagged = 0
    leads: list[int] = []
    for sprint in sprints:
        for item in sprint.outcomes:
            days = [day for code, day in item.flagged if code in codes]
            if item.bad:
                bad += 1
            if not days:
                continue
            flagged += 1
            if item.bad:
                flagged_bad += 1
                bad_flagged += 1
                leads.append(lead_days(min(days), sprint.label.end))
    return CodeScore(name, flagged, flagged_bad, bad, bad_flagged, float(median(leads)) if leads else None)


def _register_at(
    board: Board,
    sheet: SprintSheet,
    prev_sheet: SprintSheet | None,
    previous: SprintInfo | None,
    members: tuple[Dev, ...],
    history: tuple[HistoryOrder, ...],
    rules: tuple[TeamRule, ...],
    sizes: Sizes,
    at: datetime,
) -> tuple[Risk, ...]:
    """The register at one checkpoint with the TM's real `Người làm` (no proposals) and no stored state."""
    kinds = board.status_kinds
    view = view_at(sheet, at, kinds)
    orders, _ = orders_and_findings(view)
    order_sizes = sizes_of(orders, sizes)
    rest = working_days(at.date(), sheet.end)
    days = working_days(sheet.start, sheet.end)
    pool = tuple(dev for dev in members if not on_leave_all_sprint(dev, days) and not on_leave_all_sprint(dev, rest))
    if not pool:
        return ()
    label = label_of(next(s for s in board.sprints if s.id == sheet.id))
    fam = FamiliarityIndex.build(history_for(history, label.number, sheet.start, sheet.end, at.date()), pool)
    carry = carry_at(
        view_at(prev_sheet, at, kinds) if prev_sheet else None,
        at,
        members,
        {row.id for row in view.rows if row.kind == "Task"},
        kinds,
    )
    leave = {dev.code: leave_count(dev, rest) for dev in members}
    assignments = tuple(
        Assignment(
            order,
            order_sizes[order.row.stt],
            Source.PREASSIGNED,
            order.row.assignees,
            codes_of(order.row.assignees, pool),
            "",
            (),
        )
        for order in orders
        if order.row.assignees
    )
    prev_name = previous.name if previous else PREV_FALLBACK
    rules_now = in_force(rules, at.date())
    context = RiskContext(
        sheet=view,
        assignments=assignments,
        pool=pool,
        active=members,
        fam=fam,
        carry=carry,
        prev_name=prev_name,
        leave_rest=leave,
        base=at.date(),
        rest=rest,
        now=at,
        suggest=suggester(orders, assignments, order_sizes, pool, fam, carry, leave, prev_name, rules_now),
        status_kinds=kinds,
    )
    return register(context)


def _flagged(stt: int, points: tuple[Checkpoint, ...]) -> tuple[tuple[str, date], ...]:
    """(code, first checkpoint day) of the Cao or Trung bình risks that covered the order."""
    first: dict[str, date] = {}
    for point in points:
        for risk in point.risks:
            if risk.level <= RiskLevel.MEDIUM and stt in risk.covers:
                first.setdefault(risk.code, point.at.date())
    return tuple(sorted(first.items()))
