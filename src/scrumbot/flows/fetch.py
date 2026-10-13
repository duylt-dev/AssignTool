"""Read what a run needs from a raw source (bot spec §2.3) and build the Board."""

from __future__ import annotations

from datetime import date, datetime

from scrumbot.model_board import TECH_MANAGER_LIST, Board, SprintInfo
from scrumbot.rules.board import maintain_sprints, select_current
from scrumbot.sources.api_reader import read_board, read_sprints, read_tasks
from scrumbot.sources.raw_store import RawSource


def load_board(
    source: RawSource, *, day: date, sprint_id: str | None, fetched_at: datetime
) -> tuple[Board, SprintInfo]:
    """The sprint list, every Maintain sprint and list Tech manager, and the history of the running sprint."""
    raw_sprints = source.sprints()
    sprints = read_sprints(raw_sprints)
    current = select_current(sprints, day, sprint_id)
    lists: dict[str, dict[str, object]] = {}
    for sprint in maintain_sprints(sprints):
        if sprint.id != current.id:
            lists[sprint.id] = source.orders(sprint.id, sprint)
    lists[current.id] = source.orders(current.id, None)
    lists[TECH_MANAGER_LIST] = source.orders(TECH_MANAGER_LIST, None)
    ids = [task.id for task in read_tasks(lists[current.id], current.id)]
    raw_history = source.history(ids) if ids else None
    return read_board(raw_sprints, lists, raw_history, fetched_at, source.label), current


def load_everything(source: RawSource, fetched_at: datetime) -> Board:
    """A whole clone: every list it holds and its whole history (bot spec §8)."""
    raw_sprints = source.sprints()
    sprints = read_sprints(raw_sprints)
    lists = {sprint.id: source.orders(sprint.id, sprint) for sprint in maintain_sprints(sprints)}
    lists[TECH_MANAGER_LIST] = source.orders(TECH_MANAGER_LIST, None)
    return read_board(raw_sprints, lists, source.history([]), fetched_at, source.label)
