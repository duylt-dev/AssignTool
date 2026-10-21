"""Today's asker (bot spec §7.3, §8.5): one AI call for the template check and the questions of `review`. Any `ask`
plugs in; the prompt and its parsing stay as they are. Nothing of it is remembered (A90, A107)."""

from __future__ import annotations

from collections.abc import Callable

from scrumbot.ai.prompt import build_review_prompt, parse_review
from scrumbot.ai.tools import Ask
from scrumbot.core.model import OrderKind, SprintRow
from scrumbot.core.outcome import AiReview

Say = Callable[[str], None]


class AiAsker:
    """A `core.Asker`. `tool` names the AI in the line said before the call."""

    def __init__(self, ask: Ask, *, tool: str, say: Say | None = None) -> None:
        self._ask = ask
        self._tool = tool
        self._say = say or (lambda _line: None)

    def __call__(self, row: SprintRow, kind: OrderKind | None) -> AiReview:
        self._say(f"Đang hỏi {self._tool} về mô tả đơn…")
        return parse_review(self._ask(build_review_prompt(row, kind)), kind)
