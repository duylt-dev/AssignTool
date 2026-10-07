"""Deterministic PIC selection (assignment spec section 7)."""

from __future__ import annotations

from assigntool.model import Assignment, Dev, Level, Order, Priority, SizeEstimate, Source
from assigntool.normalize import text_key
from assigntool.rules.familiarity import FamiliarityIndex
from assigntool.rules.reasons import PREASSIGNED_REASON, proposed_reason

GAP_ORDERS = 1  # D26: a dev may hold at most one order more than the least-loaded dev


def assign(
    orders: tuple[Order, ...],
    sizes: dict[int, SizeEstimate],
    pool: tuple[Dev, ...],
    fam: FamiliarityIndex,
    carry: dict[str, int],
    leave: dict[str, int],
    prev_name: str,
) -> tuple[Assignment, ...]:
    """Keep pre-assignments, then choose PICs lexicographically for the rest."""
    loads = {dev.code: 0 for dev in pool}
    counts = {dev.code: 0 for dev in pool}
    assignments: dict[int, Assignment] = {}

    for order in orders:
        if not order.row.assignees:
            continue
        assignee_keys = {text_key(name) for name in order.row.assignees}
        pic_codes = tuple(dev.code for dev in pool if text_key(dev.name) in assignee_keys)
        for code in pic_codes:
            loads[code] += sizes[order.row.stt].size.value
            counts[code] += 1
        assignments[order.row.stt] = Assignment(
            order, sizes[order.row.stt], Source.PREASSIGNED, order.row.assignees, pic_codes, PREASSIGNED_REASON, ()
        )

    pending = sorted((order for order in orders if not order.row.assignees), key=_processing_key)
    for order in pending:
        needs_senior = order.priority in (Priority.URGENT, Priority.HIGH) or fam.is_new_app(order.row.app)
        cap_limit = min(counts.values()) + GAP_ORDERS
        capped = tuple(dev for dev in pool if counts[dev.code] <= cap_limit)

        def key(
            dev: Dev,
            app: str = order.row.app,
            requires_senior: bool = needs_senior,
        ) -> tuple[int, int, int, int, int, int, str]:
            return (
                fam.get(dev, app).rank,
                0 if not requires_senior or dev.level >= Level.MIDDLE else 1,
                loads[dev.code],
                carry[dev.code],
                leave[dev.code],
                -dev.level,
                dev.code,
            )

        pic = min(capped, key=key)
        pic_familiarity = fam.get(pic, order.row.app)
        backups = tuple(dev.code for dev in sorted((dev for dev in pool if dev != pic), key=key)[:2])
        pic_rank, pic_gap = key(pic)[:2]
        outside_cap = sorted((dev for dev in pool if dev not in capped), key=key)
        excluded = tuple((dev.code, counts[dev.code]) for dev in outside_cap if key(dev)[0] < pic_rank)
        excluded_senior = tuple(
            (dev.code, counts[dev.code]) for dev in outside_cap if key(dev)[0] == pic_rank and key(dev)[1] < pic_gap
        )
        senior_cause = (
            "priority"
            if order.priority in (Priority.URGENT, Priority.HIGH)
            else "new_app"
            if fam.is_new_app(order.row.app)
            else None
        )
        assignments[order.row.stt] = Assignment(
            order,
            sizes[order.row.stt],
            Source.PROPOSED,
            (pic.name,),
            (pic.code,),
            proposed_reason(
                app=order.row.app,
                familiarity=pic_familiarity,
                level=pic.level,
                senior_cause=senior_cause,
                priority=order.priority,
                load_hours=loads[pic.code],
                load_orders=counts[pic.code],
                carry_over=carry[pic.code],
                prev_name=prev_name,
                leave_days=leave[pic.code],
                cap_excluded=excluded,
                cap_excluded_senior=excluded_senior,
            ),
            backups,
        )
        loads[pic.code] += sizes[order.row.stt].size.value
        counts[pic.code] += 1
    return tuple(assignments[stt] for stt in sorted(assignments))


def _processing_key(order: Order) -> tuple[Priority, bool, object, bool, object, int]:
    row = order.row
    return order.priority, row.due is None, row.due, row.created is None, row.created, row.stt
