from datetime import date

import pytest

from assigntool.errors import InputError
from assigntool.model import (
    Dev,
    HistoryOrder,
    Level,
    Order,
    Priority,
    Size,
    SizeEstimate,
    SprintRow,
    SprintSheet,
)
from assigntool.rules.pipeline import build_result

LINH = Dev("Ngọc Văn Linh", "LinhNV", Level.MIDDLE_PLUS, True, ())
MINH = Dev("Nguyễn Nhật Minh", "MinhNM", Level.MIDDLE, True, ())
AN = Dev("Trần Đức An", "AnTD", Level.JUNIOR_PLUS, True, ())
TIEN = Dev("Bùi Văn Tiến", "TiếnBV", Level.JUNIOR, True, ())
DEVS = (LINH, MINH, AN, TIEN)


def target(*, clear_assignees: bool) -> tuple[SprintSheet, tuple[Order, ...]]:
    people = {
        1: (LINH.name, TIEN.name),
        7: (MINH.name,),
        10: (),
        14: (AN.name,),
        18: (LINH.name,),
        24: (AN.name,),
    }
    details = (
        (1, "Phone Cleaner 1.0.2", "Phone Cleaner", Priority.NORMAL, date(2026, 10, 5), None),
        (7, "PS Remote 1.1.2", "PS Remote", Priority.URGENT, date(2026, 10, 5), None),
        (10, "Roblox skin 1.0.4", "Roblox skin", Priority.NORMAL, date(2026, 9, 22), None),
        (14, "Auto click 1.1.1", "Auto click", Priority.NORMAL, date(2026, 9, 17), None),
        (18, "spin wheel 2 1.0.2", "spin wheel 2", Priority.NORMAL, date(2026, 10, 5), None),
        (24, "Game Emulator", "Game Emulator", Priority.HIGH, date(2026, 10, 5), date(2026, 10, 7)),
    )
    rows = tuple(
        SprintRow(
            stt,
            title,
            "Task",
            app,
            () if clear_assignees else people[stt],
            "",
            priority.name.lower(),
            due,
            created,
            "",
            (),
        )
        for stt, title, app, priority, created, due in details
    )
    return SprintSheet("Sprint 10", 10, date(2026, 10, 6), date(2026, 10, 17), (), rows), tuple(
        Order(row, priority) for row, (_, _, _, priority, _, _) in zip(rows, details, strict=True)
    )


def history() -> tuple[HistoryOrder, ...]:
    return (
        HistoryOrder("Sprint 9", "PS Remote", "1.1.0", (LINH.name, MINH.name), None, date(2026, 9, 1)),
        HistoryOrder("Sprint 9", "PS Remote", "1.1.1", (LINH.name, MINH.name), None, date(2026, 9, 2)),
        HistoryOrder("Sprint 9", "PS Remote", "research", ("RnD",), None, date(2026, 9, 3)),
        HistoryOrder("Sprint 9", "Game Emulator", "game", (AN.name,), None, date(2026, 9, 4)),
        HistoryOrder("Sprint 9", "AR Dog", "ar", (LINH.name,), None, date(2026, 9, 5)),
        HistoryOrder("Sprint 9", "metal detector", "metal", (LINH.name,), None, date(2026, 9, 6)),
        HistoryOrder("Sprint 9", "Santa prank", "santa", (LINH.name,), None, date(2026, 9, 7)),
        HistoryOrder("Sprint 9", "SpeakerCleaner", "speaker", (LINH.name,), None, date(2026, 9, 8)),
        HistoryOrder("Sprint 9", "Speak2", "speak", (MINH.name,), None, date(2026, 9, 9)),
        HistoryOrder("Sprint 9", "AR Dog", "old ar", (AN.name,), None, date(2026, 9, 10)),
        HistoryOrder("Sprint 9", "Game mode 2", "mode", (TIEN.name,), None, date(2026, 9, 11)),
        HistoryOrder("Sprint 9", "Other", "other", ("RnD",), None, date(2026, 9, 12)),
    )


def previous() -> SprintSheet:
    rows = (
        SprintRow(1, "Linh", "Task", "", (LINH.name,), "qa - need fix", "", None, None, "", ()),
        SprintRow(2, "Tien", "Task", "", (TIEN.name,), "need to be clean", "", None, None, "", ()),
        SprintRow(3, "Tien sub", "Subtask", "", (TIEN.name,), "internal - cant fix", "", None, None, "", ()),
        SprintRow(4, "Minh", "Task", "", (MINH.name,), "pending", "", None, None, "", ()),
    )
    return SprintSheet("Sprint 9", 9, None, None, (), rows)


def run(*, clear_assignees: bool):
    target_sheet, orders = target(clear_assignees=clear_assignees)
    return build_result(
        target=target_sheet,
        prev=previous(),
        prev_name="Sprint 9",
        orders=orders,
        findings=(),
        devs=DEVS,
        history=history(),
        sizes={order.row.stt: SizeEstimate(Size.M, "", True) for order in orders},
        sizing_note="AI off",
    )


def test_pipeline_reproduces_spec_sample_run_a_and_clean_findings() -> None:
    result = run(clear_assignees=False)

    proposed = next(item for item in result.assignments if item.order.row.stt == 10)
    assert proposed.pic_codes == ("MinhNM",)
    assert proposed.backups == ("LinhNV", "TiếnBV")
    assert result.findings == ()
    assert {item.dev.code: item.hours for item in result.devs} == {
        "LinhNV": 32,
        "MinhNM": 32,
        "AnTD": 32,
        "TiếnBV": 16,
    }


def test_pipeline_reproduces_spec_sample_run_b() -> None:
    result = run(clear_assignees=True)

    assert {item.order.row.stt: item.pic_codes[0] for item in result.assignments} == {
        1: "LinhNV",
        7: "MinhNM",
        10: "MinhNM",
        14: "LinhNV",
        18: "TiếnBV",
        24: "AnTD",
    }
    assert {item.dev.code: item.hours for item in result.devs} == {
        "LinhNV": 32,
        "MinhNM": 32,
        "AnTD": 16,
        "TiếnBV": 16,
    }


def test_pipeline_reports_missing_previous_and_full_sprint_leave() -> None:
    target_sheet, orders = target(clear_assignees=True)
    off = Dev("Off", "OFF", Level.MIDDLE, True, tuple(date(2026, 10, day) for day in range(6, 17)))
    result = build_result(
        target=target_sheet,
        prev=None,
        prev_name="Sprint 9",
        orders=orders,
        findings=(),
        devs=(LINH, off),
        history=(),
        sizes={order.row.stt: SizeEstimate(Size.M, "", True) for order in orders},
        sizing_note="AI off",
    )

    assert [(finding.code, finding.where) for finding in result.findings] == [
        ("PREV-SPRINT-MISSING", "Sprint 9"),
        ("DEV-ON-LEAVE", "OFF"),
    ]
    assert result.devs[-1].dev.code == "OFF" and result.devs[-1].on_leave_all_sprint


def test_pipeline_rejects_an_empty_available_pool() -> None:
    target_sheet, orders = target(clear_assignees=True)
    off = Dev("Off", "OFF", Level.MIDDLE, True, tuple(date(2026, 10, day) for day in range(6, 17)))

    with pytest.raises(InputError, match="Không còn dev nào"):
        build_result(
            target=target_sheet,
            prev=previous(),
            prev_name="Sprint 9",
            orders=orders,
            findings=(),
            devs=(off,),
            history=(),
            sizes={order.row.stt: SizeEstimate(Size.M, "", True) for order in orders},
            sizing_note="AI off",
        )
