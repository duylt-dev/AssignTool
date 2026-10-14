"""The review of the order file before the PIC (bot spec §7.3, D62, A86–A89): each code fires on its nearest case and
stays silent on the next one, with the exact Vietnamese message."""

from __future__ import annotations

from datetime import date

import pytest

from scrumbot.model import SprintRow
from scrumbot.rules.new_order import Placement
from scrumbot.rules.review import review

ENOUGH = "Thêm màn cài đặt và sửa luồng mua gói tháng."  # 44 characters


def _row(
    *,
    app: str = "Demo",
    priority: str = "",
    due: date | None = None,
    description: str = ENOUGH,
    assignees: tuple[str, ...] = (),
) -> SprintRow:
    return SprintRow(2, "1.0.2 - Fix", "Task", app, assignees, "", priority, due, date(2026, 10, 13), description, ())


def _codes(row: SprintRow, how: Placement = Placement.NEW) -> list[str]:
    return [item.code for item in review(row, how)]


def test_a_ready_order_has_nothing_to_fix() -> None:
    assert review(_row(), Placement.NEW) == ()


@pytest.mark.parametrize(
    ("how", "message"),
    [
        (Placement.NEW, "Thiếu App: ghi tên app vào dòng App của file đơn."),
        (Placement.BY_ID, "Thiếu App: điền App cho đơn trên hệ thống."),
        (Placement.BY_TITLE, "Thiếu App: điền App cho đơn trên hệ thống."),
    ],
)
def test_review_app_fires_without_an_app_and_says_where_to_fill_it(how: Placement, message: str) -> None:
    (item,) = review(_row(app="  "), how)

    assert (item.code, item.message) == ("REVIEW-APP", message)


@pytest.mark.parametrize(
    ("how", "message"),
    [
        (Placement.NEW, "Đơn high chưa có Hạn: ghi dòng Hạn của file đơn (YYYY-MM-DD hoặc DD/MM/YYYY)."),
        (Placement.BY_ID, "Đơn high chưa có Hạn: điền Hạn cho đơn trên hệ thống."),
    ],
)
def test_review_due_fires_for_a_high_order_without_a_due_date(how: Placement, message: str) -> None:
    (item,) = review(_row(priority="High"), how)

    assert (item.code, item.message) == ("REVIEW-DUE", message)


@pytest.mark.parametrize(
    ("priority", "due"),
    [("urgent", date(2026, 10, 16)), ("normal", None), ("", None), ("low", None), ("không rõ", None)],
)
def test_review_due_is_silent_with_a_due_date_or_below_high(priority: str, due: date | None) -> None:
    assert _codes(_row(priority=priority, due=due)) == []


def test_review_desc_fires_below_30_characters_without_links() -> None:
    linked = "Xem [link Figma] và [link Google Docs] nhé"  # "Xem và nhé": 10 characters once the links are gone

    (item,) = review(_row(description=linked), Placement.NEW)

    assert (item.code, item.message) == (
        "REVIEW-DESC",
        "Mô tả quá ngắn (10 ký tự, cần từ 30, không tính link): ghi rõ các hạng mục cần làm.",
    )
    assert _codes(_row(description="")) == ["REVIEW-DESC"]


def test_review_desc_is_silent_from_30_characters_and_counts_collapsed_spaces() -> None:
    assert _codes(_row(description="x" * 30)) == []
    assert _codes(_row(description="x" * 29 + "     ")) == ["REVIEW-DESC"]
    assert _codes(_row(description="[người] làm màn cài đặt mới cho app")) == []


def test_every_check_is_listed_in_order() -> None:
    row = _row(app="", priority="urgent", description="Sửa lỗi.")

    assert _codes(row) == ["REVIEW-APP", "REVIEW-DUE", "REVIEW-DESC"]


def test_an_order_that_already_has_a_person_is_not_reviewed() -> None:
    """A87: the order is kept as it is (D10), so nothing blocks it."""
    row = _row(app="", priority="urgent", description="", assignees=("Ngọc Văn Linh",))

    assert review(row, Placement.BY_ID) == ()
