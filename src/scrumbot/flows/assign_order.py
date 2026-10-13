"""`scrumbot assign <file>` (bot spec §7): one order file of BA/MO in the running sprint, decided as `run` decides,
written as one Markdown report. The memory is read; only AI answers of the other orders are written."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from scrumbot.actions.md_report import Header, short_name, write_order_report
from scrumbot.errors import InputError
from scrumbot.flows.common import Options, Say, risk_counts
from scrumbot.flows.run_api import decide
from scrumbot.model import Severity, Source
from scrumbot.model_risk import RiskLevel
from scrumbot.rules.new_order import Placement, order_report
from scrumbot.sources.order_reader import read_order


def assign_order(options: Options, order_file: Path, say: Say, now: datetime) -> Path:
    if not order_file.is_file():
        raise InputError(f"Không có file đơn '{order_file}'.")
    draft = read_order(order_file)
    decision = decide(options, say, now, draft, order_file)
    placed = decision.placed
    assert placed is not None  # decide() places every draft
    report = order_report(decision.result, placed, decision.team, decision.history)
    header = Header(
        sprint=decision.result.sheet_name,
        start=decision.sprint.start,
        end=decision.sprint.end,
        run_at=decision.run_at,
        freshness=decision.freshness,
        order_file=str(order_file),
        prev_name=decision.result.prev_sheet_name,
        sprint_risks=risk_counts(decision.result),
    )
    path = write_order_report(report, header, options.out_dir)
    item = report.item
    where = "đơn mới" if placed.how is Placement.NEW else f"đơn trên hệ thống {item.order.row.id}"
    size = item.size
    say(f"Đơn: {item.order.row.title} ({where}, STT {placed.stt} của {short_name(decision.result.sheet_name)})")
    say(f"Độ lớn: {size.size.name}" + (" (mặc định)" if size.is_default else "") + f" · {decision.result.sizing_note}")
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
