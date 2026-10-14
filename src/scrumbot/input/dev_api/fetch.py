"""What one run reads from the dev API (bot spec §2.3): the sprint list, every Maintain sprint, list Tech manager, and
the status history of the running sprint."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from scrumbot.core.inputs import SprintInfo, Task
from scrumbot.core.model import StatusChange
from scrumbot.core.rules.board import maintain_sprints, select_current
from scrumbot.input.dev_api.cache import LiveSource
from scrumbot.input.dev_api.client import ApiClient
from scrumbot.input.dev_api.config import TECH_MANAGER_LIST, ApiConfig
from scrumbot.input.dev_api.reader import read_changes, read_sprints, read_tasks


@dataclass(frozen=True)
class Snapshot:
    """The system's part of the standard input (bot spec §8.3)."""

    source: str  # "API devclickup.datlt.site"
    fetched_at: datetime
    sprints: tuple[SprintInfo, ...]
    lists: Mapping[str, tuple[Task, ...]]
    history_lists: tuple[str, ...]
    status_changes: tuple[StatusChange, ...]


def read_snapshot(config: ApiConfig, cache_dir: Path, *, day: date, sprint_id: str | None, now: datetime) -> Snapshot:
    """The running sprint (or `sprint_id`) is picked as the core picks it, so that only its lists are read fresh and
    only its items' history is read."""
    source = LiveSource(ApiClient(config), cache_dir, day)
    raw_sprints = source.sprints()
    sprints = read_sprints(raw_sprints)
    current = select_current(sprints, day, sprint_id)
    raw_lists: dict[str, dict[str, object]] = {}
    for sprint in maintain_sprints(sprints):
        if sprint.id != current.id:
            raw_lists[sprint.id] = source.orders(sprint.id, sprint)
    raw_lists[current.id] = source.orders(current.id, None)
    raw_lists[TECH_MANAGER_LIST] = source.orders(TECH_MANAGER_LIST, None)
    lists = {list_id: read_tasks(raw, list_id) for list_id, raw in raw_lists.items()}
    ids = [task.id for task in lists[current.id]]
    return Snapshot(
        source=source.label,
        fetched_at=now,
        sprints=sprints,
        lists=lists,
        history_lists=(TECH_MANAGER_LIST,),
        status_changes=read_changes(source.history(ids)) if ids else (),
    )
