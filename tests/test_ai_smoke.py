"""Real AI calls: the sizes of three made-up orders, the questions of one (LLM.md §8).

Opt-in: ASSIGNTOOL_TEST_AI=gemini (or agy) uv run pytest -m ai."""

from __future__ import annotations

import os

import pytest

from scrumbot.ai.prompt import build_prompt, build_question_prompt, parse_questions, parse_reply
from scrumbot.ai.tools import run_ai
from scrumbot.core.model import Order, Priority, SprintRow

TOOL = os.environ.get("ASSIGNTOOL_TEST_AI", "")

pytestmark = [
    pytest.mark.ai,
    pytest.mark.skipif(TOOL not in ("gemini", "agy"), reason="đặt ASSIGNTOOL_TEST_AI=gemini hoặc agy để chạy"),
]

TITLES = ("1.0.1 - Fix crash khi mở app", "2.0.0 - Thêm IAP + đổi luồng onboarding", "1.3.0 - Update policy store")


def _order(stt: int, title: str) -> Order:
    row = SprintRow(stt, title, "Task", "Demo", (), "ready to progress", "normal", None, None, "")
    return Order(row, Priority.NORMAL)


def test_real_ai_sizes_every_order() -> None:
    orders = tuple(_order(stt, title) for stt, title in enumerate(TITLES, start=1))

    reply = run_ai(TOOL, build_prompt(orders, ()), model=None, timeout=600)
    sizes, findings, note = parse_reply(reply, orders)

    assert reply.failure is None, reply.failure
    assert findings == (), findings
    assert sorted(sizes) == [1, 2, 3]
    assert not any(estimate.is_default for estimate in sizes.values()), note


def test_real_ai_answers_the_question_prompt() -> None:
    row = SprintRow(
        1, TITLES[1], "Task", "Demo", (), "", "high", None, None, "Thêm IAP gói tháng và đổi luồng onboarding."
    )

    reply = run_ai(TOOL, build_question_prompt(row), model=None, timeout=600)
    questions = parse_questions(reply)

    assert reply.failure is None, reply.failure
    assert questions.answered, (questions.note, reply.text)
    assert len(questions.items) <= 2
