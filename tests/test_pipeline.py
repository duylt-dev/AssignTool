from dataclasses import replace
from datetime import date

import pytest

from scrumbot.errors import InputError
from scrumbot.model import (
    Dev,
    HistoryOrder,
    Level,
    Order,
    Priority,
    RuleKind,
    Size,
    SizeEstimate,
    SprintRow,
    SprintSheet,
    TeamRule,
)
from scrumbot.rules.pipeline import build_result

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


def test_pipeline_warns_when_a_kept_order_is_held_only_by_a_dev_off_for_the_whole_sprint() -> None:
    """PRE-ASSIGNED-ON-LEAVE (A43): fires when nobody else in the pool holds the order, which is still kept (D10)."""
    target_sheet, orders = target(clear_assignees=True)
    off = Dev("Đỗ Văn Nghỉ", "OFF", Level.MIDDLE, True, tuple(date(2026, 10, day) for day in range(6, 17)))
    back = Dev("Đỗ Văn Nghỉ", "OFF", Level.MIDDLE, True, (date(2026, 10, 6),))

    def warnings(people: tuple[str, ...], devs: tuple[Dev, ...]) -> list[tuple[str, str, str]]:
        kept = tuple(Order(replace(o.row, assignees=people), o.priority) if o.row.stt == 7 else o for o in orders)
        result = build_result(
            target=target_sheet,
            prev=previous(),
            prev_name="Sprint 9",
            orders=kept,
            findings=(),
            devs=devs,
            history=(),
            sizes={order.row.stt: SizeEstimate(Size.M, "", True) for order in orders},
            sizing_note="AI off",
        )
        assert next(a for a in result.assignments if a.order.row.stt == 7).source.name == "PREASSIGNED"
        return [(f.code, f.where, f.message) for f in result.findings if f.code == "PRE-ASSIGNED-ON-LEAVE"]

    assert warnings(("đỗ  văn nghỉ", "QA Ngoài"), (*DEVS, off)) == [
        (
            "PRE-ASSIGNED-ON-LEAVE",
            "Đơn STT 7",
            "Đơn STT 7 giao sẵn cho OFF nhưng OFF nghỉ cả sprint; đơn chưa có ai làm, cân nhắc giao lại.",
        )
    ]
    assert warnings(("Đỗ Văn Nghỉ", LINH.name), (*DEVS, off)) == []  # LinhNV still works on it
    assert warnings(("Đỗ Văn Nghỉ",), (*DEVS, back)) == []  # off one day only


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


def test_pipeline_reports_rules_that_cannot_act_and_orders_they_left_without_candidates() -> None:
    """RULE-DEV-UNAVAILABLE and RULE-NO-CANDIDATE fire; the same run with rules that can act reports neither."""
    target_sheet, orders = target(clear_assignees=True)
    out = Dev("Out", "OutDev", Level.MIDDLE, False, ())

    def findings(*rules: TeamRule) -> list[tuple[str, str, str]]:
        result = build_result(
            target=target_sheet,
            prev=previous(),
            prev_name="Sprint 9",
            orders=orders,
            findings=(),
            devs=(*DEVS, out),
            history=history(),
            sizes={order.row.stt: SizeEstimate(Size.M, "", True) for order in orders},
            sizing_note="AI off",
            rules=rules,
        )
        return [(finding.code, finding.where, finding.message) for finding in result.findings]

    every = tuple(TeamRule(RuleKind.EXCLUDE, dev.code, "PS Remote", None, None, None, "", 2) for dev in DEVS)
    pin_out = TeamRule(RuleKind.PIN, "outdev", "AR Dog", None, None, None, "", 3)
    assert findings(pin_out, *every) == [
        (
            "RULE-DEV-UNAVAILABLE",
            "Luật dòng 3",
            "Luật dòng 3 (Chỉ định OutDev) không áp dụng: OutDev không nhận việc hoặc nghỉ cả sprint.",
        ),
        (
            "RULE-NO-CANDIDATE",
            "Đơn STT 7",
            "Luật TM loại hết dev khỏi đơn STT 7; đơn này được giao như khi không có luật Không giao và Tối đa đơn.",
        ),
    ]
    assert findings(TeamRule(RuleKind.PIN, "LinhNV", "AR Dog", None, None, None, "", 3), *every[1:]) == []


def test_a_dev_off_every_remaining_day_takes_no_new_order_from_the_base_day_on() -> None:
    """R8 (A75): AnTD is off 14–17/10; run on 14/10 he is out with DEV-ON-LEAVE-REST, run on 06/10 he is in."""
    off_rest = replace(AN, leave_days=tuple(date(2026, 10, day) for day in (14, 15, 16, 17)))
    target_sheet, orders = target(clear_assignees=True)

    def run_on(day: date):
        return build_result(
            target=target_sheet,
            prev=previous(),
            prev_name="Sprint 9",
            orders=orders,
            findings=(),
            devs=(LINH, MINH, off_rest, TIEN),
            history=history(),
            sizes={order.row.stt: SizeEstimate(Size.M, "", True) for order in orders},
            sizing_note="AI off",
            run_day=day,
        )

    late, early = run_on(date(2026, 10, 14)), run_on(date(2026, 10, 6))

    assert [(f.code, f.where, f.message) for f in late.findings if f.code == "DEV-ON-LEAVE-REST"] == [
        (
            "DEV-ON-LEAVE-REST",
            "AnTD",
            "AnTD nghỉ hết các ngày còn lại của sprint (từ 14/10/2026); không được giao đơn mới.",
        )
    ]
    assert all("AnTD" not in item.pic_codes for item in late.assignments)
    assert not [f for f in early.findings if f.code == "DEV-ON-LEAVE-REST"]
    assert any("AnTD" in item.pic_codes for item in early.assignments)
