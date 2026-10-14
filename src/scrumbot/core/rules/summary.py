"""One summary per active dev for the dev table of output.md (bot spec §7.4). Pure."""

from __future__ import annotations

from scrumbot.core.model import Assignment, Dev, DevSummary


def summarize(
    devs: tuple[Dev, ...],
    carry: dict[str, int],
    leave: dict[str, int],
    assignments: tuple[Assignment, ...],
    capacity: dict[str, int] | None = None,
    open_hours: dict[str, int] | None = None,
) -> tuple[DevSummary, ...]:
    """One summary per active dev: the pool and those removed for leave."""
    return tuple(
        DevSummary(
            dev=dev,
            carry_over=carry.get(dev.code, 0),
            leave_days=leave.get(dev.code, 0),
            orders=sum(dev.code in assignment.pic_codes for assignment in assignments),
            capacity=capacity.get(dev.code) if capacity is not None else None,
            open_hours=(open_hours or {}).get(dev.code, 0),
        )
        for dev in devs
        if dev.active
    )
