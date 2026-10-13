"""Where a run gets the raw API replies (bot spec §2.3; A57, A58): live from the API, with lists that no longer change
kept in a cache on disk."""

from __future__ import annotations

import gzip
import json
from datetime import date, datetime
from pathlib import Path
from typing import Protocol

from scrumbot.errors import InputError
from scrumbot.model_board import MAINTAIN_FOLDER, SprintInfo
from scrumbot.sources.api_client import ApiClient

LISTS = "don"


class RawSource(Protocol):
    """What a run reads, whatever it comes from."""

    label: str

    def sprints(self) -> dict[str, object]: ...

    def orders(self, list_id: str, sprint: SprintInfo | None) -> dict[str, object]: ...

    def history(self, ids: list[str]) -> dict[str, object]: ...


def write_json(path: Path, value: object) -> None:
    """Gzip JSON, written to `.tmp` then renamed (best practices §6)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with gzip.open(temporary, "wt", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False)
    temporary.replace(path)


def read_json(folder: Path, name: str) -> dict[str, object]:
    """`<name>.json.gz` or `<name>.json` in `folder`; a missing or unreadable file is an input error."""
    for candidate, opener in ((folder / f"{name}.json.gz", gzip.open), (folder / f"{name}.json", open)):
        if candidate.is_file():
            try:
                with opener(candidate, "rt", encoding="utf-8") as handle:
                    value = json.load(handle)
            except (OSError, EOFError, UnicodeDecodeError, json.JSONDecodeError) as error:
                raise InputError(f"Không đọc được file '{candidate}': {error}") from error
            if not isinstance(value, dict):
                raise InputError(f"File '{candidate}' không phải dữ liệu API.")
            return value
    raise InputError(f"Thư mục '{folder}' không có {name}.json.gz.")


class LiveSource:
    """Reads the API; lists that no longer change come from `cache_dir` (A58)."""

    def __init__(self, client: ApiClient, cache_dir: Path, today: date) -> None:
        self._client = client
        self._cache = cache_dir
        self._today = today
        self.label = f"API {client.host}"

    def sprints(self) -> dict[str, object]:
        return self._client.sprints(MAINTAIN_FOLDER)

    def orders(self, list_id: str, sprint: SprintInfo | None) -> dict[str, object]:
        cached = self._cache / LISTS / f"{list_id}.json.gz"
        policy = _cache_policy(sprint, self._today)
        if policy == "forever" and cached.is_file() or policy == "today" and _written_on(cached, self._today):
            value = read_json(cached.parent, list_id)
        else:
            value = self._client.orders(list_id)
            if policy is not None:
                write_json(cached, value)
        return value

    def history(self, ids: list[str]) -> dict[str, object]:
        return self._client.history(ids)


def _cache_policy(sprint: SprintInfo | None, today: date) -> str | None:
    if sprint is None:
        return None
    if sprint.archived:
        return "forever"
    if sprint.end is not None and sprint.end < today:
        return "today"
    return None


def _written_on(path: Path, day: date) -> bool:
    return path.is_file() and datetime.fromtimestamp(path.stat().st_mtime).date() == day
