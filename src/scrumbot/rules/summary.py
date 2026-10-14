"""One line per dev for the dev table of output.md (bot spec §7.4)."""

from __future__ import annotations

from datetime import date

from scrumbot.model import Assignment, Dev, DevSummary, Source
from scrumbot.rules.familiarity import FamiliarityIndex
from scrumbot.rules.leave import on_leave_all_sprint


def summarize(
    devs: tuple[Dev, ...],
    pool: tuple[Dev, ...],
    days: tuple[date, ...],
    carry: dict[str, int],
    leave: dict[str, int],
    assignments: tuple[Assignment, ...],
    fam: FamiliarityIndex,
    capacity: dict[str, int] | None = None,
    open_hours: dict[str, int] | None = None,
) -> tuple[DevSummary, ...]:
    """One row per active dev: the pool and those removed for leave (bot spec §6 adds capacity and open hours)."""
    result: list[DevSummary] = []
    for dev in devs:
        all_sprint = on_leave_all_sprint(dev, days)
        if not dev.active:
            continue
        held = tuple(assignment for assignment in assignments if dev.code in assignment.pic_codes)
        result.append(
            DevSummary(
                dev=dev,
                carry_over=carry.get(dev.code, 0),
                leave_days=leave.get(dev.code, 0),
                on_leave_all_sprint=all_sprint,
                preassigned=sum(assignment.source is Source.PREASSIGNED for assignment in held),
                proposed=sum(assignment.source is Source.PROPOSED for assignment in held),
                hours=sum(assignment.size.size.value for assignment in held),
                orders=tuple(f"{assignment.order.row.title} [{assignment.size.size.name}]" for assignment in held),
                known_apps=fam.known_apps(dev),
                capacity=capacity.get(dev.code) if capacity is not None else None,
                open_hours=(open_hours or {}).get(dev.code, 0),
            )
        )
    return tuple(result)
