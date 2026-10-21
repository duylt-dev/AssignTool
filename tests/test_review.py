"""The review of the order file before the PIC (bot spec §7.3, D62, D65, A86–A89, A106–A108): each code fires on its
nearest case and stays silent on the next one, with the exact Vietnamese message."""

from __future__ import annotations

from datetime import date

import pytest

from scrumbot.core.model import OrderKind, Placement, SprintRow
from scrumbot.core.outcome import AiReview
from scrumbot.core.review.checks import blocking
from scrumbot.core.review.templates import TEMPLATES, settled, template_item

ENOUGH = "Thêm màn cài đặt và sửa luồng mua gói tháng. Nghiệm thu khi: mua được gói tháng."
DUE = date(2026, 10, 16)


def _row(
    *,
    title: str = "Demo v1.0.2 - Thêm màn cài đặt",
    app: str = "Demo",
    priority: str = "",
    due: date | None = DUE,
    description: str = ENOUGH,
    assignees: tuple[str, ...] = (),
) -> SprintRow:
    return SprintRow(2, title, "Task", app, assignees, "", priority, due, date(2026, 10, 13), description)


def _items(row: SprintRow, how: Placement = Placement.NEW, *, owner: str = "TaiDT – BA", evidence: str = ""):
    return blocking(row, how, owner=owner, evidence=evidence)


def _codes(row: SprintRow, how: Placement = Placement.NEW, **fields: str) -> list[str]:
    return [item.code for item in _items(row, how, **fields)]


def test_a_ready_order_has_nothing_to_fix() -> None:
    assert _items(_row()) == ()


@pytest.mark.parametrize(
    ("how", "message"),
    [
        (Placement.NEW, "Thiếu App: ghi tên app vào dòng App của file đơn."),
        (Placement.BY_ID, "Thiếu App: điền App cho đơn trên hệ thống."),
        (Placement.BY_TITLE, "Thiếu App: điền App cho đơn trên hệ thống."),
    ],
)
def test_review_app_fires_without_an_app_and_says_where_to_fill_it(how: Placement, message: str) -> None:
    (item,) = _items(_row(app="  "), how)

    assert (item.code, item.message) == ("REVIEW-APP", message)


@pytest.mark.parametrize(
    ("how", "message"),
    [
        (
            Placement.NEW,
            "Tiêu đề chưa có version: ghi dòng # của file đơn theo mẫu App + version + việc cần làm, vd App A "
            "v1.0.3 – Gắn interstitial ở màn Spin.",
        ),
        (
            Placement.BY_TITLE,
            "Tiêu đề chưa có version: sửa tiêu đề đơn trên hệ thống theo mẫu App + version + việc cần làm.",
        ),
    ],
)
def test_review_title_fires_for_a_title_without_a_version(how: Placement, message: str) -> None:
    (item,) = _items(_row(title="Game Emulator - Chỉnh sửa luồng auto scan game"), how)

    assert (item.code, item.message) == ("REVIEW-TITLE", message)


@pytest.mark.parametrize(
    "title",
    ["1.0.2 - Fix", "App A v1.0.3 – Gắn interstitial", "Demo V2.10 sửa crash", "Sửa crash (2.3.1)", "Bản 1.0"],
)
def test_review_title_is_silent_with_a_version(title: str) -> None:
    assert _codes(_row(title=title)) == []


@pytest.mark.parametrize("title", ["App A 2026 - Sửa crash", "Version mới", "App1.0 sửa", "Sửa v2"])
def test_review_title_needs_digits_joined_by_dots_after_a_space(title: str) -> None:
    assert _codes(_row(title=title)) == ["REVIEW-TITLE"]


@pytest.mark.parametrize(
    ("how", "message"),
    [
        (Placement.NEW, "Đơn chưa có Hạn: ghi dòng Hạn của file đơn (YYYY-MM-DD hoặc DD/MM/YYYY)."),
        (Placement.BY_ID, "Đơn chưa có Hạn: điền Hạn cho đơn trên hệ thống."),
    ],
)
def test_review_due_fires_for_every_order_without_a_due_date(how: Placement, message: str) -> None:
    """D65: not only urgent and high orders."""
    (item,) = _items(_row(due=None), how)

    assert (item.code, item.message) == ("REVIEW-DUE", message)
    assert _codes(_row(due=None, priority="low")) == ["REVIEW-DUE"]


def test_review_owner_fires_without_the_line_of_the_file() -> None:
    (item,) = _items(_row(), Placement.BY_ID, owner="  ")

    assert (item.code, item.message) == (
        "REVIEW-OWNER",
        "Thiếu người chịu trách nhiệm: ghi dòng Người chịu trách nhiệm của file đơn (người trả lời Dev về đơn).",
    )
    assert _codes(_row(), owner="[Tên] – MO") == []


@pytest.mark.parametrize(
    ("priority", "how", "message"),
    [
        (
            "urgent",
            Placement.NEW,
            "Đơn urgent là đơn Khẩn cấp nhưng chưa có Bằng chứng: ghi dòng Bằng chứng của file đơn (ảnh dashboard, "
            "email store/đối tác, số liệu KPI), hoặc hạ Ưu tiên về normal.",
        ),
        (
            "High",
            Placement.BY_ID,
            "Đơn high là đơn Khẩn cấp nhưng chưa có Bằng chứng: ghi dòng Bằng chứng của file đơn (ảnh dashboard, "
            "email store/đối tác, số liệu KPI), hoặc hạ Ưu tiên của đơn trên hệ thống về normal.",
        ),
    ],
)
def test_review_evidence_fires_for_an_urgent_or_high_order_without_evidence(
    priority: str, how: Placement, message: str
) -> None:
    (item,) = _items(_row(priority=priority), how)

    assert (item.code, item.message) == ("REVIEW-EVIDENCE", message)


@pytest.mark.parametrize(
    ("priority", "evidence"),
    [("urgent", "Ảnh dashboard Crashlytics"), ("high", "email Google Play"), ("normal", ""), ("low", ""), ("?", "")],
)
def test_review_evidence_is_silent_with_evidence_or_below_high(priority: str, evidence: str) -> None:
    assert _codes(_row(priority=priority), evidence=evidence) == []


def test_review_desc_fires_below_30_characters_without_links() -> None:
    linked = "Xem [link Figma] và [link Google Docs] nhé"  # "Xem và nhé": 10 characters once the links are gone

    items = _items(_row(description=linked))

    assert (items[0].code, items[0].message) == (
        "REVIEW-DESC",
        "Mô tả quá ngắn (10 ký tự, cần từ 30, không tính link): ghi rõ các hạng mục cần làm.",
    )
    assert _codes(_row(description="")) == ["REVIEW-DESC", "REVIEW-ACCEPT"]


def test_review_desc_is_silent_from_30_characters_and_counts_collapsed_spaces() -> None:
    assert _codes(_row(description="Nghiệm thu khi: " + "x" * 14)) == []
    assert _codes(_row(description="Nghiệm thu khi: " + "x" * 13 + "     ")) == ["REVIEW-DESC"]
    assert _codes(_row(description="[người] làm màn cài đặt mới. Nghiệm thu khi: có màn")) == []


def test_review_accept_fires_without_the_acceptance_part() -> None:
    items = _items(_row(description="Thêm màn cài đặt và sửa luồng mua gói tháng cho người dùng."))

    assert [(item.code, item.message) for item in items] == [
        (
            "REVIEW-ACCEPT",
            'Mô tả chưa có mục "Nghiệm thu khi": ghi các điều kiện kiểm tra được, đủ để tester viết test case.',
        )
    ]


@pytest.mark.parametrize("acceptance", ["Nghiệm thu khi:", "NGHIỆM THU KHI", "nghiệm   thu khi"])
def test_review_accept_is_silent_in_any_case_and_spacing(acceptance: str) -> None:
    assert _codes(_row(description=f"Thêm màn cài đặt và luồng mua gói. {acceptance} mua được gói.")) == []


def test_every_check_is_listed_in_order() -> None:
    row = _row(title="Sửa lỗi", app="", priority="urgent", due=None, description="Sửa lỗi.")

    assert _codes(row, owner="") == [
        "REVIEW-APP",
        "REVIEW-TITLE",
        "REVIEW-DUE",
        "REVIEW-OWNER",
        "REVIEW-EVIDENCE",
        "REVIEW-DESC",
        "REVIEW-ACCEPT",
    ]


def test_an_order_that_already_has_a_person_is_not_reviewed() -> None:
    """A87: the order is kept as it is (D10), so nothing blocks it."""
    row = _row(title="Sửa lỗi", app="", priority="urgent", due=None, description="", assignees=("Ngọc Văn Linh",))

    assert _items(row, Placement.BY_ID, owner="") == ()


def test_every_template_holds_the_points_of_the_process_without_its_documents_point() -> None:
    """A106: 8 types; the `Tài liệu: …` point of each template is not checked."""
    assert set(TEMPLATES) == set(OrderKind)
    assert [len(points) for points in TEMPLATES.values()] == [5, 5, 5, 6, 4, 5, 5, 5]
    assert not any(point.startswith("Tài liệu") for points in TEMPLATES.values() for point in points)


def test_review_template_fires_with_the_template_s_own_words_in_its_order() -> None:
    ai = settled(None, AiReview("iap", True, (4, 2, 2, 9, 0), ("Gói nào?",), True, "AI (agy)"))

    item = template_item(ai)

    assert item is not None
    assert (item.code, item.message) == (
        "REVIEW-TEMPLATE",
        "Mô tả chưa đủ ý của mẫu IAP (AI chấm): Paywall: màn nào, điều kiện hiển thị; Event tracking IAP cần bắn.",
    )


def test_the_file_s_type_wins_over_the_ai_s() -> None:
    ai = settled(OrderKind.BUGFIX, AiReview("other", True, (3,), (), True, "AI (agy)"))

    assert ai.kind == "bugfix"
    item = template_item(ai)
    assert item is not None and item.message == (
        "Mô tả chưa đủ ý của mẫu Fix bug / crash (AI chấm): Bước tái hiện, kết quả thực tế và mong đợi."
    )


@pytest.mark.parametrize(
    ("declared", "ai"),
    [
        (None, AiReview("feature", True, (), (), True, "AI (agy)")),  # every point covered
        (None, AiReview("feature", True, (7, 0), (), True, "AI (agy)")),  # no number inside the template
        (None, AiReview("feature", False, (1,), (), True, "AI (agy)")),  # no list of points in the reply
        (None, AiReview("other", True, (1,), (), True, "AI (agy)")),  # outside the 8 types
        (None, AiReview("", True, (1,), (), True, "AI (agy)")),  # an unknown type
        (OrderKind.ADS, AiReview(note="tắt AI")),  # the AI off
    ],
)
def test_review_template_is_silent_without_a_point_to_name(declared: OrderKind | None, ai: AiReview) -> None:
    assert template_item(settled(declared, ai)) is None


def test_settled_keeps_other_and_never_checks_an_unknown_type() -> None:
    assert settled(None, AiReview("other", True)) == AiReview("other", False)
    assert settled(None, AiReview("", True)) == AiReview("", False)
    assert settled(OrderKind.ADS, AiReview(note="tắt AI")) == AiReview("ads", note="tắt AI")
