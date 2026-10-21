"""Today's sizer (bot spec §2.6, §8.5): AI answers from the memory when the same order id and title was sized before,
one AI call for the rest. Any `ask` plugs in; the prompt, its parsing and the memory stay as they are."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from scrumbot.ai.memory import AnswerMemory
from scrumbot.ai.prompt import build_prompt, parse_reply
from scrumbot.ai.tools import Ask
from scrumbot.core.assign.sizing import Sizing
from scrumbot.core.model import HistoryOrder, Order

Say = Callable[[str], None]


class AiSizer:
    """A `core.Sizer`. `tool` names the AI in the notes and the memory; `now` is the run time stored with an answer."""

    def __init__(
        self, ask: Ask, *, tool: str, now: datetime, memory: AnswerMemory | None = None, say: Say | None = None
    ) -> None:
        self._ask = ask
        self._tool = tool
        self._now = now
        self._memory = memory
        self._say = say or (lambda _line: None)

    def __call__(self, orders: tuple[Order, ...], examples: tuple[HistoryOrder, ...], fresh: frozenset[int]) -> Sizing:
        """Orders whose STT is in `fresh` are always sized by the call and never remembered: their description comes
        from the filed order (bot spec §7.2)."""
        keys = [(order.row.id, order.row.title) for order in orders if order.row.id and order.row.stt not in fresh]
        remembered = self._memory.ai_answers(keys) if self._memory is not None else {}
        sizes = {
            order.row.stt: remembered[key] for order in orders if (key := (order.row.id, order.row.title)) in remembered
        }
        todo = tuple(order for order in orders if order.row.stt not in sizes)
        if not todo:
            return Sizing(sizes, (), f"AI (bộ nhớ, {len(sizes)}/{len(orders)} đơn)")
        self._say(f"Đang ước lượng độ lớn bằng {self._tool}… ({len(todo)} đơn)")
        reply = self._ask(build_prompt(todo, examples))
        sized, findings, note = parse_reply(reply, todo)
        if self._memory is not None and reply.failure is None:
            self._memory.save_ai_answers(
                {(o.row.id, o.row.title): sized[o.row.stt] for o in todo if o.row.id and o.row.stt not in fresh},
                self._tool,
                self._now,
            )
        sizes.update(sized)
        if remembered:
            valid = sum(not estimate.is_default for estimate in sizes.values())
            note = (
                f"{note}; {len(remembered)} đơn từ bộ nhớ"
                if reply.failure is not None
                else f"AI ({self._tool}, {valid}/{len(orders)} đơn; {len(remembered)} từ bộ nhớ)"
            )
        return Sizing(sizes, findings, note)
