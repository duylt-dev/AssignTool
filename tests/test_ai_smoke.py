"""One real AI call on the sample (LLM.md §8). Opt-in: ASSIGNTOOL_TEST_AI=gemini (or agy) uv run pytest -m ai."""

from __future__ import annotations

import os

import pytest

from assigntool.ai_cli import run_ai
from assigntool.rules.sizing import build_prompt, parse_reply
from assigntool.rules.validate import orders_and_findings
from assigntool.sprint_reader import read_workbook
from tests.sample import SAMPLE, SKIP_REASON, history_orders

TOOL = os.environ.get("ASSIGNTOOL_TEST_AI", "")

pytestmark = [
    pytest.mark.ai,
    pytest.mark.skipif(TOOL not in ("gemini", "agy"), reason="đặt ASSIGNTOOL_TEST_AI=gemini hoặc agy để chạy"),
    pytest.mark.skipif(not SAMPLE.is_file(), reason=SKIP_REASON),
]


def test_real_ai_sizes_every_order_of_the_sample() -> None:
    target, previous, _ = read_workbook(SAMPLE)
    orders, _ = orders_and_findings(target)
    prompt = build_prompt(orders, history_orders(previous))

    reply = run_ai(TOOL, prompt, model=None, timeout=600)  # agy took 117–360 s per sprint prompt (2026-10-08)
    sizes, findings, note = parse_reply(reply, orders)

    assert reply.failure is None, reply.failure
    assert findings == (), findings
    assert sorted(sizes) == [1, 7, 10, 14, 18, 24]
    assert not any(estimate.is_default for estimate in sizes.values()), note
