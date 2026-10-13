"""Progress and quality risks (bot spec §4.2): DUE-AT-RISK, STATUS-STUCK and QA-RETURNS. Pure."""

from __future__ import annotations

from scrumbot.model import Assignment, Source, SprintRow, StatusChange
from scrumbot.model_risk import Risk, RiskGroup, RiskLevel
from scrumbot.normalize import text_key
from scrumbot.rules.leave import days_left, working_time
from scrumbot.rules.risk_register import (
    RiskContext,
    deadline,
    deadline_text,
    escalate,
    is_done,
    is_open,
    make,
    not_started,
    order_where,
    pic_codes,
)

DUE_SOON_DAYS = 3  # T3
QA_RETURNS = 2  # O12
MANY_BUGS = 5  # O12: P80 of bugs per order
_STATUSES = ("in progress", "ready to progress", "ready to qa-testing", "ready to internal testing", "ready to release")
_IN_PROGRESS, _READY, _QA, _INTERNAL, _RELEASE = (text_key(name) for name in _STATUSES)
ROOT_LIMITS = {_IN_PROGRESS: 4, _READY: 2, _QA: 2, _INTERNAL: 2, _RELEASE: 6}  # A49, working days
SUBTASK_LIMITS = {_IN_PROGRESS: 2, _READY: 3, _QA: 2, _INTERNAL: 2}  # A49
_DEV_SIDE = frozenset({_IN_PROGRESS, _READY})
_TEST_SIDE = frozenset({_QA, _INTERNAL})
_QA_NEED_FIX = text_key("qa - need fix")


def due_risks(context: RiskContext) -> tuple[Risk, ...]:
    """DUE-AT-RISK (D45 risk 7): overdue, not started near the deadline, or many open subtasks near it."""
    risks: list[Risk] = []
    for item in context.assignments:
        row = item.order.row
        codes = pic_codes(item, context.active)
        end = deadline(row, context.sheet)
        if not codes or end is None or not (is_open(row) or not_started(row)):
            continue
        left = days_left(context.base, end)
        if row.due is not None and row.due < context.base:
            level = RiskLevel.HIGH
            problem = f'Đơn STT {row.stt} quá hạn {row.due:%d/%m/%Y} (trạng thái "{row.status}")'
            impact = "Đơn đã trễ hạn."
        elif left > DUE_SOON_DAYS:
            continue
        elif not_started(row):
            level = escalate(RiskLevel.HIGH if left <= 1 else RiskLevel.MEDIUM, item.order.priority)
            tail = f'nhưng vẫn "{row.status}"' if row.status else "nhưng vẫn chưa bắt đầu"
            problem = f"Đơn STT {row.stt} còn {left} ngày làm việc tới {deadline_text(row, context.sheet)} {tail}"
            impact = "Đơn có thể trễ hạn."
        else:
            subtasks = _subtasks(context, row)
            unfinished = [sub for sub in subtasks if not is_done(sub)]
            if len(unfinished) < 2 or 2 * len(unfinished) < len(subtasks):
                continue
            level = escalate(RiskLevel.HIGH if left <= 1 else RiskLevel.MEDIUM, item.order.priority)
            problem = (
                f"Đơn STT {row.stt} còn {left} ngày làm việc tới {deadline_text(row, context.sheet)} mà còn "
                f"{len(unfinished)}/{len(subtasks)} subtask chưa xong"
            )
            impact = "Đơn có thể trễ hạn."
        pic = ", ".join(codes)
        if item.source is Source.PROPOSED:
            action, owner = f"Giao ngay cho {pic}; nếu không kịp: lùi hạn hoặc đẩy sang sprint sau.", "TM"
        else:
            suggestion = context.suggest(row.stt, frozenset(codes))
            action = (
                f"Hỏi {pic} lý do; nếu kẹt: chuyển cho {suggestion.pic_codes[0]} hoặc lùi hạn"
                if suggestion is not None
                else f"Hỏi {pic} lý do; nếu kẹt: lùi hạn hoặc đẩy sang sprint sau."
            )
            owner = pic
        risks.append(
            _order_risk(context, item, level, "DUE-AT-RISK", RiskGroup.PROGRESS, problem, impact, action, owner)
        )
    return tuple(risks)


def stuck_risks(context: RiskContext) -> tuple[Risk, ...]:
    """STATUS-STUCK (D45 risk 10, A49, A61): the order or a subtask stays in one status past its threshold."""
    changes = _changes_by_task(context)
    risks: list[Risk] = []
    for item in context.assignments:
        row = item.order.row
        if item.source is Source.PROPOSED:
            continue  # nobody has the order yet: the proposal is the action
        root_hit = _stuck(row, ROOT_LIMITS, changes, context)
        sub_hits = []
        if row.id and not is_done(row):
            for sub in _subtasks(context, row):
                if (hit := _stuck(sub, SUBTASK_LIMITS, changes, context)) is not None:
                    sub_hits.append(hit)
        if root_hit is None and not sub_hits:
            continue
        parts = []
        if root_hit is not None:
            elapsed, limit, _ = root_hit
            parts.append(f'Đơn STT {row.stt} ở "{row.status}" {_days(elapsed)} ngày làm việc (ngưỡng {limit})')
        worst = max(sub_hits, key=lambda hit: (hit[0] - hit[1], hit[0])) if sub_hits else None
        if worst is not None:
            elapsed, limit, sub = worst
            text = (
                f'{len(sub_hits)} subtask kẹt, lâu nhất "{sub.title}" ở "{sub.status}" {_days(elapsed)} ngày '
                f"(ngưỡng {limit})"
            )
            parts.append(text if root_hit is not None else f"Đơn STT {row.stt} có {text}")
        side = text_key(row.status if root_hit is not None else worst[2].status)  # type: ignore[index]
        codes = pic_codes(item, context.active)
        pic = ", ".join(codes)
        if side in _DEV_SIDE:
            action, owner = (f"Hỏi {pic} đang vướng gì.", pic) if codes else ("Hỏi người làm đang vướng gì.", "TM")
        elif side in _TEST_SIDE:
            action, owner = "Nhắc khâu test nhận đơn.", "TM"
        else:
            action, owner = "Nhắc khâu phát hành.", "TM"
        risks.append(
            _order_risk(
                context,
                item,
                escalate(RiskLevel.MEDIUM, item.order.priority),
                "STATUS-STUCK",
                RiskGroup.PROGRESS,
                "; ".join(parts),
                "Đơn chậm lại; có thể trễ hạn.",
                action,
                owner,
            )
        )
    return tuple(risks)


def qa_risks(context: RiskContext) -> tuple[Risk, ...]:
    """QA-RETURNS (D45 risk 11, O12, A61): returns to `qa - need fix`, many bugs, or open bugs near the deadline."""
    changes = _changes_by_task(context)
    risks: list[Risk] = []
    for item in context.assignments:
        row = item.order.row
        if is_done(row) or not row.id:
            continue
        returns = sum(text_key(change.new) == _QA_NEED_FIX for change in changes.get(row.id, ()))
        bugs = [bug for bug in context.sheet.bugs if bug.root_id == row.id]
        unfinished = sum(not is_done(bug) for bug in bugs)
        end = deadline(row, context.sheet)
        left = days_left(context.base, end) if end is not None else None
        parts = []
        if returns >= QA_RETURNS:
            parts.append(f'về "qa - need fix" {returns} lần')
        if len(bugs) >= MANY_BUGS:
            parts.append(f"có {len(bugs)} bug ({unfinished} chưa xong)")
        if unfinished and left is not None and left <= DUE_SOON_DAYS:
            parts.append(
                f"còn {unfinished} bug mở khi còn {left} ngày làm việc tới {deadline_text(row, context.sheet)}"
            )
        if not parts:
            continue
        codes = pic_codes(item, context.active)
        pic = ", ".join(codes)
        action = (
            f"Hỏi {pic} nguyên nhân; cân nhắc review code trước khi gửi test."
            if codes
            else "Tìm nguyên nhân trước khi gửi test lại."
        )
        risks.append(
            _order_risk(
                context,
                item,
                escalate(RiskLevel.MEDIUM, item.order.priority),
                "QA-RETURNS",
                RiskGroup.QUALITY,
                f"Đơn STT {row.stt} " + "; ".join(parts),
                "Bản build còn nhiều lỗi; vòng test có thể kéo dài.",
                action,
                pic or "TM",
            )
        )
    return tuple(risks)


def time_in_status(row: SprintRow, changes: dict[str, list[StatusChange]], context: RiskContext) -> float | None:
    """Working days since the row entered its current status (A61), or None when nothing dates it."""
    events = changes.get(row.id, []) if row.id else []
    if events:
        into = [event for event in events if text_key(event.new) == text_key(row.status)]
        since = (into or events)[-1].at
    elif row.updated is not None:
        since = row.updated
    else:
        return None
    return working_time(since, context.now)


def _stuck(
    row: SprintRow, limits: dict[str, int], changes: dict[str, list[StatusChange]], context: RiskContext
) -> tuple[float, int, SprintRow] | None:
    limit = limits.get(text_key(row.status))
    if limit is None:
        return None
    elapsed = time_in_status(row, changes, context)
    if elapsed is None:
        return None
    elapsed = round(elapsed, 1)  # compared as shown: "4,0 ngày (ngưỡng 4)" must never appear
    return (elapsed, limit, row) if elapsed > limit else None


def _subtasks(context: RiskContext, row: SprintRow) -> list[SprintRow]:
    if not row.id:
        return []
    return [sub for sub in context.sheet.rows if sub.kind == "Subtask" and sub.root_id == row.id]


def _changes_by_task(context: RiskContext) -> dict[str, list[StatusChange]]:
    grouped: dict[str, list[StatusChange]] = {}
    for change in context.sheet.changes:
        if change.at <= context.now:
            grouped.setdefault(change.task_id, []).append(change)
    return grouped


def _days(value: float) -> str:
    return f"{value:.1f}".replace(".", ",")


def _order_risk(
    context: RiskContext,
    item: Assignment,
    level: RiskLevel,
    code: str,
    group: RiskGroup,
    problem: str,
    impact: str,
    action: str,
    owner: str,
) -> Risk:
    stt = item.order.row.stt
    return make(context, level, code, group, order_where(stt), problem, impact, action, owner, stt=stt, covers=(stt,))
