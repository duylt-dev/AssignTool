from datetime import date

from assigntool.model import Priority, SprintRow, SprintSheet
from assigntool.rules.validate import orders_and_findings


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


def test_history_findings_say_where_familiarity_came_from() -> None:
    from assigntool.rules.validate import history_findings

    assert history_findings(True, ()) == ()
    (info,) = history_findings(False, ("Sprint 8", "Sprint 9"))
    assert (info.severity.value, info.code, info.where) == ("INFO", "HISTORY-FROM-WORKBOOK", "Sprint 8, Sprint 9")
    (warn,) = history_findings(False, ())
    assert (warn.severity.value, warn.code) == ("WARN", "HISTORY-MISSING")
