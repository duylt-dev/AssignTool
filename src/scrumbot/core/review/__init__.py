"""The review step (bot spec §7.3, D64): what blocks the filed order, then the AI's questions when nothing does. Pure;
it never imports `core.assign`."""

from __future__ import annotations

from dataclasses import replace

from scrumbot.core.outcome import Outcome, Status
from scrumbot.core.place import Placed
from scrumbot.core.review.asking import AI_OFF, Asker
from scrumbot.core.review.checks import blocking


def review(placed: Placed, asker: Asker | None = None) -> Outcome:
    """`pre_assigned` with no check (A87); `not_ready` with what to fix and no AI call (A86); else `ready` with the AI's
    questions. The caller keeps the `order.fingerprint` of a `ready` outcome: `assign` needs it (A101)."""
    order = placed.order
    if order.row.assignees:
        return placed.outcome(Status.PRE_ASSIGNED)
    items = blocking(order.row, order.how)
    if items:
        return replace(placed.outcome(Status.NOT_READY), review=items)
    return replace(placed.outcome(Status.READY), questions=asker(order.row) if asker is not None else AI_OFF)
