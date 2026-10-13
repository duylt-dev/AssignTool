"""What changed since the stored state (bot spec §5): ORDER-CHANGED, the "Thay đổi" rows, the state to store, and
the report fingerprint of A78. Pure."""

from __future__ import annotations

import hashlib
import json
from datetime import date

from scrumbot.model import Assignment, Dev, Result
from scrumbot.model_risk import Change, ChangeKind, OrderMark, Outcome, Risk, RiskGroup, RiskLevel
from scrumbot.normalize import clean, text_key
from scrumbot.rules.risk_register import RiskContext, escalate, make, order_where, pic_codes

_KIND_ORDER = list(ChangeKind)


def marks(assignments: tuple[Assignment, ...], active: tuple[Dev, ...]) -> tuple[OrderMark, ...]:
    """The state to store for each order with an id: title, priority, due date and the pool codes in `Người làm`."""
    rows = [item.order.row for item in assignments]
    return tuple(
        OrderMark(row.id, row.title, row.priority_raw, row.due, _codes(item, active))
        for row, item in zip(rows, assignments, strict=True)
        if row.id
    )


def changed_risks(context: RiskContext) -> tuple[Risk, ...]:
    """ORDER-CHANGED (D45 risk 9, A62): priority, due date or title differs from the stored state."""
    if context.baseline is None:
        return ()
    stored = {mark.id: mark for mark in context.baseline}
    risks: list[Risk] = []
    for item in context.assignments:
        row = item.order.row
        mark = stored.get(row.id) if row.id else None
        if mark is None:
            continue
        diffs = _diffs(mark, item)
        if not diffs:
            continue
        codes = pic_codes(item, context.active)
        action = f"Báo {', '.join(codes)}; xem lại độ lớn và hạn." if codes else "Xem lại độ lớn và hạn."
        risks.append(
            make(
                context,
                escalate(RiskLevel.LOW, item.order.priority),
                "ORDER-CHANGED",
                RiskGroup.CHANGE,
                order_where(row.stt),
                f"Đơn STT {row.stt} đổi " + "; ".join(text for _, text in diffs),
                "Độ lớn, PIC hoặc kế hoạch có thể cần xem lại.",
                action,
                "TM",
                stt=row.stt,
                covers=(row.stt,),
            )
        )
    return tuple(risks)


def change_rows(
    assignments: tuple[Assignment, ...],
    baseline: tuple[OrderMark, ...],
    outcomes: tuple[Outcome, ...],
    active: tuple[Dev, ...],
) -> tuple[Change, ...]:
    """The rows of the "Thay đổi" sheet (bot spec §5.3), codes only (D14)."""
    stored = {mark.id: mark for mark in baseline}
    current = {item.order.row.id: item for item in assignments if item.order.row.id}
    assigned = {outcome.order_id for outcome in outcomes}
    rows: list[tuple[int, Change]] = []
    for order_id, item in current.items():
        row = item.order.row
        label = f"STT {row.stt} · {row.title}"
        mark = stored.get(order_id)
        if mark is None:
            rows.append((row.stt, Change(ChangeKind.NEW, label, "—", f"{row.title} [{item.size.size.name}]")))
            continue
        for kind, _text in _diffs(mark, item):
            before, after = _values(kind, mark, item)
            rows.append((row.stt, Change(kind, label, before, after)))
        codes = _codes(item, active)
        if order_id not in assigned and set(codes) != set(mark.codes) and (codes or mark.codes):
            before, after = ", ".join(mark.codes) or "trống", ", ".join(codes) or "trống"
            rows.append((row.stt, Change(ChangeKind.PEOPLE, label, before, after)))
    for order_id, mark in stored.items():
        if order_id not in current:
            rows.append((1_000_000, Change(ChangeKind.REMOVED, mark.title, mark.title, "—")))
    for outcome in outcomes:
        item = current.get(outcome.order_id)
        label = f"STT {item.order.row.stt} · {item.order.row.title}" if item is not None else outcome.title
        verdict = "khớp" if outcome.matched else "khác đề xuất"
        actual = ", ".join(outcome.actual) or "người ngoài team"
        rows.append(
            (
                item.order.row.stt if item is not None else 1_000_000,
                Change(ChangeKind.TM_ASSIGNED, label, outcome.proposed, f"{actual} ({verdict})"),
            )
        )
    rows.sort(key=lambda pair: (_KIND_ORDER.index(pair[1].kind), pair[0], pair[1].order))
    return tuple(change for _, change in rows)


def fingerprint(result: Result) -> str:
    """What makes a report new (A78): who holds which order, the register's (code, where, level), the changes."""
    payload = {
        "assignments": sorted(
            [item.order.row.id or str(item.order.row.stt), sorted(item.pic_codes), item.source.name]
            for item in result.assignments
        ),
        "risks": sorted([risk.code, risk.where, int(risk.level)] for risk in result.risks),
        "changes": sorted([change.kind.name, change.order, change.before, change.after] for change in result.changes),
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _codes(item: Assignment, active: tuple[Dev, ...]) -> tuple[str, ...]:
    names = {text_key(name) for name in item.order.row.assignees}
    return tuple(dev.code for dev in active if text_key(dev.name) in names)


def _diffs(mark: OrderMark, item: Assignment) -> list[tuple[ChangeKind, str]]:
    row = item.order.row
    diffs = []
    if text_key(mark.priority_raw) != text_key(row.priority_raw):
        diffs.append((ChangeKind.PRIORITY, f"ưu tiên {mark.priority_raw or 'trống'} → {row.priority_raw or 'trống'}"))
    if mark.due != row.due:
        diffs.append((ChangeKind.DUE, f"hạn {_day(mark.due)} → {_day(row.due)}"))
    if clean(mark.title) != clean(row.title):
        diffs.append((ChangeKind.TITLE, f'tên "{mark.title}" → "{row.title}"'))
    return diffs


def _values(kind: ChangeKind, mark: OrderMark, item: Assignment) -> tuple[str, str]:
    row = item.order.row
    if kind is ChangeKind.PRIORITY:
        return mark.priority_raw or "trống", row.priority_raw or "trống"
    if kind is ChangeKind.DUE:
        return _day(mark.due), _day(row.due)
    return mark.title, row.title


def _day(value: date | None) -> str:
    return f"{value:%d/%m/%Y}" if value is not None else "trống"
