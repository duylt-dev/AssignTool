"""The standard input of the core (bot spec §8.3): the system's sprints and items, the devs, the TM rules and the order
being filed. Every input adapter builds an `Inputs`; the core reads nothing else. No I/O here."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import cast

from scrumbot.core.codec import from_plain, invalid, to_plain
from scrumbot.core.model import Dev, OrderDraft, StatusChange, TeamRule

FORMAT = "scrumbot-input/1"


@dataclass(frozen=True, slots=True, kw_only=True)
class SprintInfo:
    """One list of board Maintain (bot spec §2.3)."""

    id: str
    name: str  # "Sprint 10 (10/6 - 10/17)"
    kind: str  # "sprint" or "list"
    total: int  # root orders; a list with 0 is not a Maintain sprint (A56)
    start: date | None = None
    end: date | None = None
    archived: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class Task:
    """One item of a list: a root order, a subtask or a bug (bot spec §2.5). Text is NFC-normalised."""

    id: str
    title: str
    created: datetime
    parent_id: str = ""  # "" for a root
    is_bug: bool = False
    status: str = ""  # status name; "" when unknown
    status_kind: str = ""  # "open", "custom", "done", "closed"; "" when unknown
    assignees: tuple[str, ...] = ()  # full names
    priority_raw: str = ""
    due: date | None = None
    hours: float | None = None  # the human estimate: an AI example on history orders only (D3)
    app: str = ""
    updated: datetime | None = None
    closed: datetime | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class Inputs:
    """Everything one run decides on. `lists` maps a list id to its items, every level of the tree; it holds at least
    every Maintain sprint, and the lists of `history_lists`."""

    source: str  # "API devclickup.datlt.site"
    fetched_at: datetime
    sprints: tuple[SprintInfo, ...]
    lists: Mapping[str, tuple[Task, ...]]
    history_lists: tuple[str, ...] = ()  # lists that are not sprints but count as history (bot spec §2.5)
    status_changes: tuple[StatusChange, ...] = ()
    devs: tuple[Dev, ...]
    rules: tuple[TeamRule, ...] = ()
    rules_source: str = ""  # where the rules came from, quoted in rule errors; "" without rules
    order: OrderDraft

    @classmethod
    def from_dict(cls, data: object) -> Inputs:
        """The JSON form (bot spec §8.3); an InputError names the first field that does not fit."""
        if not isinstance(data, dict):
            raise invalid("", "không phải bảng")
        if data.get("format") is None:
            raise invalid("format", "thiếu")
        if data["format"] != FORMAT:
            raise invalid("", f"format '{data['format']}', cần {FORMAT}")
        return cast(Inputs, from_plain(cls, data, ""))

    def to_dict(self) -> dict[str, object]:
        return {"format": FORMAT, **cast(dict[str, object], to_plain(self))}
