"""Today's sizer (bot spec §2.6, §8.5) with a canned `ask` and a real memory file: what is asked, what is remembered,
and the sizing note."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from scrumbot.ai.memory import AnswerMemory
from scrumbot.ai.prompt import AiReply
from scrumbot.ai.sizer import AiSizer
from scrumbot.core.model import Order, Priority, Size, SprintRow

NOW = datetime(2026, 10, 14, 9)


def _order(stt: int, order_id: str, title: str) -> Order:
    return Order(SprintRow(stt, title, "Task", "Demo", (), "", "", None, None, "", id=order_id), Priority.NORMAL)


ORDERS = (_order(1, "a", "Demo 1.0.0"), _order(2, "b", "Demo 1.0.1"), _order(3, "", "Demo 1.0.2"))


class Ask:
    """Answers L for every `- STT n` line of the prompt, or fails."""

    def __init__(self, failure: str | None = None) -> None:
        self.asked: list[list[int]] = []
        self.failure = failure

    def __call__(self, prompt: str) -> AiReply:
        stts = [int(found) for found in re.findall(r"^- STT (\d+) ·", prompt, flags=re.M)]
        self.asked.append(stts)
        if self.failure:
            return AiReply("thử", None, self.failure)
        return AiReply("thử", json.dumps([{"stt": stt, "size": "L", "reason": "lớn"} for stt in stts]), None)


def test_the_first_call_asks_every_order_and_remembers_all_but_the_fresh_one(tmp_path: Path) -> None:
    ask, said = Ask(), []
    sizer = AiSizer(ask, tool="thử", now=NOW, memory=AnswerMemory(tmp_path), say=said.append)

    sizing = sizer(ORDERS, (), frozenset({3}))

    assert ask.asked == [[1, 2, 3]] and said == ["Đang ước lượng độ lớn bằng thử… (3 đơn)"]
    assert {stt: estimate.size for stt, estimate in sizing.sizes.items()} == {1: Size.L, 2: Size.L, 3: Size.L}
    assert sizing.note == "AI (thử, 3/3 đơn)" and sizing.findings == ()
    assert set(AnswerMemory(tmp_path).ai_answers([("a", "Demo 1.0.0"), ("b", "Demo 1.0.1")])) == {
        ("a", "Demo 1.0.0"),
        ("b", "Demo 1.0.1"),
    }


def test_remembered_orders_are_not_asked_again(tmp_path: Path) -> None:
    AiSizer(Ask(), tool="thử", now=NOW, memory=AnswerMemory(tmp_path))(ORDERS, (), frozenset({3}))
    ask = Ask()

    sizing = AiSizer(ask, tool="thử", now=NOW, memory=AnswerMemory(tmp_path))(ORDERS, (), frozenset({3}))

    assert ask.asked == [[3]]
    assert sizing.note == "AI (thử, 3/3 đơn; 2 từ bộ nhớ)"
    assert [sizing.sizes[stt].remembered for stt in (1, 2, 3)] == [True, True, False]


def test_without_anything_to_ask_the_ai_is_not_called(tmp_path: Path) -> None:
    AiSizer(Ask(), tool="thử", now=NOW, memory=AnswerMemory(tmp_path))(ORDERS[:2], (), frozenset())
    ask = Ask()

    sizing = AiSizer(ask, tool="thử", now=NOW, memory=AnswerMemory(tmp_path))(ORDERS[:2], (), frozenset())

    assert ask.asked == [] and sizing.note == "AI (bộ nhớ, 2/2 đơn)"


def test_a_failed_call_sizes_m_keeps_the_memory_and_saves_nothing(tmp_path: Path) -> None:
    AiSizer(Ask(), tool="thử", now=NOW, memory=AnswerMemory(tmp_path))(ORDERS[:2], (), frozenset())
    fresh = _order(4, "d", "Demo 2.0")

    sizing = AiSizer(Ask("hết thời gian 180s"), tool="thử", now=NOW, memory=AnswerMemory(tmp_path))(
        (*ORDERS[:2], fresh), (), frozenset()
    )

    assert sizing.sizes[4].size is Size.M and sizing.sizes[4].is_default
    assert sizing.note == "mặc định M (hết thời gian 180s); 2 đơn từ bộ nhớ"
    assert [finding.code for finding in sizing.findings] == ["SIZE-AI-FAILED"]
    assert AnswerMemory(tmp_path).ai_answers([("d", "Demo 2.0")]) == {}


def test_without_memory_every_order_is_asked() -> None:
    ask = Ask()

    AiSizer(ask, tool="thử", now=NOW)(ORDERS, (), frozenset())

    assert ask.asked == [[1, 2, 3]]
