"""Working-day and leave helpers."""

from __future__ import annotations

from datetime import date, timedelta

from assigntool.model import Dev


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


def leave_count(dev: Dev, days: tuple[date, ...]) -> int:
    return sum(day in dev.leave_days for day in days)


def on_leave_all_sprint(dev: Dev, days: tuple[date, ...]) -> bool:
    return bool(days) and all(day in dev.leave_days for day in days)
