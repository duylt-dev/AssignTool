"""The review step (bot spec §7.3, D64, D65): what blocks the filed order, then the AI's template check and questions
when nothing does. Pure; it never imports `core.assign`."""

from __future__ import annotations

from dataclasses import replace

from scrumbot.core.outcome import Outcome, Status
from scrumbot.core.place import Placed
from scrumbot.core.review.asking import AI_OFF, Asker
from scrumbot.core.review.checks import blocking
from scrumbot.core.review.templates import settled, template_item


def review(placed: Placed, asker: Asker | None = None) -> Outcome:
    """`pre_assigned` with no check (A87); `not_ready` with what to fix and no AI call (A86); else the AI's template
    check, `not_ready` when it names missing points (A107), `ready` otherwise. The caller keeps the
    `order.fingerprint` of a `ready` outcome: `assign` needs it (A101)."""
    order, draft = placed.order, placed.inputs.order
    if order.row.assignees:
        return placed.outcome(Status.PRE_ASSIGNED)
    items = blocking(order.row, order.how, owner=draft.owner, evidence=draft.evidence)
    if items:
        return replace(placed.outcome(Status.NOT_READY), review=items)
    ai = settled(draft.kind, asker(order.row, draft.kind) if asker is not None else AI_OFF)
    item = template_item(ai)
    if item is not None:
        return replace(placed.outcome(Status.NOT_READY), review=(item,), ai=ai)
    return replace(placed.outcome(Status.READY), ai=ai)
