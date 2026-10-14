"""The API replies of a run (bot spec §2.3, A58): live from the API, with lists that no longer change kept in a cache
on disk."""

from __future__ import annotations

import gzip
import json
from datetime import date, datetime
from pathlib import Path

from scrumbot.core.errors import InputError
from scrumbot.core.inputs import SprintInfo
from scrumbot.input.dev_api.client import ApiClient
from scrumbot.input.dev_api.config import MAINTAIN_FOLDER

LISTS = "don"


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
        """The list `list_id`; `sprint` is the list as a sprint when it may come from the cache, else None."""
        cached = self._cache / LISTS / f"{list_id}.json.gz"
        policy = _cache_policy(sprint, self._today)
        if policy == "forever" and cached.is_file() or policy == "today" and _written_on(cached, self._today):
            return read_json(cached)
        value = self._client.orders(list_id)
        if policy is not None:
            write_json(cached, value)
        return value

    def history(self, ids: list[str]) -> dict[str, object]:
        return self._client.history(ids)


def write_json(path: Path, value: object) -> None:
    """Gzip JSON, written to `.tmp` then renamed (best practices §6)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with gzip.open(temporary, "wt", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False)
    temporary.replace(path)


def read_json(path: Path) -> dict[str, object]:
    """A cached reply; an unreadable file is an input error."""
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, EOFError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InputError(f"Không đọc được file '{path}': {error}") from error
    if not isinstance(value, dict):
        raise InputError(f"File '{path}' không phải dữ liệu API.")
    return value


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
