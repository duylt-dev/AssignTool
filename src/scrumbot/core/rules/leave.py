"""Working-day and leave helpers (assignment spec §6.3, bot spec §3). Working days are Monday to Friday (T5)."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from scrumbot.core.model import Dev, Finding, Order, Severity
from scrumbot.core.normalize import text_key


def working_days(start: date | None, end: date | None) -> tuple[date, ...]:
    """Return Monday-to-Friday dates in the inclusive sprint range."""
    if start is None or end is None:
        return ()
    days: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return tuple(days)


def add_working_days(day: date, n: int) -> date:
    """The n-th working day after `day` (n = 0 gives `day`)."""
    current, added = day, 0
    while added < n:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


def days_left(base: date, deadline: date) -> int:
    """Working days from `base` to `deadline`, both included; 0 when the deadline is past."""
    return len(working_days(base, deadline))


def working_time(start: datetime, end: datetime) -> float:
    """Days from `start` to `end` counting Monday to Friday only, with fractions (A61)."""
    total = 0.0
    current = start
    while current < end:
        segment_end = min(datetime.combine(current.date() + timedelta(days=1), time()), end)
        if current.weekday() < 5:
            total += (segment_end - current).total_seconds()
        current = segment_end
    return total / 86400


def leave_count(dev: Dev, days: tuple[date, ...]) -> int:
    return sum(day in dev.leave_days for day in days)


def on_leave_all_sprint(dev: Dev, days: tuple[date, ...]) -> bool:
    return bool(days) and all(day in dev.leave_days for day in days)


def pre_assigned_on_leave(
    orders: tuple[Order, ...], removed: tuple[Dev, ...], pool: tuple[Dev, ...]
) -> tuple[Finding, ...]:
    """PRE-ASSIGNED-ON-LEAVE (A43): a kept order (D10) whose only pool-side holder is off for the whole sprint."""
    off = {text_key(dev.name): dev.code for dev in removed}
    working = {text_key(dev.name) for dev in pool}
    findings: list[Finding] = []
    for order in orders:
        people = {text_key(name) for name in order.row.assignees}
        codes = sorted(off[name] for name in people if name in off)
        if codes and not people & working:
            stt, who = order.row.stt, ", ".join(codes)
            findings.append(
                Finding(
                    Severity.WARN,
                    "PRE-ASSIGNED-ON-LEAVE",
                    f"Đơn STT {stt}",
                    f"Đơn STT {stt} giao sẵn cho {who} nhưng {who} nghỉ cả sprint; "
                    "đơn chưa có ai làm, cân nhắc giao lại.",
                )
            )
    return tuple(findings)
