"""Capacity risks (bot spec §4.2): CAPACITY-DEV, CAPACITY-SPRINT, SCOPE-ADDED and CARRY-OVER. Pure."""

from __future__ import annotations

from scrumbot.core.model import Assignment
from scrumbot.core.model_risk import Risk, RiskGroup, RiskLevel
from scrumbot.core.rules.risk_register import (
    RiskContext,
    defer_list,
    is_open,
    make,
    not_started,
    pic_codes,
    reverse_key,
    stt_list,
)

HOURS_PER_DAY = 6  # R6 (D48)
HIGH_FACTOR = 1.5  # R6: Cao above 1.5 × capacity
CARRY_MEDIUM = 3  # A73: CARRY-OVER is Trung bình from 3 rows


def capacities(context: RiskContext) -> dict[str, int] | None:
    """Hours left per pool dev: 6 × (remaining days − leave among them); None without sprint dates."""
    if context.view.start is None or context.view.end is None:
        return None
    days = len(context.rest)
    return {dev.code: HOURS_PER_DAY * max(0, days - context.leave_rest.get(dev.code, 0)) for dev in context.pool}


def open_assignments(context: RiskContext) -> list[Assignment]:
    """Open orders that have a PIC, each once."""
    return [item for item in context.assignments if is_open(item.order.row) and pic_codes(item, context.active)]


def remaining_hours(item: Assignment, context: RiskContext) -> int:
    """Hours left on an open order (A73): its size times the share of its subtasks still with the dev (busy status
    or none). An order without subtasks counts whole: nothing says how far it is."""
    row = item.order.row
    subtasks = [sub for sub in context.view.rows if row.id and sub.kind == "Subtask" and sub.root_id == row.id]
    if not subtasks:
        return item.size.size.value
    left = sum(is_open(sub) for sub in subtasks)
    return (2 * item.size.size.value * left + len(subtasks)) // (2 * len(subtasks))


def dev_loads(context: RiskContext) -> dict[str, int]:
    held = open_assignments(context)
    return {
        dev.code: sum(remaining_hours(item, context) for item in held if dev.code in pic_codes(item, context.active))
        for dev in context.pool
    }


def capacity_risks(context: RiskContext) -> tuple[Risk, ...]:
    caps = capacities(context)
    if caps is None:
        return ()
    held = open_assignments(context)
    loads = dev_loads(context)
    risks: list[Risk] = []
    for dev in context.pool:
        load, cap = loads[dev.code], caps[dev.code]
        if load <= cap:
            continue
        mine = [item for item in held if dev.code in pic_codes(item, context.active)]
        days = max(0, len(context.rest) - context.leave_rest.get(dev.code, 0))
        free_hours = [(caps[code] - loads[code], code) for code in caps if code != dev.code]
        receivers = sorted(free_hours, key=lambda pair: (-pair[0], pair[1]))
        candidate = min(mine, key=lambda item: (not not_started(item.order.row), reverse_key(item.order)))
        if receivers and receivers[0][0] > 0:
            free, code = receivers[0]
            action = f"Cân nhắc chuyển STT {candidate.order.row.stt} cho {code} (còn trống {free}h)"
        else:
            action = "Không dev nào còn trống; xem rủi ro của sprint."
        risks.append(
            make(
                context,
                RiskLevel.HIGH if load > HIGH_FACTOR * cap else RiskLevel.MEDIUM,
                "CAPACITY-DEV",
                RiskGroup.CAPACITY,
                dev.code,
                f"{dev.code} còn {load}h việc ({len(mine)} đơn), sức chứa còn {cap}h ({days} ngày × {HOURS_PER_DAY}h)",
                f"Có thể không xong hết đơn trước {context.view.end:%d/%m/%Y}.",
                action,
                "TM",
            )
        )
    risks.extend(_sprint_risk(context, held, sum(caps.values())))
    return tuple(risks)


def carry_risks(context: RiskContext) -> tuple[Risk, ...]:
    """CARRY-OVER: a pool dev with carry-over who also holds open orders now (A73)."""
    held = open_assignments(context)
    risks: list[Risk] = []
    for dev in context.pool:
        count = context.carry.get(dev.code, 0)
        mine = tuple(item.order.row.stt for item in held if dev.code in pic_codes(item, context.active))
        if count < 1 or not mine:
            continue
        risks.append(
            make(
                context,
                RiskLevel.MEDIUM if count >= CARRY_MEDIUM else RiskLevel.LOW,
                "CARRY-OVER",
                RiskGroup.CAPACITY,
                dev.code,
                f"{dev.code} còn {count} việc dở ở {context.prev_name}",
                f"Sức chứa thật của {dev.code} ở sprint này thấp hơn tính toán.",
                f"Hỏi {dev.code} khi nào xong việc dở; tính tới khi giao thêm đơn.",
                "TM",
            )
        )
    return tuple(risks)


def _sprint_risk(context: RiskContext, held: list[Assignment], capacity: int) -> tuple[Risk, ...]:
    hours = {item.order.row.stt: remaining_hours(item, context) for item in held}
    total = sum(hours.values())
    if total <= capacity:
        return ()
    start = context.view.start
    late = [item for item in held if start is not None and item.order.row.created and item.order.row.created > start]
    late_hours = sum(hours[item.order.row.stt] for item in late)
    sprint = context.view.name
    impact = f"Khoảng {total - capacity}h việc có thể trễ sang sprint sau."
    if late and total - late_hours <= capacity:
        deferred = defer_list(late, total - capacity)
        action = (
            f"Đề xuất đẩy sang sprint sau: STT {stt_list(deferred)} ({_hours(deferred)}h)"
            if deferred
            else "Các đơn lên giữa sprint đã bắt đầu; cân nhắc thêm người ngoài team."
        )
        problem = (
            f"{len(late)} đơn lên sau ngày đầu sprint (STT {stt_list(late)}: {late_hours}h) làm tải vượt sức chứa "
            f"({total}h > {capacity}h)"
        )
        return (_sprint(context, "SCOPE-ADDED", sprint, problem, impact, action),)
    deferred = defer_list(held, total - capacity)
    action = (
        f"Đề xuất đẩy sang sprint sau: STT {stt_list(deferred)} ({_hours(deferred)}h), hoặc thêm người ngoài team"
        if deferred
        else "Không còn đơn chưa bắt đầu để đẩy; cân nhắc thêm người ngoài team."
    )
    problem = f"Sprint còn {total}h việc, sức chứa của team còn {capacity}h"
    return (_sprint(context, "CAPACITY-SPRINT", sprint, problem, impact, action),)


def _sprint(context: RiskContext, code: str, where: str, problem: str, impact: str, action: str) -> Risk:
    return make(context, RiskLevel.HIGH, code, RiskGroup.CAPACITY, where, problem, impact, action, "TM")


def _hours(items: tuple[Assignment, ...]) -> int:
    return sum(item.size.size.value for item in items)
