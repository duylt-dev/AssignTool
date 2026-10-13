"""Reading the past from today's data (bot spec §8, A70, A74): an item's status at a moment, when it was done, the
sprint as it looked at a checkpoint, carry-over at a sprint's start and the outcome of an order. Pure."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, time

from scrumbot.model import Dev, SprintRow, SprintSheet, StatusChange
from scrumbot.normalize import text_key
from scrumbot.rules.board import is_done_kind
from scrumbot.rules.carry_over import BUSY_STATUSES
from scrumbot.rules.leave import working_days

MANY_BUGS = 5  # O12, D56
CHECKPOINT_TIME = time(8, 30)  # the morning run (D54)
_IN_PROGRESS = ("in progress", "custom")

Changes = Mapping[str, list[StatusChange]]


def by_task(changes: tuple[StatusChange, ...]) -> dict[str, list[StatusChange]]:
    grouped: dict[str, list[StatusChange]] = {}
    for change in sorted(changes, key=lambda item: item.at):
        grouped.setdefault(change.task_id, []).append(change)
    return grouped


def status_at(row: SprintRow, changes: Changes, at: datetime, kinds: Mapping[str, str]) -> tuple[str, str] | None:
    """(name, kind) of the row's status at `at` from its history; None when the row has no history."""
    events = changes.get(row.id) if row.id else None
    if not events:
        return None
    before = [event for event in events if event.at <= at]
    name = before[-1].new if before else events[0].old
    return name, kinds.get(text_key(name), "")


def done_time(row: SprintRow, changes: Changes, kinds: Mapping[str, str]) -> datetime | None:
    """`ngay_dong`, else the first move into a status of kind done/closed (A74); None when unknown."""
    if row.closed is not None:
        return row.closed
    for event in changes.get(row.id, ()) if row.id else ():
        if is_done_kind(kinds.get(text_key(event.new), "")):
            return event.at
    return None


def view_at(sheet: SprintSheet, at: datetime, kinds: Mapping[str, str]) -> SprintSheet:
    """The sheet as the bot would have seen it at `at` (bot spec §8.2): items created before, statuses then."""
    changes = by_task(sheet.changes)

    def seen(row: SprintRow) -> bool:
        return row.created_at is None or row.created_at <= at

    def then(row: SprintRow) -> SprintRow:
        status = status_at(row, changes, at, kinds)
        closed = row.closed if row.closed is not None and row.closed <= at else None
        if status is not None:
            name, kind = status
        elif row.closed is not None and row.closed <= at or not is_done_kind(row.status_kind):
            name, kind = row.status, row.status_kind
        else:
            name, kind = _IN_PROGRESS  # done now, done when unknown: assumed at work during the sprint (A74)
        return replace(row, status=name, status_kind=kind, closed=closed)

    return replace(
        sheet,
        rows=tuple(then(row) for row in sheet.rows if seen(row)),
        bugs=tuple(then(row) for row in sheet.bugs if seen(row)),
        changes=tuple(change for change in sheet.changes if change.at <= at),
    )


def carry_at(
    prev: SprintSheet | None, at: datetime, devs: tuple[Dev, ...], carried: set[str], kinds: Mapping[str, str]
) -> dict[str, int]:
    """Carry-over at a moment (A70): previous-sprint rows naming the dev that were busy then."""
    counts = {dev.code: 0 for dev in devs}
    if prev is None:
        return counts
    changes = by_task(prev.changes)
    for row in prev.rows:
        if row.created_at is not None and row.created_at > at:
            continue
        status = status_at(row, changes, at, kinds)
        if status is not None:
            busy = text_key(status[0]) in BUSY_STATUSES
        elif row.closed is not None:
            busy = row.closed > at
        else:
            busy = not is_done_kind(row.status_kind) or row.root_id in carried
        if not busy:
            continue
        names = {text_key(name) for name in row.assignees}
        for dev in devs:
            if text_key(dev.name) in names:
                counts[dev.code] += 1
    return counts


def outcome(
    row: SprintRow, sheet: SprintSheet, later: set[str], changes: Changes, kinds: Mapping[str, str]
) -> tuple[str, ...]:
    """Why an order's outcome is bad (D56, A74); empty when it is good."""
    reasons = []
    finished = done_time(row, changes, kinds)
    end = datetime.combine(sheet.end, time.max) if sheet.end is not None else None
    if finished is not None and end is not None and finished > end:
        reasons.append("xong sau ngày kết thúc")
    if row.id in later:
        reasons.append("có mặt ở sprint sau")
    if finished is None and not is_done_kind(row.status_kind):
        reasons.append("chưa xong")
    if finished is not None and row.due is not None and finished.date() > row.due:
        reasons.append("xong sau hạn")
    bugs = sum(bug.root_id == row.id for bug in sheet.bugs)
    if bugs >= MANY_BUGS:
        reasons.append(f"{bugs} bug")
    return tuple(reasons)


def checkpoints(sheet: SprintSheet) -> tuple[datetime, ...]:
    """08:30 of the first working day, of the 5th, and of the day from which 3 working days remain (D56)."""
    days = working_days(sheet.start, sheet.end)
    if not days:
        return ()
    picks = {days[0]}
    if len(days) >= 5:
        picks.add(days[4])
    if len(days) >= 3:
        picks.add(days[-3])
    return tuple(datetime.combine(day, CHECKPOINT_TIME) for day in sorted(picks))
