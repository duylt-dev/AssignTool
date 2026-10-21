"""The lines `scrumbot review` and `scrumbot assign` print (bot spec §7.3, §7.4): what the run read, before the AI is
called, then what it decided. `cli.py` prints them."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from scrumbot.core.model import ORDER_KINDS, Placement, Severity
from scrumbot.core.outcome import Outcome, Status
from scrumbot.core.place import Placed
from scrumbot.core.review.templates import OTHER
from scrumbot.output.markdown import kind_of, risk_counts, short_name


def run_day(day: date) -> str:
    return f"Ngày chạy: {day:%d/%m/%Y} (--today)"


def placed_lines(placed: Placed) -> list[str]:
    """The source, the TM rules, the history and the placed order."""
    inputs, row = placed.inputs, placed.order.row
    fresh = f" (dữ liệu mới nhất {placed.freshness:%d/%m/%Y %H:%M})" if placed.freshness else ""
    rules = (
        f"Luật TM: file {Path(inputs.rules_source).name} ({len(inputs.rules)} luật, "
        f"{len(placed.rules)} có hiệu lực ngày {placed.rules_day:%d/%m/%Y})"
        if inputs.rules_source
        else "Luật TM: không có"
    )
    where = "đơn mới" if placed.order.how is Placement.NEW else f"đơn trên hệ thống {row.id}"
    return [
        f"Nguồn: {inputs.source}{fresh}",
        rules,
        f"Lịch sử: API ({len(placed.history)} đơn gốc)",
        f"Đơn: {row.title} ({where}, STT {row.stt} của {short_name(placed.sprint.name)})",
    ]


def review_lines(outcome: Outcome, report: Path) -> list[str]:
    """What blocks the order, or the AI's template check and how many questions it asked; then the path of the
    report."""
    if outcome.status is Status.NOT_READY:
        lines = [
            f"Review: chưa đạt ({len(outcome.review)} mục)",
            *(f"- {review.code}: {review.message}" for review in outcome.review),
        ]
    elif outcome.status is Status.PRE_ASSIGNED:
        lines = ["Review: không cần (đơn đã có người làm)"]
    else:
        ai, kind = outcome.ai, kind_of(outcome.ai)
        if ai is not None and ai.checked and kind is not None:
            template = f"đủ ý mẫu {ORDER_KINDS[kind]}"
        else:
            template = "ngoài 8 loại đơn" if ai is not None and ai.kind == OTHER else "chưa chấm theo mẫu"
        asked = (
            f"{len(ai.questions)} câu hỏi của AI"
            if ai is not None and ai.answered
            else f"không có câu hỏi của AI: {ai.note if ai is not None else 'tắt AI'}"
        )
        lines = [f"Review: đạt ({template}; {asked})", f"Tiếp theo: scrumbot assign {outcome.order.origin}"]
    return [*lines, f"Báo cáo: {report}"]


def assign_lines(outcome: Outcome, report: Path) -> list[str]:
    """The size, the PIC and the risks; then the path of the report."""
    item = outcome.assignment
    assert item is not None  # an `assign` outcome always carries its assignment
    size = item.size
    lines = [f"Độ lớn: {size.size.name}" + (" (mặc định)" if size.is_default else "") + f" · {outcome.sizing_note}"]
    if outcome.status is Status.PROPOSED:
        lines.append(f"PIC đề xuất: {item.pic_codes[0]} (dự phòng: {', '.join(item.backups) or 'không có'})")
    else:
        lines.append(f"Đã có người làm: {', '.join(item.pic_codes) or 'người ngoài team'} (giữ nguyên)")
    lines.append(f"Rủi ro liên quan: {risk_counts([risk.level for risk in outcome.risks])}")
    lines += [f"WARN {f.code}: {f.message}" for f in outcome.findings if f.severity is Severity.WARN]
    lines.append(f"Báo cáo: {report}")
    return lines
