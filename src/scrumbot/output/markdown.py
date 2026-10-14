"""`output.md` of `scrumbot assign`, built from the standard outcome alone: the review when the order is not ready
(bot spec §7.3), else the full report (§7.4). Written to `.tmp` and renamed."""

from __future__ import annotations

import os
import re
from datetime import date
from pathlib import Path

from scrumbot.core.model import ORDER_TYPES, Placement, Severity
from scrumbot.core.model_risk import IF_IT_HAPPENS, LEVEL_TEXT, RiskLevel
from scrumbot.core.normalize import LEVEL_NAMES
from scrumbot.core.outcome import Outcome, Status

FILE = "output.md"
RISK_HEADERS = ("Mức", "Mã", "Vấn đề", "Ảnh hưởng", "Phòng ngừa", "Nếu xảy ra", "Ai xử lý", "Hạn xử lý")
_DATES = re.compile(r"\s*\(.*$")


def write(outcome: Outcome, out_dir: Path) -> Path:
    """`<out_dir>/output.md`, replacing the previous one (A85)."""
    path = out_dir / FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(render(outcome), encoding="utf-8")
    os.replace(temporary, path)
    return path


def render(outcome: Outcome) -> str:
    lines = _review(outcome) if outcome.status is Status.NOT_READY else _report(outcome)
    return "\n".join(lines) + "\n"


def short_name(sprint: str) -> str:
    """`Sprint 10 (10/6 - 10/17)` → `Sprint 10`: the API's dates are month/day, the report writes its own."""
    return _DATES.sub("", sprint) or sprint


def risk_counts(levels: list[RiskLevel]) -> str:
    """`<x> cao · <y> trung bình · <z> thấp`."""
    high, medium, low = (sum(found is level for found in levels) for level in RiskLevel)
    return f"{high} cao · {medium} trung bình · {low} thấp"


def _review(outcome: Outcome) -> list[str]:
    """The order is not ready (bot spec §7.3): only what to fix, no PIC."""
    return [
        *_top(outcome),
        "## Review: chưa đạt",
        "",
        f"Bot chưa đề xuất PIC. Sửa các mục dưới đây rồi chạy lại `scrumbot assign {outcome.order.origin}`:",
        "",
        *(f"- `{item.code}`: {item.message}" for item in outcome.review),
    ]


def _report(outcome: Outcome) -> list[str]:
    item, order = outcome.assignment, outcome.order
    assert item is not None  # a ready outcome always carries its assignment
    size = item.size
    proposed = outcome.status is Status.PROPOSED
    lines = _top(outcome)
    if proposed:  # a pre-assigned order is not reviewed (A87)
        lines += ["## Review: đạt", ""]
        if size.is_default:
            lines.append("Không có câu hỏi của AI (AI tắt hoặc lỗi).")
        elif size.questions:
            lines += ["Câu hỏi của AI cho người lên đơn (không chặn; trả lời trong file đơn nếu cần):", ""]
            lines += [f"- {question}" for question in size.questions]
        else:
            lines.append("AI không có câu hỏi.")
        lines.append("")
    lines += ["## Kết luận", ""]
    if proposed:
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
    lines.append(f"- Rủi ro liên quan: {risk_counts([risk.level for risk in outcome.risks])}")
    if proposed:
        lines += ["", "Bot chưa ghi được vào hệ thống: người lên đơn nhập PIC vào hệ thống."]

    lines += ["", "## Thông tin đơn", "", "| Trường | Giá trị |", "|---|---|"]
    info = [
        ("Đơn", _placement(outcome)),
        ("File đơn", order.origin),
        ("App", order.app or "trống"),
        ("Ưu tiên", order.priority_raw or "trống"),
        ("Hạn", _day(order.due) if order.due else "trống"),
        ("Loại đơn (AI)", ORDER_TYPES.get(size.kind, "") or "—"),
        ("Hạng mục (AI)", "; ".join(size.items) or "—"),
        ("Mô tả AI đọc", order.description or "không có"),
    ]
    lines += [f"| {name} | {_cell(value)} |" for name, value in info]

    app = order.app or "app"
    lines += [
        "",
        "## So sánh dev",
        "",
        f"| Dev | Level | Quen {_cell(app)} | Đơn trong sprint | Giờ việc còn lại / sức chứa | Việc dở "
        f"{_cell(short_name(outcome.sprint.previous))} | Ngày nghỉ còn lại | Vai trò |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for dev in outcome.devs:
        hours = f"{dev.open_hours}h / {dev.capacity}h" if dev.capacity is not None else "—"
        cells = (dev.code, LEVEL_NAMES[dev.level], dev.familiarity, dev.orders, hours, dev.carry_over, dev.leave_days)
        role = f"**{dev.role}**" if dev.role in ("PIC", "Người làm") else dev.role
        lines.append("| " + " | ".join(_cell(cell) for cell in (*cells, role)) + " |")
    lines += ["", "Số đơn và giờ đã tính cả đơn này cho PIC."]

    lines += ["", "## Rủi ro và phương án dự phòng", ""]
    if outcome.risks:
        lines += ["| " + " | ".join(RISK_HEADERS) + " |", "|" + "---|" * len(RISK_HEADERS)]
        for risk in outcome.risks:
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
    counts = outcome.sprint_risks
    lines += ["", f"Sổ rủi ro cả sprint: {counts.high} cao · {counts.medium} trung bình · {counts.low} thấp."]

    lines += ["", "## Rủi ro kỹ thuật (AI nhận xét, chỉ để tham khảo)", ""]
    lines += [f"- {text}" for text in size.tech_risks] or ["Không có."]

    lines += ["", "## Cảnh báo dữ liệu", ""]
    lines += [
        f"- {'WARN' if finding.severity is Severity.WARN else 'INFO'} `{finding.code}`: {finding.message}"
        for finding in outcome.findings
    ] or ["Không có cảnh báo."]
    return lines


def _top(outcome: Outcome) -> list[str]:
    """The title and the facts of the run (bot spec §7.3, §7.4)."""
    sprint = outcome.sprint
    dates = f" ({_day(sprint.start)} – {_day(sprint.end)})" if sprint.start and sprint.end else ""
    facts = [f"{short_name(sprint.name)}{dates}", f"chạy {outcome.run_at:%d/%m/%Y %H:%M}"]
    if outcome.freshness is not None:
        facts.append(f"dữ liệu API mới nhất {outcome.freshness:%d/%m/%Y %H:%M}")
    return [f"# Giao đơn: {outcome.order.title}", "", " · ".join(facts), ""]


def _placement(outcome: Outcome) -> str:
    order = outcome.order
    if order.placement is Placement.NEW:
        return f"Đơn mới, chưa có trên hệ thống (tính là STT {order.stt} của {short_name(outcome.sprint.name)})"
    found = "theo ID" if order.placement is Placement.BY_ID else "theo tên đơn"
    return f"Đơn trên hệ thống, ID {order.id}, STT {order.stt} (nối {found})"


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _day(value: date | None) -> str:
    return f"{value:%d/%m/%Y}" if value is not None else ""
