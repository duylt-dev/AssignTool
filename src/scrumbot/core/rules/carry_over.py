"""Carry-over counts from the previous sprint."""

from __future__ import annotations

from scrumbot.core.model import Dev, SprintView
from scrumbot.core.normalize import text_key

BUSY_STATUSES = frozenset(
    {
        text_key("qa - need fix"),
        text_key("all issue"),
        text_key("in progress"),
        text_key("ready to progress"),
        text_key("need to be clean"),
        text_key("internal - cant fix"),
        text_key("internal - need fix"),
        text_key("đã ro"),
    }
)


def carry_over(prev: SprintView | None, pool: tuple[Dev, ...]) -> dict[str, int]:
    """Count busy previous rows for each pool member, including subtasks."""
    counts = {dev.code: 0 for dev in pool}
    if prev is None:
        return counts
    for row in prev.rows:
        if text_key(row.status) not in BUSY_STATUSES:
            continue
        assignees = {text_key(name) for name in row.assignees}
        for dev in pool:
            if text_key(dev.name) in assignees:
                counts[dev.code] += 1
    return counts
