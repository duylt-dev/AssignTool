"""The lines `scrumbot assign` prints (bot spec §7.4): what the run read, before the AI is called, then what it
decided. `cli.py` prints them."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from scrumbot.core.engine import Prepared
from scrumbot.core.model import Placement, Severity
from scrumbot.core.outcome import Outcome, Status
from scrumbot.output.markdown import risk_counts, short_name


def run_day(day: date) -> str:
    return f"Ngày chạy: {day:%d/%m/%Y} (--today)"


def prepared_lines(prepared: Prepared) -> list[str]:
    """The source, the TM rules, the history and the placed order."""
    inputs, row = prepared.inputs, prepared.placed.row
    fresh = f" (dữ liệu mới nhất {prepared.freshness:%d/%m/%Y %H:%M})" if prepared.freshness else ""
    rules = (
        f"Luật TM: file {Path(inputs.rules_source).name} ({len(inputs.rules)} luật, "
        f"{len(prepared.rules)} có hiệu lực ngày {prepared.rules_day:%d/%m/%Y})"
        if inputs.rules_source
        else "Luật TM: không có"
    )
    where = "đơn mới" if prepared.placed.how is Placement.NEW else f"đơn trên hệ thống {row.id}"
    return [
        f"Nguồn: {inputs.source}{fresh}",
        rules,
        f"Lịch sử: API ({len(prepared.history)} đơn gốc)",
        f"Đơn: {row.title} ({where}, STT {row.stt} của {short_name(prepared.sprint.name)})",
    ]


def outcome_lines(outcome: Outcome, report: Path) -> list[str]:
    """The review, or the size, the PIC and the risks; then the path of the report."""
    item = outcome.assignment
    if outcome.status is Status.NOT_READY or item is None:
        return [
            f"Review: chưa đạt ({len(outcome.review)} mục)",
            *(f"- {review.code}: {review.message}" for review in outcome.review),
            f"Báo cáo: {report}",
        ]
    size = item.size
    lines = []
    if outcome.status is Status.PROPOSED:
        lines.append(f"Review: đạt ({len(size.questions)} câu hỏi của AI)")
    lines.append(f"Độ lớn: {size.size.name}" + (" (mặc định)" if size.is_default else "") + f" · {outcome.sizing_note}")
    if outcome.status is Status.PROPOSED:
        lines.append(f"PIC đề xuất: {item.pic_codes[0]} (dự phòng: {', '.join(item.backups) or 'không có'})")
    else:
        lines.append(f"Đã có người làm: {', '.join(item.pic_codes) or 'người ngoài team'} (giữ nguyên)")
    lines.append(f"Rủi ro liên quan: {risk_counts([risk.level for risk in outcome.risks])}")
    lines += [f"WARN {f.code}: {f.message}" for f in outcome.findings if f.severity is Severity.WARN]
    lines.append(f"Báo cáo: {report}")
    return lines
