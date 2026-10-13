from datetime import date

from scrumbot.model import Priority, SprintRow, SprintSheet
from scrumbot.rules.validate import orders_and_findings


def row(stt: int, **changes: object) -> SprintRow:
    values: dict[str, object] = {
        "title": f"Order {stt}",
        "kind": "Task",
        "app": "App",
        "assignees": (),
        "status": "",
        "priority_raw": "normal",
        "due": None,
        "created": None,
        "description": "",
        "cells": (),
    }
    values.update(changes)
    return SprintRow(stt=stt, **values)  # type: ignore[arg-type]


def sheet(*rows: SprintRow) -> SprintSheet:
    return SprintSheet("Sprint 10", 10, None, None, (), rows)


def test_orders_and_findings_reports_every_phase_finding() -> None:
    orders, findings = orders_and_findings(
        sheet(
            row(1, app="", priority_raw="rush", due=date(2026, 10, 5), created=date(2026, 10, 6)),
            row(2, kind="Feature"),
            row(3, kind="Subtask"),
        )
    )

    assert [(order.row.stt, order.priority) for order in orders] == [(1, Priority.NORMAL)]
    assert [(finding.code, finding.where) for finding in findings] == [
        ("PRIORITY-UNKNOWN", "Đơn STT 1"),
        ("APP-MISSING", "Đơn STT 1"),
        ("DUE-BEFORE-CREATED", "Đơn STT 1"),
        ("TYPE-UNKNOWN", "Dòng STT 2"),
    ]
    assert findings[2].message.endswith("05/10/2026 trước Ngày tạo 06/10/2026.")


def test_orders_and_findings_has_no_finding_for_clean_rows() -> None:
    orders, findings = orders_and_findings(sheet(row(1), row(2, kind="Subtask")))

    assert [order.row.stt for order in orders] == [1]
    assert findings == ()


def test_due_missing_fires_on_urgent_and_high_orders_without_a_due_date_only() -> None:
    _, findings = orders_and_findings(
        sheet(
            row(1, priority_raw="urgent"),
            row(2, priority_raw="high", due=date(2026, 10, 15)),
            row(3, priority_raw="high"),
            row(4, priority_raw="normal"),
        )
    )

    assert [(f.severity.value, f.code, f.where, f.message) for f in findings] == [
        ("WARN", "DUE-MISSING", "Đơn STT 1", "Đơn STT 1 là đơn urgent nhưng chưa có Hạn."),
        ("WARN", "DUE-MISSING", "Đơn STT 3", "Đơn STT 3 là đơn high nhưng chưa có Hạn."),
    ]
