"""Real AI calls: the sizes of three made-up orders, the review of one (LLM.md §8).

Opt-in: ASSIGNTOOL_TEST_AI=gemini (or agy) uv run pytest -m ai."""

from __future__ import annotations

import os

import pytest

from scrumbot.ai.prompt import build_prompt, build_review_prompt, parse_reply, parse_review
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


def test_real_ai_names_the_type_and_the_missing_points_of_an_incomplete_order() -> None:
    """An IAP order with the package and the acceptance only: no paywall, no Remote Config, no events (D65)."""
    description = (
        "Thêm gói monthly_pro: subscription 1 tháng, không trial. "
        "Nghiệm thu khi: mua sandbox thành công thì mở Premium."
    )
    row = SprintRow(1, "Demo v2.0.0 - Thêm gói tháng", "Task", "Demo", (), "", "normal", None, None, description)

    reply = run_ai(TOOL, build_review_prompt(row, None), model=None, timeout=600)
    found = parse_review(reply, None)

    assert reply.failure is None, reply.failure
    assert found.answered and found.checked, (found.note, reply.text)
    assert found.kind == "iap", reply.text
    assert found.missing, reply.text
    assert len(found.questions) <= 2
