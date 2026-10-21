from __future__ import annotations

import json
from datetime import date, timedelta

import pytest

from scrumbot.ai.prompt import (
    MAX_EXAMPLES,
    PROMPT_BUDGET,
    QUESTION_DESC_LIMIT,
    AiReply,
    build_prompt,
    build_review_prompt,
    default_sizes,
    parse_reply,
    parse_review,
)
from scrumbot.core.model import ORDER_KINDS, HistoryOrder, Order, OrderKind, Priority, Size, SprintRow
from scrumbot.core.outcome import AiReview


def _order(
    stt: int,
    *,
    app: str = "Camera",
    title: str = "Fix crash",
    description: str = "",
    assignees: tuple[str, ...] = (),
) -> Order:
    row = SprintRow(stt, title, "Task", app, assignees, "", "high", None, None, description)
    return Order(row, Priority.HIGH)


def _history(
    title: str, *, app: str = "Camera", hours: float | None = 4, day: int = 1, people: tuple[str, ...] = ()
) -> HistoryOrder:
    return HistoryOrder("Sprint 9", app, title, people, hours, date(2026, 1, 1) + timedelta(days=day))


def test_build_prompt_has_exact_headers_removes_urls_and_never_includes_people() -> None:
    prompt = build_prompt(
        (_order(7, description="  See https://internal.example/a?q=1 please ", assignees=("Nguyen Van A",)),),
        (_history("Previous", people=("Tran Thi B",)),),
    )

    assert prompt.startswith("You estimate the size of change orders for an Android app team.\n")
    assert "An order is one release (version) of one app" in prompt
    assert "Past orders of this team with the hours they took (for calibration):\n- Camera · Previous · 4h" in prompt
    assert "Orders to size:\n- STT 7 · Camera · high · Fix crash · See [link] please" in prompt
    assert prompt.endswith(
        '[{"stt": <STT number>, "size": "S|M|L|XL", "reason": "<at most 20 words, in Vietnamese>",\n'
        '  "type": "<type>", "items": ["<item>"], "tech_risks": ["<risk>"]}]\n'
    )
    assert "its type (ads, iap, flow_ui, policy, crash, sdk, feature or other)" in prompt
    assert "question" not in prompt  # the questions are the review's own call (A102)
    assert "Nguyen Van A" not in prompt
    assert "Tran Thi B" not in prompt
    assert "https://" not in prompt


def test_build_prompt_orders_examples_by_target_app_then_recency_and_caps_them() -> None:
    history = tuple(
        _history(f"Old {index}", app="Other", day=1) if index == 0 else _history(f"Camera {index}", day=index)
        for index in range(1, MAX_EXAMPLES + 5)
    ) + (_history("Other", app="Other", day=2), _history("No hours", hours=0, day=3))

    prompt = build_prompt((_order(1),), history)
    examples = (
        prompt.split("Past orders of this team with the hours they took (for calibration):\n", 1)[1]
        .split("\n\nOrders to size:", 1)[0]
        .splitlines()
    )

    assert len(examples) == MAX_EXAMPLES
    assert examples[0] == "- Camera · Camera 34 · 4h"
    assert examples[-1] == "- Camera · Camera 5 · 4h"


def test_build_prompt_uses_empty_list_lines_and_desc_budget_fallbacks() -> None:
    assert "- (none)\n\nOrders to size:\n- (none)" in build_prompt((), ())

    many = tuple(_order(index, description="x" * 600) for index in range(60))
    prompt = build_prompt(many, ())
    assert len(prompt) <= PROMPT_BUDGET
    assert " · " + "x" * 200 in prompt
    assert " · " + "x" * 201 not in prompt

    oversized = build_prompt((_order(1, title="t" * (PROMPT_BUDGET + 1), description="visible"),), ())
    assert " · visible" not in oversized


def test_default_sizes_marks_every_order_as_default_m() -> None:
    sizes = default_sizes((_order(3), _order(8)))

    assert {stt: (estimate.size, estimate.reason, estimate.is_default) for stt, estimate in sizes.items()} == {
        3: (Size.M, "", True),
        8: (Size.M, "", True),
    }


def test_parse_reply_accepts_valid_items_and_cleans_and_cuts_reason() -> None:
    reply = AiReply(
        "gemini",
        'extra [{"stt": "3", "size": " xl ", "reason": "  Lý   do  "}, {"stt": 8, "size": "S", "reason": "x"}] end',
        None,
    )

    sizes, findings, note = parse_reply(reply, (_order(3), _order(8)))

    assert sizes[3].size is Size.XL
    assert sizes[3].reason == "Lý do"
    assert sizes[8].size is Size.S
    assert not findings
    assert note == "AI (gemini, 2/2 đơn)"


def test_parse_reply_fails_for_explicit_failure_or_unreadable_array() -> None:
    for reply, reason in (
        (AiReply("agy", None, "hết thời gian 180s"), "hết thời gian 180s"),
        (AiReply("agy", "```json\nnot an array\n```", None), "không đọc được mảng JSON trong trả lời"),
    ):
        sizes, findings, note = parse_reply(reply, (_order(1),))

        assert sizes[1].size is Size.M and sizes[1].is_default
        assert findings[0].code == "SIZE-AI-FAILED"
        assert findings[0].where == "agy"
        assert findings[0].message == f"Không ước lượng được độ lớn bằng AI ({reason}); mọi đơn tính là M (16h)."
        assert note == f"mặc định M ({reason})"


def test_parse_reply_ignores_invalid_duplicate_and_unknown_items() -> None:
    reply = AiReply(
        "gemini",
        '[{"stt": 1, "size": "S"}, {"stt": 1, "size": "L"}, {"stt": 2, "size": "bad"}, {"stt": 9, "size": "S"}]',
        None,
    )

    sizes, findings, note = parse_reply(reply, (_order(1), _order(2), _order(3)))

    assert all(sizes[stt].size is Size.M and sizes[stt].is_default for stt in (1, 2, 3))
    assert findings[0].code == "SIZE-AI-INVALID"
    assert findings[0].message == "AI không trả độ lớn hợp lệ cho đơn STT 1,2,3; các đơn này tính là M (16h)."
    assert note == "AI (gemini, 0/3 đơn)"


def test_parse_reply_accepts_fenced_array_and_limits_reason() -> None:
    reply = AiReply("agy", '```json\n[{"stt": 1, "size": "L", "reason": "' + "a" * 140 + '"}]\n```', None)

    sizes, findings, note = parse_reply(reply, (_order(1),))

    assert sizes[1].size is Size.L
    assert len(sizes[1].reason) == 120
    assert not findings
    assert note == "AI (agy, 1/1 đơn)"


def test_parse_reply_reads_the_understanding_fields_and_never_lets_them_change_the_size() -> None:
    orders = (_order(1), _order(2), _order(3))
    reply = AiReply(
        "agy",
        '[{"stt": 1, "size": "L", "reason": "r", "type": "IAP", "items": ["Add IAP", " ", 3], '
        '"tech_risks": ["SDK mới", "hạn store", "thừa"]},'
        ' {"stt": 2, "size": "S", "type": "unknown", "items": "not a list", "tech_risks": null},'
        ' {"stt": 3, "size": "XL"}]',
        None,
    )

    sizes, findings, _ = parse_reply(reply, orders)

    assert findings == ()
    assert (sizes[1].size, sizes[1].kind, sizes[1].items, sizes[1].tech_risks) == (
        Size.L,
        "iap",
        ("Add IAP",),
        ("SDK mới", "hạn store"),
    )
    assert (sizes[2].size, sizes[2].kind, sizes[2].items, sizes[2].tech_risks) == (Size.S, "", (), ())
    assert (sizes[3].size, sizes[3].kind) == (Size.XL, "")


def test_parse_reply_ignores_a_questions_key() -> None:
    """D64: the sizing reply has no questions; an extra key never changes the size."""
    reply = AiReply("agy", '[{"stt": 1, "size": "S", "reason": "r", "questions": ["Màn nào?"]}]', None)

    sizes, findings, _ = parse_reply(reply, (_order(1),))

    assert (findings, sizes[1].size) == ((), Size.S)


REVIEW_REPLY = (
    'Reply with only a JSON object, no prose and no code fence:\n{"type": "<type>", "missing": [<point number>], '
    '"questions": ["<question>"]}\n'
)


def _filed(description: str = "Gói tháng https://x.io/a [người]") -> SprintRow:
    return SprintRow(3, "1.0.2 - Add IAP", "Task", "Demo", (), "", "high", None, None, description)


def test_the_review_prompt_holds_the_filed_order_alone_and_every_template_without_links() -> None:
    prompt = build_review_prompt(_filed(), None)

    assert prompt.startswith("You review a change order of an Android app team before it is assigned to a developer.\n")
    assert "The order:\n- Demo · high · 1.0.2 - Add IAP\n- Description: Gói tháng [link] [người]\n" in prompt
    assert "The team's process has 8 order types; the description of each must cover the points of its template:\n" in (
        prompt
    )
    for kind in OrderKind:
        assert f"\n- {kind.value} ({ORDER_KINDS[kind]}): 1. " in prompt
    iap = "- iap (IAP): 1. Danh sách gói: product ID, loại (subscription / mua một lần), chu kỳ, trial; 2. Paywall"
    assert iap in prompt
    assert 'or "other" when none fits (for example a new app, which follows its own SRS)' in prompt
    assert "Tài liệu:" not in prompt  # the documents point is not checked (A106)
    assert prompt.endswith(REVIEW_REPLY)
    assert "https://" not in prompt and "STT" not in prompt


def test_the_review_prompt_gives_only_the_template_of_the_file_s_type() -> None:
    prompt = build_review_prompt(_filed(), OrderKind.BUGFIX)

    assert (
        "The order's type is bugfix (Fix bug / crash); its description must cover the points of this template:\n"
        "1. Tên lỗi, mã lỗi và link lỗi cho từng lỗi\n2. Version app, build; thiết bị, OS nếu biết\n"
        "3. Bước tái hiện, kết quả thực tế và mong đợi\n4. Ảnh, video hoặc log (nếu có)\n"
        'Give "type": "bugfix". In "missing", list the numbers of the points the description does not cover'
    ) in prompt
    assert "8 order types" not in prompt and "Quảng cáo" not in prompt
    assert prompt.endswith(REVIEW_REPLY)


def test_the_review_prompt_cuts_the_description_and_names_what_is_missing() -> None:
    row = SprintRow(3, "Fix", "Task", "", (), "", "", None, None, "x" * (QUESTION_DESC_LIMIT + 50))

    prompt = build_review_prompt(row, None)

    assert f"- (không có app) · (không có ưu tiên) · Fix\n- Description: {'x' * QUESTION_DESC_LIMIT}\n" in prompt
    empty = build_review_prompt(SprintRow(3, "Fix", "Task", "Demo", (), "", "low", None, None, ""), None)
    assert "- Description: (không có)\n" in empty


def test_parse_review_reads_the_type_the_point_numbers_and_at_most_two_questions() -> None:
    long = "Có " + "x" * 300
    reply = {"type": " Feature ", "missing": [3, "1", 3, True, "a"], "questions": ["Màn nào?", "", long, "?"]}
    text = json.dumps(reply, ensure_ascii=False)

    found = parse_review(AiReply("agy", f"```json\n{text}\n```", None), None)

    assert found == AiReview("feature", True, (1, 3), ("Màn nào?", long[:200]), True, "AI (agy)")


def test_parse_review_checks_against_the_file_s_type_whatever_type_the_ai_names() -> None:
    found = parse_review(AiReply("agy", '{"type": "other", "missing": [2], "questions": []}', None), OrderKind.ADS)

    assert found == AiReview("other", True, (2,), (), True, "AI (agy)")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('{"type": "other", "missing": [], "questions": []}', AiReview("other", False, (), (), True, "AI (agy)")),
        ('{"type": "game", "missing": [1], "questions": []}', AiReview("", False, (1,), (), True, "AI (agy)")),
        ('{"type": "ads", "missing": "1", "questions": []}', AiReview("ads", False, (), (), True, "AI (agy)")),
        (
            '{"type": "ads", "missing": [], "questions": "Màn nào?"}',
            AiReview("ads", True, (), (), False, "không đọc được câu hỏi trong trả lời của AI"),
        ),
    ],
)
def test_parse_review_checks_nothing_without_a_known_type_or_a_list_of_points(text: str, expected: AiReview) -> None:
    assert parse_review(AiReply("agy", text, None), None) == expected


@pytest.mark.parametrize(
    ("reply", "note"),
    [
        (AiReply("agy", None, "agy hết thời gian chờ"), "agy hết thời gian chờ"),
        (AiReply("agy", "không có JSON", None), "không đọc được trả lời của AI"),
    ],
)
def test_parse_review_gives_nothing_on_a_failure_or_another_form(reply: AiReply, note: str) -> None:
    assert parse_review(reply, OrderKind.IAP) == AiReview(note=note)
