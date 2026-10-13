"""Which history orders a run may use (A22): none from the sprint being assigned, none from after the run day."""

from __future__ import annotations

from datetime import date

from scrumbot.model import HistoryOrder


def in_sprint(order: HistoryOrder, number: int, start: date | None, end: date | None) -> bool:
    """True when one of the order's sprint labels is this sprint. Unknown dates match any date."""
    return any(
        label.number == number and (start is None or label.start == start) and (end is None or label.end == end)
        for label in order.sprints
    )


def history_for(
    history: tuple[HistoryOrder, ...], number: int, start: date | None, end: date | None, day: date
) -> tuple[HistoryOrder, ...]:
    """History for assigning sprint `number` on `day`: not that sprint's own orders, nothing filed after `day`, and
    nothing whose first sprint starts after `day`, so a run with --today never sees an assignment made later."""
    return tuple(
        order
        for order in history
        if not in_sprint(order, number, start, end)
        and order.created <= day
        and min((label.start for label in order.sprints), default=order.created) <= day
    )
