"""The fixed checks of the review (bot spec §7.3, D62, D65, A86–A89, A108): what blocks the filed order before any AI
call. Pure."""

from __future__ import annotations

import re

from scrumbot.core.model import Placement, Priority, SprintRow
from scrumbot.core.normalize import app_key, clean, parse_priority
from scrumbot.core.outcome import ReviewItem

MIN_DESCRIPTION = 30  # characters without links (A88, T1 of A45)
ACCEPTANCE = "nghiệm thu khi"  # the part every description needs (A108)
_LINK = re.compile(r"\[link[^\]]*\]")
_VERSION = re.compile(r"(?<![\w.])[vV]?\d+(?:\.\d+)+")  # 1.0.3, v1.0.3
_URGENT = (Priority.URGENT, Priority.HIGH)  # Khẩn cấp in the process: p0 and p1 (A108)


def blocking(row: SprintRow, how: Placement, *, owner: str, evidence: str) -> tuple[ReviewItem, ...]:
    """What the person who filed the order must fix first; empty when the order is ready, or when it already has a
    `Người làm` (A87). `row` is the order as placed: title, App, priority and `Hạn` from the API for an order on the
    system, the description as the AI reads it (§7.2); `owner` and `evidence` always come from the file."""
    if row.assignees:
        return ()
    on_system = how is not Placement.NEW
    items: list[ReviewItem] = []
    if not app_key(row.app):
        where = "điền App cho đơn trên hệ thống" if on_system else "ghi tên app vào dòng App của file đơn"
        items.append(ReviewItem("REVIEW-APP", f"Thiếu App: {where}."))
    if not _VERSION.search(row.title):
        where = (
            "sửa tiêu đề đơn trên hệ thống theo mẫu App + version + việc cần làm"
            if on_system
            else "ghi dòng # của file đơn theo mẫu App + version + việc cần làm, vd App A v1.0.3 – Gắn interstitial ở "
            "màn Spin"
        )
        items.append(ReviewItem("REVIEW-TITLE", f"Tiêu đề chưa có version: {where}."))
    if row.due is None:
        where = (
            "điền Hạn cho đơn trên hệ thống" if on_system else "ghi dòng Hạn của file đơn (YYYY-MM-DD hoặc DD/MM/YYYY)"
        )
        items.append(ReviewItem("REVIEW-DUE", f"Đơn chưa có Hạn: {where}."))
    if not clean(owner):
        items.append(
            ReviewItem(
                "REVIEW-OWNER",
                "Thiếu người chịu trách nhiệm: ghi dòng Người chịu trách nhiệm của file đơn (người trả lời Dev về "
                "đơn).",
            )
        )
    priority = parse_priority(row.priority_raw)
    if priority is not None and priority in _URGENT and not clean(evidence):
        lower = "hạ Ưu tiên của đơn trên hệ thống về normal" if on_system else "hạ Ưu tiên về normal"
        items.append(
            ReviewItem(
                "REVIEW-EVIDENCE",
                f"Đơn {priority.name.lower()} là đơn Khẩn cấp nhưng chưa có Bằng chứng: ghi dòng Bằng chứng của file "
                f"đơn (ảnh dashboard, email store/đối tác, số liệu KPI), hoặc {lower}.",
            )
        )
    length = len(clean(_LINK.sub(" ", row.description)))
    if length < MIN_DESCRIPTION:
        items.append(
            ReviewItem(
                "REVIEW-DESC",
                f"Mô tả quá ngắn ({length} ký tự, cần từ {MIN_DESCRIPTION}, không tính link): ghi rõ các hạng mục "
                "cần làm.",
            )
        )
    if ACCEPTANCE not in clean(row.description).casefold():
        items.append(
            ReviewItem(
                "REVIEW-ACCEPT",
                'Mô tả chưa có mục "Nghiệm thu khi": ghi các điều kiện kiểm tra được, đủ để tester viết test case.',
            )
        )
    return tuple(items)
