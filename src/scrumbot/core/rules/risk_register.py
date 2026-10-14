"""The risk register (bot spec §4): shared terms, levels, ordering, and the call of every producer. Pure."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime

from scrumbot.core.model import Assignment, Dev, Order, Priority, Source, SprintRow, SprintView
from scrumbot.core.model_risk import Risk, RiskLevel
from scrumbot.core.normalize import text_key
from scrumbot.core.rules.board import is_done_kind
from scrumbot.core.rules.carry_over import BUSY_STATUSES
from scrumbot.core.rules.familiarity import FamiliarityIndex
from scrumbot.core.rules.leave import add_working_days

NOT_STARTED = frozenset({text_key("ready to progress"), text_key("pending"), text_key("all issue"), ""})
DONE_NAMES = frozenset({text_key(name) for name in ("done", "ready to release", "close", "complete", "đã ro")})
URGENT = (Priority.URGENT, Priority.HIGH)

Suggest = Callable[[int, frozenset[str]], Assignment | None]  # (STT, codes left out) -> the §7 choice


@dataclass(frozen=True)
class RiskContext:
    """Everything a producer may look at. `assignments` hold every order of the sprint with its PIC."""

    view: SprintView
    assignments: tuple[Assignment, ...]
    pool: tuple[Dev, ...]  # devs who can take work in the remaining days
    active: tuple[Dev, ...]  # devs with "Nhận việc" = Y, the pool and those on leave
    fam: FamiliarityIndex
    carry: Mapping[str, int]
    prev_name: str
    leave_rest: Mapping[str, int]  # leave days among the remaining days, per dev code
    base: date
    rest: tuple[date, ...]  # remaining working days
    now: datetime
    suggest: Suggest


def register(context: RiskContext) -> tuple[Risk, ...]:
    """Every risk of bot spec §4.2, in the register's order."""
    from scrumbot.core.rules.capacity import capacity_risks, carry_risks
    from scrumbot.core.rules.pic_risks import absent_risks, unfamiliar_risks
    from scrumbot.core.rules.progress import due_risks, qa_risks, stuck_risks

    risks = [
        *capacity_risks(context),
        *carry_risks(context),
        *unfamiliar_risks(context),
        *absent_risks(context),
        *due_risks(context),
        *stuck_risks(context),
        *qa_risks(context),
    ]
    return ordered(risks)


def ordered(risks: list[Risk] | tuple[Risk, ...]) -> tuple[Risk, ...]:
    return tuple(sorted(risks, key=lambda risk: (risk.level, risk.code, _where_key(risk.where))))


def escalate(level: RiskLevel, priority: Priority) -> RiskLevel:
    """One step up for an urgent or high order (T4), never above HIGH."""
    return RiskLevel(max(level - 1, RiskLevel.HIGH)) if priority in URGENT else level


def due_for(level: RiskLevel, base: date) -> date:
    """`Hạn xử lý`: the base day for Cao, one working day later for Trung bình, two for Thấp."""
    return add_working_days(base, int(level))


def make(
    context: RiskContext,
    level: RiskLevel,
    code: str,
    group: object,
    where: str,
    problem: str,
    impact: str,
    action: str,
    owner: str,
    *,
    stt: int | None = None,
) -> Risk:
    return Risk(level, code, group, where, problem, impact, action, owner, due_for(level, context.base), stt)  # type: ignore[arg-type]


def is_open(row: SprintRow) -> bool:
    """Work is left for the dev: a busy status (D8) or none."""
    return text_key(row.status) in BUSY_STATUSES or not row.status


def not_started(row: SprintRow) -> bool:
    return text_key(row.status) in NOT_STARTED


def is_done(row: SprintRow) -> bool:
    if row.status_kind:
        return is_done_kind(row.status_kind)
    return text_key(row.status) in DONE_NAMES


def pic_codes(assignment: Assignment, active: tuple[Dev, ...]) -> tuple[str, ...]:
    """The PIC as dev codes: the bot's choice, or the active devs named on a pre-assigned order."""
    if assignment.source is Source.PROPOSED:
        return assignment.pic_codes
    names = {text_key(name) for name in assignment.order.row.assignees}
    return tuple(dev.code for dev in active if text_key(dev.name) in names)


def deadline(row: SprintRow, view: SprintView) -> date | None:
    return row.due or view.end


def deadline_text(row: SprintRow, view: SprintView) -> str:
    if row.due is not None:
        return f"hạn {row.due:%d/%m/%Y}"
    return f"cuối sprint ({view.end:%d/%m/%Y})" if view.end else "cuối sprint"


def reverse_key(order: Order) -> tuple[object, ...]:
    """The opposite of A5: lowest priority, latest or no due date, newest, highest STT first."""
    row = order.row
    return (
        -order.priority,
        row.due is not None,
        -(row.due.toordinal() if row.due else 0),
        -(row.created.toordinal() if row.created else 0),
        -row.stt,
    )


def defer_list(assignments: list[Assignment], excess: int) -> tuple[Assignment, ...]:
    """Not-started orders in reverse order, taken until their hours cover `excess` (bot spec §4.1)."""
    chosen: list[Assignment] = []
    hours = 0
    for item in sorted((a for a in assignments if not_started(a.order.row)), key=lambda a: reverse_key(a.order)):
        if hours >= excess:
            break
        chosen.append(item)
        hours += item.size.size.value
    return tuple(chosen)


def stt_list(items: tuple[Assignment, ...] | list[Assignment]) -> str:
    return ", ".join(str(item.order.row.stt) for item in items)


def order_where(stt: int) -> str:
    return f"Đơn STT {stt}"


def _where_key(where: str) -> tuple[int, str]:
    """`Đơn STT 10` after `Đơn STT 9`."""
    prefix = "Đơn STT "
    if where.startswith(prefix) and where[len(prefix) :].isdigit():
        return int(where[len(prefix) :]), ""
    return 1_000_000, where
