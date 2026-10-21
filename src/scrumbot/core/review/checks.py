"""The checks of the review (bot spec §7.3, D62, A86–A89): what blocks the filed order. Pure."""

from __future__ import annotations

import re

from scrumbot.core.model import Placement, Priority, SprintRow
from scrumbot.core.normalize import app_key, clean, parse_priority
from scrumbot.core.outcome import ReviewItem

MIN_DESCRIPTION = 30  # characters without links (A88, T1 of A45)
_LINK = re.compile(r"\[link[^\]]*\]")


def blocking(row: SprintRow, how: Placement) -> tuple[ReviewItem, ...]:
    """What the person who filed the order must fix first; empty when the order is ready, or when it already has a
    `Người làm` (A87). `row` is the order as placed: App, priority and `Hạn` from the API for an order on the system,
    the description as the AI reads it (§7.2)."""
    if row.assignees:
        return ()
    on_system = how is not Placement.NEW
    items: list[ReviewItem] = []
    if not app_key(row.app):
        where = "điền App cho đơn trên hệ thống" if on_system else "ghi tên app vào dòng App của file đơn"
        items.append(ReviewItem("REVIEW-APP", f"Thiếu App: {where}."))
    priority = parse_priority(row.priority_raw)
    if row.due is None and priority is not None and priority in (Priority.URGENT, Priority.HIGH):
        where = (
            "điền Hạn cho đơn trên hệ thống" if on_system else "ghi dòng Hạn của file đơn (YYYY-MM-DD hoặc DD/MM/YYYY)"
        )
        items.append(ReviewItem("REVIEW-DUE", f"Đơn {priority.name.lower()} chưa có Hạn: {where}."))
    length = len(clean(_LINK.sub(" ", row.description)))
    if length < MIN_DESCRIPTION:
        items.append(
            ReviewItem(
                "REVIEW-DESC",
                f"Mô tả quá ngắn ({length} ký tự, cần từ {MIN_DESCRIPTION}, không tính link): ghi rõ các hạng mục "
                "cần làm.",
            )
        )
    return tuple(items)
