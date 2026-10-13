"""Turn target rows into orders and report non-fatal data issues."""

from __future__ import annotations

from scrumbot.model import Finding, Order, Priority, Severity, SprintSheet
from scrumbot.normalize import app_key, parse_priority, text_key


def history_findings(file_used: bool, sheet_names: tuple[str, ...]) -> tuple[Finding, ...]:
    """Say where familiarity came from when there was no history file (spec §5, §9)."""
    if file_used:
        return ()
    if sheet_names:
        sheets = ", ".join(sheet_names)
        return (
            Finding(
                Severity.INFO,
                "HISTORY-FROM-WORKBOOK",
                sheets,
                f"Không có file lịch sử; dùng sheet {sheets} trong workbook làm lịch sử.",
            ),
        )
    return (
        Finding(
            Severity.WARN,
            "HISTORY-MISSING",
            "Lịch sử",
            "Không có file lịch sử và workbook không có sheet sprint cũ; coi như chưa ai làm app nào.",
        ),
    )


def orders_and_findings(target: SprintSheet) -> tuple[tuple[Order, ...], tuple[Finding, ...]]:
    """Return assignable orders and the validation findings for a target sheet."""
    orders: list[Order] = []
    findings: list[Finding] = []
    for row in target.rows:
        kind = text_key(row.kind)
        if kind == "subtask":
            continue
        if kind != "task":
            findings.append(
                Finding(
                    Severity.WARN,
                    "TYPE-UNKNOWN",
                    f"Dòng STT {row.stt}",
                    f'Dòng STT {row.stt} có Loại "{row.kind}" không hợp lệ; bỏ qua dòng này.',
                )
            )
            continue

        priority = parse_priority(row.priority_raw)
        where = f"Đơn STT {row.stt}"
        if priority is None:
            findings.append(
                Finding(
                    Severity.WARN,
                    "PRIORITY-UNKNOWN",
                    where,
                    f'Đơn STT {row.stt} có Ưu tiên "{row.priority_raw}" không hợp lệ; coi như normal.',
                )
            )
            priority = Priority.NORMAL
        if not app_key(row.app):
            findings.append(
                Finding(
                    Severity.WARN,
                    "APP-MISSING",
                    where,
                    f"Đơn STT {row.stt} không có App Name; coi như app chưa ai làm.",
                )
            )
        if row.due is None and priority in (Priority.URGENT, Priority.HIGH):
            findings.append(
                Finding(
                    Severity.WARN,
                    "DUE-MISSING",
                    where,
                    f"Đơn STT {row.stt} là đơn {priority.name.lower()} nhưng chưa có Hạn.",
                )
            )
        if row.due is not None and row.created is not None and row.due < row.created:
            findings.append(
                Finding(
                    Severity.WARN,
                    "DUE-BEFORE-CREATED",
                    where,
                    f"Đơn STT {row.stt} có Hạn {row.due:%d/%m/%Y} trước Ngày tạo {row.created:%d/%m/%Y}.",
                )
            )
        orders.append(Order(row, priority))
    return tuple(orders), tuple(findings)
