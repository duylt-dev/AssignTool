"""Value objects for what the internal system's API returns (bot spec §2). No I/O here."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime

from scrumbot.model import StatusChange

TECH_MANAGER_LIST = "901609972453"  # list "Tech manager" (docs/api-doc-he-thong.md §1)
MAINTAIN_FOLDER = "90169740714"  # folder "Maintain update"


@dataclass(frozen=True, slots=True)
class SprintInfo:
    """One list of folder Maintain, from `/api/doc/sprints`."""

    id: str
    name: str  # "Sprint 10 (10/6 - 10/17)"
    kind: str  # "sprint" or "list"
    start: date | None
    end: date | None
    archived: bool
    total: int  # root task orders
    done: int


@dataclass(frozen=True, slots=True)
class Task:
    """One item of `/api/doc/don`: a root order, a subtask or a bug. Text is NFC-normalised."""

    id: str
    title: str
    parent_id: str  # "" for a root
    is_bug: bool
    status: str  # status name; "" when unknown
    status_kind: str  # "open", "custom", "done", "closed"; "" when unknown
    assignees: tuple[str, ...]  # names
    priority_raw: str
    due: date | None
    hours: float | None
    app: str
    created: datetime
    updated: datetime | None
    closed: datetime | None
    home_list: str


@dataclass(frozen=True, slots=True)
class Board:
    """Everything one run read: sprints, the items of each list, and the status history.

    `lists` maps a list id to its items (pages merged, every level of the tree); the Tech manager list is one of
    them. It is never mutated after the reader builds it.
    """

    sprints: tuple[SprintInfo, ...]
    lists: Mapping[str, tuple[Task, ...]]
    changes: tuple[StatusChange, ...]
    status_kinds: Mapping[str, str]  # text_key(status name) -> kind, over every status table read (A74)
    fetched_at: datetime
    source: str  # "API devclickup.datlt.site", "Snapshot <dir>", "Bản sao <dir>"
