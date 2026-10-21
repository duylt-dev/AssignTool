"""`output.md` of `scrumbot review` (bot spec §7.3) and of `scrumbot assign` (§7.4), built from the standard outcome
alone; the later run replaces it (D64). Written to `.tmp` and renamed."""

from __future__ import annotations

import os
import re
from datetime import date
from pathlib import Path

from scrumbot.core.model import ORDER_KINDS, ORDER_TYPES, OrderKind, Placement, Severity
from scrumbot.core.model_risk import IF_IT_HAPPENS, LEVEL_TEXT, RiskLevel
from scrumbot.core.normalize import LEVEL_NAMES
from scrumbot.core.outcome import AiReview, Outcome, Status
from scrumbot.core.review.templates import OTHER

FILE = "output.md"
RISK_HEADERS = ("Mức", "Mã", "Vấn đề", "Ảnh hưởng", "Phòng ngừa", "Nếu xảy ra", "Ai xử lý", "Hạn xử lý")
QUESTIONS = "Câu hỏi của AI cho người lên đơn (không chặn; trả lời trong file đơn nếu cần):"
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
    """A `review` outcome carries no assignment."""
    lines = _review(outcome) if outcome.assignment is None else _report(outcome)
    return "\n".join(lines) + "\n"


def short_name(sprint: str) -> str:
    """`Sprint 10 (10/6 - 10/17)` → `Sprint 10`: the API's dates are month/day, the report writes its own."""
    return _DATES.sub("", sprint) or sprint


def risk_counts(levels: list[RiskLevel]) -> str:
    """`<x> cao · <y> trung bình · <z> thấp`."""
    high, medium, low = (sum(found is level for found in levels) for level in RiskLevel)
    return f"{high} cao · {medium} trung bình · {low} thấp"


def kind_of(ai: AiReview | None) -> OrderKind | None:
    """The type the review used (the file's or the AI's), when it is one of the 8 of the process."""
    try:
        return OrderKind(ai.kind) if ai is not None else None
    except ValueError:
        return None


def _review(outcome: Outcome) -> list[str]:
    """What blocks the order, or the AI's template check and questions, then the order as placed (bot spec §7.3)."""
    order, ai = outcome.order, outcome.ai
    lines = _top(outcome, "Review đơn")
    if outcome.status is Status.NOT_READY:
        lines += [
            "## Review: chưa đạt",
            "",
            f"Sửa các mục dưới đây rồi chạy lại `scrumbot review {order.origin}`:",
            "",
            *(f"- `{item.code}`: {item.message}" for item in outcome.review),
        ]
        if ai is not None and ai.questions:
            lines += ["", QUESTIONS, "", *(f"- {question}" for question in ai.questions)]
    elif outcome.status is Status.PRE_ASSIGNED:
        lines += [
            "## Review: không cần",
            "",
            "Đơn đã có người làm trên hệ thống: bot giữ nguyên, không review. "
            f"Chạy `scrumbot assign {order.origin}` để xem người làm và rủi ro.",
        ]
    else:
        lines += ["## Review: đạt", "", _template_line(ai), ""]
        if ai is not None and ai.questions:
            lines += [QUESTIONS, "", *(f"- {question}" for question in ai.questions)]
        elif ai is not None and ai.answered:
            lines.append("AI không có câu hỏi.")
        else:
            lines.append("Không có câu hỏi của AI (AI tắt hoặc lỗi).")
        lines += [
            "",
            f"Chạy `scrumbot assign {order.origin}` để bot đề xuất PIC. Sửa file đơn sau lần review này thì phải "
            "review lại.",
        ]
    lines += ["", *_info(outcome, _review_rows(outcome))]
    return lines


def _template_line(ai: AiReview | None) -> str:
    kind = kind_of(ai)
    if ai is not None and ai.checked and kind is not None:
        return f"Mô tả đủ ý của mẫu {ORDER_KINDS[kind]} (AI chấm)."
    if ai is not None and ai.kind == OTHER:
        return "AI xếp đơn ngoài 8 loại đơn của quy trình (vd app mới, theo SRS riêng): chưa chấm theo mẫu."
    return "Chưa chấm mô tả theo mẫu loại đơn (AI tắt hoặc lỗi)."


def _review_rows(outcome: Outcome) -> tuple[tuple[str, str], ...]:
    """What the review adds to `Thông tin đơn` (bot spec §7.3); the table of `assign` stays as it was (A110)."""
    order, ai = outcome.order, outcome.ai
    kind = kind_of(ai)
    if order.kind is not None:
        kind_text = f"{ORDER_KINDS[order.kind]} (file đơn)"
    elif kind is not None:
        kind_text = f"{ORDER_KINDS[kind]} (AI)"
    elif ai is not None and ai.kind == OTHER:
        kind_text = "ngoài 8 loại (AI)"
    else:
        kind_text = "trống"
    return (
        ("Loại đơn", kind_text),
        ("Người chịu trách nhiệm", order.owner or "trống"),
        ("Bằng chứng", order.evidence or "trống"),
    )


def _report(outcome: Outcome) -> list[str]:
    item, order = outcome.assignment, outcome.order
    assert item is not None  # an `assign` outcome always carries its assignment
    size = item.size
    proposed = outcome.status is Status.PROPOSED
    lines = _top(outcome, "Giao đơn")
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

    ai = (("Loại đơn (AI)", ORDER_TYPES.get(size.kind, "") or "—"), ("Hạng mục (AI)", "; ".join(size.items) or "—"))
    lines += ["", *_info(outcome, ai)]

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


def _top(outcome: Outcome, heading: str) -> list[str]:
    """The title and the facts of the run (bot spec §7.3, §7.4)."""
    sprint = outcome.sprint
    dates = f" ({_day(sprint.start)} – {_day(sprint.end)})" if sprint.start and sprint.end else ""
    facts = [f"{short_name(sprint.name)}{dates}", f"chạy {outcome.run_at:%d/%m/%Y %H:%M}"]
    if outcome.freshness is not None:
        facts.append(f"dữ liệu API mới nhất {outcome.freshness:%d/%m/%Y %H:%M}")
    return [f"# {heading}: {outcome.order.title}", "", " · ".join(facts), ""]


def _info(outcome: Outcome, extra: tuple[tuple[str, str], ...]) -> list[str]:
    """The table `Thông tin đơn`; `extra` (what the review read, or what the AI said in `assign`) comes before the
    description."""
    order = outcome.order
    rows = (
        ("Đơn", _placement(outcome)),
        ("File đơn", order.origin),
        ("App", order.app or "trống"),
        ("Ưu tiên", order.priority_raw or "trống"),
        ("Hạn", _day(order.due) if order.due else "trống"),
        *extra,
        ("Mô tả AI đọc", order.description or "không có"),
    )
    return [
        "## Thông tin đơn",
        "",
        "| Trường | Giá trị |",
        "|---|---|",
        *(f"| {name} | {_cell(value)} |" for name, value in rows),
    ]


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
