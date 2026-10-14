"""`scrumbot assign <file>` (bot spec §7): one order file of BA/MO placed in the running sprint, reviewed, then decided
on the whole sprint and written as one Markdown report. Only AI answers of the other orders are remembered."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path

from scrumbot.actions.md_report import Header, short_name, write_order_report, write_review_report
from scrumbot.errors import InputError
from scrumbot.flows.common import Options, Say, risk_counts
from scrumbot.flows.decide import decide, prepare
from scrumbot.model import Severity, Source
from scrumbot.model_risk import RiskLevel
from scrumbot.rules.new_order import Placement, order_report
from scrumbot.rules.review import review
from scrumbot.sources.order_reader import read_order


def assign_order(options: Options, order_file: Path, say: Say, now: datetime) -> Path:
    if not order_file.is_file():
        raise InputError(f"Không có file đơn '{order_file}'.")
    draft = read_order(order_file)
    prepared = prepare(options, say, now, draft, order_file)
    placed, sprint = prepared.placed, prepared.sprint
    row = placed.row
    header = Header(
        sprint=placed.sheet.name,
        start=sprint.start,
        end=sprint.end,
        run_at=prepared.run_at,
        freshness=prepared.freshness,
        order_file=str(order_file),
    )
    where = "đơn mới" if placed.how is Placement.NEW else f"đơn trên hệ thống {row.id}"
    say(f"Đơn: {row.title} ({where}, STT {placed.stt} của {short_name(placed.sheet.name)})")

    blocking = review(row, placed.how)
    if blocking:  # not ready: no AI call, no assignment, no register (A86)
        say(f"Review: chưa đạt ({len(blocking)} mục)")
        for item in blocking:
            say(f"- {item.code}: {item.message}")
        path = write_review_report(row.title, blocking, header, options.out_dir)
        say(f"Báo cáo: {path}")
        return path

    decision = decide(prepared, options, say)
    result = decision.result
    report = order_report(result, placed, decision.team, prepared.history)
    header = replace(header, prev_name=result.prev_sheet_name, sprint_risks=risk_counts(result))
    path = write_order_report(report, header, options.out_dir)
    item = report.item
    size = item.size
    if item.source is Source.PROPOSED:
        say(f"Review: đạt ({len(size.questions)} câu hỏi của AI)")
    say(f"Độ lớn: {size.size.name}" + (" (mặc định)" if size.is_default else "") + f" · {result.sizing_note}")
    if item.source is Source.PROPOSED:
        say(f"PIC đề xuất: {item.pic_codes[0]} (dự phòng: {', '.join(item.backups) or 'không có'})")
    else:
        say(f"Đã có người làm: {', '.join(item.pic_codes) or 'người ngoài team'} (giữ nguyên)")
    counts = [sum(risk.level is level for risk in report.risks) for level in RiskLevel]
    say(f"Rủi ro liên quan: {counts[0]} cao · {counts[1]} trung bình · {counts[2]} thấp")
    for finding in report.findings:
        if finding.severity is Severity.WARN:
            say(f"WARN {finding.code}: {finding.message}")
    say(f"Báo cáo: {path}")
    return path
