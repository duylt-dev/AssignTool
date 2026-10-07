from datetime import date

from assigntool.model import HistoryOrder, Level, Priority
from assigntool.rules.familiarity import AppFamiliarity
from assigntool.rules.reasons import PREASSIGNED_REASON, proposed_reason


def test_proposed_reason_joins_all_applicable_parts_in_spec_order() -> None:
    latest = HistoryOrder("Sprint 9", "PS", "Fix ads", (), None, date(2026, 10, 1))

    reason = proposed_reason(
        app="PS",
        familiarity=AppFamiliarity(0, latest, 3),
        level=Level.MIDDLE,
        senior_cause="priority",
        priority=Priority.URGENT,
        load_hours=16,
        load_orders=1,
        carry_over=2,
        prev_name="Sprint 9",
        leave_days=1,
        cap_excluded=(("LinhNV", 32),),
    )

    assert reason == (
        "Làm version gần nhất của PS (Sprint 9: Fix ads) · Đơn urgent → ưu tiên middle trở lên · "
        "Tải sprint này: 16h (1 đơn) · Việc dở Sprint 9: 2 · Nghỉ 1 ngày · "
        "LinhNV quen app hơn nhưng đang có 32h (cân tải)"
    )


def test_proposed_reason_handles_new_empty_and_non_middle_orders() -> None:
    assert PREASSIGNED_REASON == "Đã giao sẵn trong file"
    assert "Đơn không có App Name" in proposed_reason(
        app="",
        familiarity=AppFamiliarity(2, None, 0),
        level=Level.JUNIOR,
        senior_cause="new_app",
        priority=Priority.NORMAL,
        load_hours=0,
        load_orders=0,
        carry_over=0,
        prev_name="Sprint 9",
        leave_days=0,
        cap_excluded=(),
    )
