"""Write the order report of `scrumbot assign` (bot spec §7.3): one Markdown file, written to `.tmp` and renamed."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from scrumbot.model import Severity, Source
from scrumbot.model_risk import LEVEL_TEXT, RiskLevel
from scrumbot.normalize import LEVEL_NAMES
from scrumbot.rules.new_order import OrderReport, Placement
from scrumbot.understanding.sizing import ORDER_TYPES

FILE = "output.md"
_DATES = re.compile(r"\s*\(.*$")
# "Nếu xảy ra" of bot spec §7.3: one fixed sentence per risk code.
IF_IT_HAPPENS = {
    "CAPACITY-DEV": "Chuyển đơn chưa bắt đầu sang dev còn trống giờ; không còn ai trống thì lùi hạn đơn ưu tiên thấp.",
    "CAPACITY-SPRINT": "Chốt với BA/MO các đơn đẩy sang sprint sau; giữ lại đơn urgent/high.",
    "SCOPE-ADDED": "Báo BA/MO dời hạn đơn mới hoặc tách bớt hạng mục sang sprint sau.",
    "CARRY-OVER": "Làm xong việc dở trước; đơn mới chưa bắt đầu thì chuyển cho người dự phòng.",
    "PIC-UNFAMILIAR": "Chuyển cho người dự phòng đã làm app, hoặc ghép người đó review code.",
    "PIC-ABSENT": "Chuyển đơn cho người dự phòng ngay; không còn ai thì đẩy sang sprint sau.",
    "DUE-AT-RISK": "Báo BA/MO lùi hạn hoặc cắt bớt hạng mục; cần thì thêm người hỗ trợ.",
    "STATUS-STUCK": "Gặp người làm để gỡ vướng; vướng ở khâu test hoặc phát hành thì báo người phụ trách khâu đó.",
    "QA-RETURNS": "Dừng gửi test; review code và tự test lại trước khi gửi QA lần nữa.",
    "ORDER-CHANGED": "Ước lượng lại độ lớn và xác nhận lại hạn với BA/MO.",
}
RISK_HEADERS = ("Mức", "Mã", "Vấn đề", "Ảnh hưởng", "Phòng ngừa", "Nếu xảy ra", "Ai xử lý", "Hạn xử lý")


@dataclass(frozen=True)
class Header:
    """The facts of the run shown under the title."""

    sprint: str
    start: date | None
    end: date | None
    run_at: datetime
    freshness: datetime | None
    order_file: str
    prev_name: str
    sprint_risks: str  # "<x> cao · <y> trung bình · <z> thấp" of the whole register


def write_order_report(report: OrderReport, header: Header, out_dir: Path) -> Path:
    path = out_dir / FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(render(report, header), encoding="utf-8")
    os.replace(temporary, path)
    return path


def render(report: OrderReport, header: Header) -> str:
    item = report.item
    row, size = item.order.row, item.size
    dates = f" ({_day(header.start)} – {_day(header.end)})" if header.start and header.end else ""
    facts = [f"{short_name(header.sprint)}{dates}", f"chạy {header.run_at:%d/%m/%Y %H:%M}"]
    if header.freshness is not None:
        facts.append(f"dữ liệu API mới nhất {header.freshness:%d/%m/%Y %H:%M}")
    lines = [f"# Giao đơn: {row.title}", "", " · ".join(facts), "", "## Kết luận", ""]
    if item.source is Source.PROPOSED:
        lines += [
            f"- **PIC đề xuất: {item.pic_codes[0]}**",
            f"- Lý do: {item.reason}",
            f"- Dự phòng: {', '.join(item.backups) or 'không có'}",
        ]
    else:
        who = ", ".join(item.pic_codes) or "người ngoài team"
        lines.append(f"- **Đã có người làm trên hệ thống: {who}.** Bot giữ nguyên, không đề xuất PIC khác.")
    size_text = f"{size.size.name} ({size.size.value}h)" + (" (mặc định)" if size.is_default else "")
    lines.append(f"- Độ lớn (AI): {size_text}" + (f": {size.reason}" if size.reason else ""))
    counts = [sum(risk.level is level for risk in report.risks) for level in RiskLevel]
    lines.append(f"- Rủi ro liên quan: {counts[0]} cao · {counts[1]} trung bình · {counts[2]} thấp")
    if item.source is Source.PROPOSED:
        lines += ["", "Bot chưa ghi được vào hệ thống: TM nhập PIC vào hệ thống."]

    lines += ["", "## Thông tin đơn", "", "| Trường | Giá trị |", "|---|---|"]
    info = [
        ("Đơn", _placement(report.how, row.stt, row.id, short_name(header.sprint))),
        ("File đơn", header.order_file),
        ("App", row.app or "trống"),
        ("Ưu tiên", row.priority_raw or "trống"),
        ("Hạn", _day(row.due) if row.due else "trống"),
        ("Loại đơn (AI)", ORDER_TYPES.get(size.kind, "") or "—"),
        ("Hạng mục (AI)", "; ".join(size.items) or "—"),
        ("Mô tả AI đọc", row.description or "không có"),
    ]
    lines += [f"| {name} | {_cell(value)} |" for name, value in info]

    app = row.app or "app"
    lines += [
        "",
        "## So sánh dev",
        "",
        f"| Dev | Level | Quen {_cell(app)} | Đơn trong sprint | Giờ việc còn lại / sức chứa | Việc dở "
        f"{_cell(short_name(header.prev_name))} | Ngày nghỉ còn lại | Vai trò |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for dev in report.devs:
        hours = f"{dev.open_hours}h / {dev.capacity}h" if dev.capacity is not None else "—"
        cells = (dev.code, LEVEL_NAMES[dev.level], dev.familiarity, dev.orders, hours, dev.carry_over, dev.leave_days)
        role = f"**{dev.role}**" if dev.role in ("PIC", "Người làm") else dev.role
        lines.append("| " + " | ".join(_cell(cell) for cell in (*cells, role)) + " |")
    lines += ["", "Số đơn và giờ đã tính cả đơn này cho PIC."]

    lines += ["", "## Rủi ro và phương án dự phòng", ""]
    if report.risks:
        lines += ["| " + " | ".join(RISK_HEADERS) + " |", "|" + "---|" * len(RISK_HEADERS)]
        for risk in report.risks:
            cells = (
                LEVEL_TEXT[risk.level],
                risk.code,
                risk.problem,
                risk.impact,
                risk.action,
                IF_IT_HAPPENS.get(risk.code, ""),
                risk.owner,
                _day(risk.due) if risk.due else "",
            )
            lines.append("| " + " | ".join(_cell(cell) for cell in cells) + " |")
    else:
        lines.append("Không có rủi ro liên quan tới đơn này, PIC hoặc sprint.")
    lines += ["", f"Sổ rủi ro cả sprint: {header.sprint_risks} (chi tiết: `scrumbot run`)."]

    lines += ["", "## Rủi ro kỹ thuật (AI nhận xét, chỉ để tham khảo)", ""]
    lines += [f"- {text}" for text in size.tech_risks] or ["Không có."]

    lines += ["", "## Cảnh báo dữ liệu", ""]
    lines += [
        f"- {'WARN' if finding.severity is Severity.WARN else 'INFO'} `{finding.code}`: {finding.message}"
        for finding in report.findings
    ] or ["Không có cảnh báo."]
    return "\n".join(lines) + "\n"


def short_name(sprint: str) -> str:
    """`Sprint 10 (10/6 - 10/17)` → `Sprint 10`: the API's dates are month/day, the report writes its own."""
    return _DATES.sub("", sprint) or sprint


def _placement(how: Placement, stt: int, order_id: str, sprint: str) -> str:
    if how is Placement.NEW:
        return f"Đơn mới, chưa có trên hệ thống (tính là STT {stt} của {sprint})"
    found = "theo ID" if how is Placement.BY_ID else "theo tên đơn"
    return f"Đơn trên hệ thống, ID {order_id}, STT {stt} (nối {found})"


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _day(value: date | None) -> str:
    return f"{value:%d/%m/%Y}" if value is not None else ""
