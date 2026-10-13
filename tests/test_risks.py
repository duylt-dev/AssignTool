"""The risk register (bot spec §4): every code fires on its case and stays silent on the nearest case that must not
fire (LLM.md §8). Run through build_result, so each risk sees what a real run gives it."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime

from scrumbot.model import (
    Assignment,
    Dev,
    HistoryOrder,
    Priority,
    Size,
    SizeEstimate,
    Source,
    SprintRow,
    SprintSheet,
    StatusChange,
)
from scrumbot.model_risk import OrderMark, Risk, RiskLevel
from scrumbot.rules.pipeline import build_result
from scrumbot.rules.risk_register import defer_list, due_for, escalate, ordered
from scrumbot.rules.validate import orders_and_findings
from tests.api_builders import AN, LINH, MINH, POOL, TIEN

START, END = date(2026, 10, 6), date(2026, 10, 17)  # Tue 06/10 – Sat 17/10, as Sprint 10
TUESDAY = date(2026, 10, 13)  # 13–16/10 left: 4 working days, 24h of capacity per dev


def row(
    stt: int,
    *,
    status: str = "in progress",
    people: tuple[str, ...] = (),
    app: str = "Demo",
    priority: str = "",
    due: date | None = None,
    created: date = date(2026, 10, 1),
    kind: str = "Task",
    root: int | None = None,
    updated: datetime | None = None,
    kind_status: str = "",
    title: str | None = None,
) -> SprintRow:
    ident = f"o{stt}"
    return SprintRow(
        stt,
        title or f"Order {stt}",
        kind,
        app,
        people,
        status,
        priority,
        due,
        created,
        "",
        (),
        None,
        ident,
        f"o{root}" if root is not None else ident,
        kind_status,
        datetime.combine(created, datetime.min.time()),
        updated,
        None,
    )


def run(
    rows: list[SprintRow],
    *,
    sizes: dict[int, Size] | None = None,
    day: date = TUESDAY,
    now: datetime | None = None,
    devs: tuple[Dev, ...] = POOL,
    prev: SprintSheet | None = None,
    history: tuple[HistoryOrder, ...] = (),
    bugs: tuple[SprintRow, ...] = (),
    changes: tuple[StatusChange, ...] = (),
    baseline: tuple[OrderMark, ...] | None = None,
) -> list[Risk]:
    sheet = SprintSheet("Sprint 10 (10/6 - 10/17)", 10, START, END, (), tuple(rows), "S10", bugs, changes)
    orders, findings = orders_and_findings(sheet)
    estimates = {o.row.stt: SizeEstimate((sizes or {}).get(o.row.stt, Size.M), "", False) for o in orders}
    result = build_result(
        target=sheet,
        prev=prev,
        prev_name="Sprint 9",
        orders=orders,
        findings=findings,
        devs=devs,
        history=history,
        sizes=estimates,
        sizing_note="",
        run_day=day,
        now=now,
        baseline=baseline,
    )
    return list(result.risks)


def codes(risks: list[Risk], code: str) -> list[Risk]:
    return [risk for risk in risks if risk.code == code]


def history_of(app: str, *people: str) -> HistoryOrder:
    return HistoryOrder("Sprint 8 (9/4 - 9/18)", app, f"{app} 1.0.0", people, None, date(2026, 9, 5))


# Levels and order


def test_escalate_moves_one_step_up_for_urgent_and_high_only_and_never_above_cao() -> None:
    assert escalate(RiskLevel.LOW, Priority.URGENT) is RiskLevel.MEDIUM
    assert escalate(RiskLevel.MEDIUM, Priority.HIGH) is RiskLevel.HIGH
    assert escalate(RiskLevel.HIGH, Priority.URGENT) is RiskLevel.HIGH
    assert escalate(RiskLevel.LOW, Priority.NORMAL) is RiskLevel.LOW


def test_due_to_act_is_the_base_day_for_cao_then_one_and_two_working_days() -> None:
    friday = date(2026, 10, 16)
    assert [due_for(level, friday) for level in RiskLevel] == [friday, date(2026, 10, 19), date(2026, 10, 20)]


def test_the_register_sorts_by_level_then_code_then_order_number() -> None:
    def risk(level: RiskLevel, code: str, where: str) -> Risk:
        return Risk(level, code, None, where, "", "", "", "", None)  # type: ignore[arg-type]

    found = ordered(
        [risk(RiskLevel.LOW, "A", "x"), risk(RiskLevel.HIGH, "B", "Đơn STT 10"), risk(RiskLevel.HIGH, "B", "Đơn STT 9")]
    )

    assert [(r.level, r.where) for r in found] == [
        (RiskLevel.HIGH, "Đơn STT 9"),
        (RiskLevel.HIGH, "Đơn STT 10"),
        (RiskLevel.LOW, "x"),
    ]


# 2, 3, 4: capacity


def test_capacity_dev_fires_above_capacity_and_is_cao_above_one_and_a_half() -> None:
    rows = [
        row(1, people=(LINH,)),
        row(2, people=(LINH,)),
        row(3, people=(MINH,)),
        row(4, people=(AN,), status="qa - testing"),
    ]

    medium = codes(run(rows, sizes={1: Size.M, 2: Size.M, 3: Size.S}), "CAPACITY-DEV")
    high = codes(run(rows, sizes={1: Size.L, 2: Size.M, 3: Size.S}), "CAPACITY-DEV")

    assert [(r.level, r.where) for r in medium] == [(RiskLevel.MEDIUM, "LinhNV")]
    assert medium[0].problem == "LinhNV còn 32h việc (2 đơn), sức chứa còn 24h (4 ngày × 6h)"
    assert medium[0].impact == "Có thể không xong hết đơn trước 17/10/2026."
    assert medium[0].action == "Cân nhắc chuyển STT 2 cho AnTD (còn trống 24h)"  # AnTD's order is in QA: not open
    assert medium[0].covers == (1, 2) and medium[0].due == date(2026, 10, 14)
    assert [r.level for r in high] == [RiskLevel.HIGH]


def test_capacity_counts_only_the_share_of_subtasks_still_with_the_dev() -> None:
    rows = [
        row(1, people=(LINH,)),
        row(2, people=(LINH,)),
        *(
            row(10 + n, people=(LINH,), kind="Subtask", root=1, status="done" if n < 3 else "in progress")
            for n in range(4)
        ),
    ]

    risks = run(rows, sizes={1: Size.L, 2: Size.S})

    assert codes(risks, "CAPACITY-DEV") == []  # 32h × 1/4 + 4h = 12h ≤ 24h


def test_capacity_sprint_proposes_the_not_started_orders_last_in_line() -> None:
    rows = [
        row(1, people=(LINH,)),
        row(2, people=(MINH,), status="ready to progress", priority="low"),
        row(3, people=(AN,), status="ready to progress", priority="urgent", due=date(2026, 10, 16)),
        row(4, people=(TIEN,)),
    ]

    (risk,) = codes(run(rows, sizes={1: Size.XL, 2: Size.L, 3: Size.L, 4: Size.L}), "CAPACITY-SPRINT")

    assert (risk.level, risk.where) == (RiskLevel.HIGH, "Sprint 10 (10/6 - 10/17)")
    assert risk.problem == "Sprint còn 160h việc, sức chứa của team còn 96h"
    assert risk.impact == "Khoảng 64h việc có thể trễ sang sprint sau."
    assert risk.action == "Đề xuất đẩy sang sprint sau: STT 2, 3 (64h), hoặc thêm người ngoài team"
    assert codes(run(rows, sizes={1: Size.M, 2: Size.M, 3: Size.M, 4: Size.M}), "CAPACITY-SPRINT") == []


def test_scope_added_replaces_capacity_sprint_when_the_late_orders_tip_the_sprint_over() -> None:
    rows = [
        row(1, people=(LINH,)),
        row(2, people=(MINH,)),
        row(3, people=(AN,)),
        row(4, people=(TIEN,), status="ready to progress", created=date(2026, 10, 9)),
    ]

    risks = run(rows, sizes={1: Size.L, 2: Size.L, 3: Size.S, 4: Size.L})

    (risk,) = codes(risks, "SCOPE-ADDED")
    assert codes(risks, "CAPACITY-SPRINT") == []
    assert risk.problem == "1 đơn lên sau ngày đầu sprint (STT 4: 32h) làm tải vượt sức chứa (100h > 96h)"
    assert risk.action == "Đề xuất đẩy sang sprint sau: STT 4 (32h)"


def test_carry_over_needs_carry_over_and_an_open_order_and_is_medium_from_three() -> None:
    prev_rows = tuple(
        row(20 + n, people=(LINH,) if n < 3 else (MINH,), status="all issue", kind="Task" if n == 0 else "Subtask")
        for n in range(4)
    )
    prev = SprintSheet("Sprint 9", 9, None, None, (), prev_rows)
    rows = [row(1, people=(LINH,)), row(2, people=(TIEN,))]

    risks = codes(run(rows, prev=prev), "CARRY-OVER")

    assert [(r.where, r.level, r.problem) for r in risks] == [
        ("LinhNV", RiskLevel.MEDIUM, "LinhNV còn 3 việc dở ở Sprint 9")
    ]  # MinhNM has carry-over but no open order


# 5, 6: assignment


def test_pic_unfamiliar_fires_on_an_urgent_order_and_names_who_knows_the_app() -> None:
    history = (history_of("Demo", MINH),)
    urgent = [row(1, people=(TIEN,), priority="urgent", due=END)]

    (risk,) = codes(run(urgent, history=history), "PIC-UNFAMILIAR")
    normal = codes(run([replace(urgent[0], priority_raw="")], history=history), "PIC-UNFAMILIAR")
    new_app = codes(run([replace(urgent[0], app="Other")], history=history), "PIC-UNFAMILIAR")

    assert (risk.level, risk.problem) == (
        RiskLevel.MEDIUM,
        "Đơn STT 1 (urgent) giao cho TiếnBV nhưng TiếnBV chưa làm Demo",
    )
    assert risk.action.startswith(
        "Nhờ MinhNM (Làm version gần nhất của Demo (Sprint 8 (9/4 - 9/18): Demo 1.0.0)) hỗ trợ"
    )
    assert normal == []
    assert new_app[0].action == "App mới với team: tính thêm thời gian tìm hiểu."


def test_pic_absent_fires_when_the_holder_is_off_every_remaining_day_and_suggests_by_section_7() -> None:
    off = replace(
        POOL[3], leave_days=(date(2026, 10, 13), date(2026, 10, 14), date(2026, 10, 15), date(2026, 10, 16), END)
    )
    devs = (*POOL[:3], off)
    rows = [row(1, people=(TIEN,)), row(2, people=(LINH,)), row(3, people=(TIEN,), status="qa - testing")]

    risks = codes(run(rows, devs=devs), "PIC-ABSENT")
    working = codes(run(rows), "PIC-ABSENT")

    assert [(r.where, r.level) for r in risks] == [("Đơn STT 1", RiskLevel.HIGH)]
    assert risks[0].problem == "Đơn STT 1 giao cho TiếnBV nhưng TiếnBV nghỉ các ngày còn lại của sprint (từ 13/10/2026)"
    assert risks[0].action.startswith("Chuyển cho MinhNM: Chưa làm Demo")
    assert working == []


# 7: due dates


def test_due_at_risk_overdue_not_started_and_open_subtasks() -> None:
    rows = [
        row(1, people=(LINH,), due=date(2026, 10, 10)),
        row(2, people=(MINH,), status="ready to progress", due=date(2026, 10, 14)),
        row(3, people=(AN,), status="ready to progress", priority="high", due=date(2026, 10, 15)),
        row(4, people=(TIEN,), due=date(2026, 10, 15)),
        *(row(10 + n, people=(TIEN,), kind="Subtask", root=4, status="in progress" if n else "done") for n in range(3)),
        row(5, people=(LINH,), status="ready to progress", due=date(2026, 10, 20)),
    ]

    risks = {r.where: r for r in codes(run(rows, day=date(2026, 10, 14)), "DUE-AT-RISK")}

    assert (risks["Đơn STT 1"].level, risks["Đơn STT 1"].problem) == (
        RiskLevel.HIGH,
        'Đơn STT 1 quá hạn 10/10/2026 (trạng thái "in progress")',
    )
    assert risks["Đơn STT 2"].level is RiskLevel.HIGH  # 1 day left
    assert (
        risks["Đơn STT 2"].problem == 'Đơn STT 2 còn 1 ngày làm việc tới hạn 14/10/2026 nhưng vẫn "ready to progress"'
    )
    assert risks["Đơn STT 3"].level is RiskLevel.HIGH  # 2 days, Trung bình, + high
    assert risks["Đơn STT 4"].problem == "Đơn STT 4 còn 2 ngày làm việc tới hạn 15/10/2026 mà còn 2/3 subtask chưa xong"
    assert risks["Đơn STT 1"].action.startswith("Hỏi LinhNV lý do; nếu kẹt: chuyển cho ")
    assert "Đơn STT 5" not in risks  # 14–20/10: 5 working days left


def test_due_at_risk_on_a_proposal_asks_to_assign_now() -> None:
    (risk,) = codes(run([row(1, status="ready to progress", due=date(2026, 10, 14))]), "DUE-AT-RISK")

    assert risk.owner == "TM"
    assert risk.action.endswith("; nếu không kịp: lùi hạn hoặc đẩy sang sprint sau.")
    assert risk.action.startswith("Giao ngay cho ")


# 10: stuck


def test_status_stuck_counts_working_days_since_the_last_move_into_the_status() -> None:
    entered = StatusChange("o1", "ready to progress", "in progress", datetime(2026, 10, 7, 9))
    sub = row(10, people=(LINH,), kind="Subtask", root=1, status="ready to qa-testing")
    sub_moved = StatusChange("o10", "in progress", "ready to qa-testing", datetime(2026, 10, 8, 9))
    rows = [row(1, people=(LINH,)), sub]

    (risk,) = codes(run(rows, now=datetime(2026, 10, 13, 9), changes=(entered, sub_moved)), "STATUS-STUCK")

    # the root: Wed 07/10 09:00 to Tue 13/10 09:00 is 4,0 working days, not past 4; the subtask: 3,0 days, past 2
    assert risk.problem == 'Đơn STT 1 có 1 subtask kẹt, lâu nhất "Order 10" ở "ready to qa-testing" 3,0 ngày (ngưỡng 2)'
    assert (risk.level, risk.action, risk.owner) == (RiskLevel.MEDIUM, "Nhắc khâu test nhận đơn.", "TM")


def test_status_stuck_is_compared_as_shown_and_skips_proposals() -> None:
    entered = StatusChange("o1", "", "in progress", datetime(2026, 10, 7, 9))
    exactly_four = codes(
        run([row(1, people=(LINH,))], now=datetime(2026, 10, 13, 9), changes=(entered,)), "STATUS-STUCK"
    )
    later = codes(run([row(1, people=(LINH,))], now=datetime(2026, 10, 13, 12), changes=(entered,)), "STATUS-STUCK")
    proposal = codes(
        run(
            [row(1, status="ready to progress")],
            now=datetime(2026, 10, 13, 12),
            changes=(replace(entered, new="ready to progress"),),
        ),
        "STATUS-STUCK",
    )

    assert exactly_four == []  # 4,0 days is not past the threshold of 4
    assert later[0].problem == 'Đơn STT 1 ở "in progress" 4,1 ngày làm việc (ngưỡng 4)'
    assert later[0].action == "Hỏi LinhNV đang vướng gì." and later[0].owner == "LinhNV"
    assert proposal == []


# 11: QA


def test_qa_returns_counts_returns_bugs_and_open_bugs_near_the_deadline() -> None:
    returns = tuple(StatusChange("o1", "qa - testing", "qa - need fix", datetime(2026, 10, d, 9)) for d in (8, 9))
    bugs = tuple(
        row(
            30 + n,
            kind="Bug",
            root=2,
            status="done" if n < 4 else "in progress",
            kind_status="done" if n < 4 else "custom",
        )
        for n in range(5)
    )
    rows = [
        row(1, people=(LINH,), status="qa - testing", kind_status="custom"),
        row(2, people=(MINH,), status="qa - testing", kind_status="custom", due=date(2026, 10, 14)),
        row(3, people=(AN,), status="done", kind_status="done"),
    ]

    risks = {r.where: r for r in codes(run(rows, changes=returns, bugs=bugs), "QA-RETURNS")}

    assert risks["Đơn STT 1"].problem == 'Đơn STT 1 về "qa - need fix" 2 lần'
    assert risks["Đơn STT 2"].problem == (
        "Đơn STT 2 có 5 bug (1 chưa xong); còn 1 bug mở khi còn 2 ngày làm việc tới hạn 14/10/2026"
    )
    assert "Đơn STT 3" not in risks


# 9: changes


def test_order_changed_compares_with_the_stored_state_and_needs_one() -> None:
    rows = [row(1, people=(LINH,), priority="urgent", due=date(2026, 10, 15), title="1.0.2 - Fix")]
    stored = (OrderMark("o1", "1.0.1 - Fix", "", date(2026, 10, 17), ("LinhNV",)),)

    (risk,) = codes(run(rows, baseline=stored), "ORDER-CHANGED")

    assert risk.level is RiskLevel.MEDIUM  # Thấp + urgent
    assert risk.problem == (
        'Đơn STT 1 đổi ưu tiên trống → urgent; hạn 17/10/2026 → 15/10/2026; tên "1.0.1 - Fix" → "1.0.2 - Fix"'
    )
    assert risk.action == "Báo LinhNV; xem lại độ lớn và hạn."
    assert codes(run(rows), "ORDER-CHANGED") == []


def test_defer_list_stops_once_the_excess_is_covered() -> None:
    risks_input = [
        row(1, people=(LINH,), status="ready to progress"),
        row(2, people=(MINH,), status="ready to progress"),
    ]
    sheet = SprintSheet("S", 10, START, END, (), tuple(risks_input))
    orders, _ = orders_and_findings(sheet)
    items = [
        Assignment(o, SizeEstimate(Size.L, "", False), Source.PREASSIGNED, o.row.assignees, (), "", ()) for o in orders
    ]

    assert [a.order.row.stt for a in defer_list(items, 20)] == [2]
    assert [a.order.row.stt for a in defer_list(items, 40)] == [2, 1]
