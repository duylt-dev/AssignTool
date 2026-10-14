from __future__ import annotations

from datetime import date, timedelta

from scrumbot.model import AiReply, HistoryOrder, Order, Priority, Size, SprintRow
from scrumbot.understanding.sizing import MAX_EXAMPLES, PROMPT_BUDGET, build_prompt, default_sizes, parse_reply


def _order(
    stt: int,
    *,
    app: str = "Camera",
    title: str = "Fix crash",
    description: str = "",
    assignees: tuple[str, ...] = (),
) -> Order:
    row = SprintRow(stt, title, "Task", app, assignees, "", "high", None, None, description, ())
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
        '  "type": "<type>", "items": ["<item>"], "tech_risks": ["<risk>"], "questions": ["<question>"]}]\n'
    )
    assert "its type (ads, iap, flow_ui, policy, crash, sdk, feature or other)" in prompt
    assert "also give at most 2 short questions in Vietnamese to the person who filed it" in prompt
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


def test_parse_reply_keeps_at_most_two_questions_and_a_wrong_key_never_changes_the_size() -> None:
    """A90: questions to the person who filed the order; bad values are dropped, the size stays."""
    orders = (_order(1), _order(2))
    long = "Có " + "x" * 300
    reply = AiReply(
        "agy",
        '[{"stt": 1, "size": "M", "reason": "r", "questions": ["Màn nào?", "", "' + long + '", "Thừa?"]},'
        ' {"stt": 2, "size": "S", "questions": "not a list"}]',
        None,
    )

    sizes, findings, _ = parse_reply(reply, orders)

    assert findings == ()
    assert sizes[1].questions == ("Màn nào?", long[:200])
    assert (sizes[2].size, sizes[2].questions) == (Size.S, ())
