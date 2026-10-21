"""How the review asks the AI (bot spec §7.3, §8.5): the asker it is given, else no template check and no question.
Pure."""

from __future__ import annotations

from typing import Protocol

from scrumbot.core.model import OrderKind, SprintRow
from scrumbot.core.outcome import AiReview

AI_OFF = AiReview(note="tắt AI")


class Asker(Protocol):
    """The AI (bot spec §8.5). `row` is the filed order as placed, its description already scrubbed; `kind` is the
    file's `Loại đơn`, or None for the AI to name the type. An asker never raises for an AI failure: it returns no
    check and no question, `answered` false, and why in the note."""

    def __call__(self, row: SprintRow, kind: OrderKind | None) -> AiReview: ...
