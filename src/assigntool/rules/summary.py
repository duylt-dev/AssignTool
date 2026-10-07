"""Rows for the report's Tải dev sheet."""

from __future__ import annotations

from datetime import date

from assigntool.model import Assignment, Dev, DevSummary, Source
from assigntool.rules.familiarity import FamiliarityIndex
from assigntool.rules.leave import on_leave_all_sprint


def summarize(
    devs: tuple[Dev, ...],
    pool: tuple[Dev, ...],
    days: tuple[date, ...],
    carry: dict[str, int],
    leave: dict[str, int],
    assignments: tuple[Assignment, ...],
    fam: FamiliarityIndex,
) -> tuple[DevSummary, ...]:
    """Summarize active available devs and active devs removed for full leave."""
    pool_codes = {dev.code for dev in pool}
    result: list[DevSummary] = []
    for dev in devs:
        all_sprint = on_leave_all_sprint(dev, days)
        if not dev.active or (dev.code not in pool_codes and not all_sprint):
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
            )
        )
    return tuple(result)
