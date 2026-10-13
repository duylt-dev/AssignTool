"""Raw API replies on disk and where a run gets them (bot spec §2.3, §2.4; A57, A58): live from the API with the
list cache and a snapshot of what was read, or from a stored snapshot or clone."""

from __future__ import annotations

import gzip
import json
from datetime import date, datetime
from pathlib import Path
from typing import Protocol

from scrumbot.errors import InputError
from scrumbot.model_board import MAINTAIN_FOLDER, SprintInfo
from scrumbot.sources.api_client import ApiClient

META = "meta.json"
SPRINTS = "sprints"
HISTORY = "lich-su"
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


def has_json(folder: Path, name: str) -> bool:
    return (folder / f"{name}.json.gz").is_file() or (folder / f"{name}.json").is_file()


class Recorder:
    """Writes every reply a run used into one folder: a snapshot, or a clone (bot spec §2.4)."""

    def __init__(self, folder: Path, *, kind: str, host: str, now: datetime) -> None:
        self.folder = folder
        folder.mkdir(parents=True, exist_ok=True)
        meta = {"kind": kind, "host": host, "fetched_at": now.strftime("%Y-%m-%d %H:%M:%S")}
        (folder / META).write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    def save(self, name: str, value: object) -> None:
        write_json(self.folder / f"{name}.json.gz", value)


class LiveSource:
    """Reads the API; lists that no longer change come from `cache_dir` (A58); everything used is recorded."""

    def __init__(self, client: ApiClient, cache_dir: Path, recorder: Recorder | None, today: date) -> None:
        self._client = client
        self._cache = cache_dir
        self._recorder = recorder
        self._today = today
        self.label = f"API {client.host}"

    def sprints(self) -> dict[str, object]:
        return self._record(SPRINTS, self._client.sprints(MAINTAIN_FOLDER))

    def orders(self, list_id: str, sprint: SprintInfo | None) -> dict[str, object]:
        cached = self._cache / LISTS / f"{list_id}.json.gz"
        policy = _cache_policy(sprint, self._today)
        if policy == "forever" and cached.is_file() or policy == "today" and _written_on(cached, self._today):
            value = read_json(cached.parent, list_id)
        else:
            value = self._client.orders(list_id)
            if policy is not None:
                write_json(cached, value)
        return self._record(f"{LISTS}/{list_id}", value)

    def history(self, ids: list[str]) -> dict[str, object]:
        return self._record(HISTORY, self._client.history(ids))

    def _record(self, name: str, value: dict[str, object]) -> dict[str, object]:
        if self._recorder is not None:
            self._recorder.save(name, value)
        return value


class StoredSource:
    """Reads a snapshot or a clone; lists missing from it come from the cache when one is given (bot spec §2.4)."""

    def __init__(self, folder: Path, cache_dir: Path | None) -> None:
        if not folder.is_dir():
            raise InputError(f"Không có thư mục '{folder}'.")
        self._folder = folder
        self._cache = cache_dir
        kind = _meta(folder).get("kind")
        self.label = f"{'Bản sao' if kind == 'clone' else 'Snapshot'} {folder}"
        self.fetched_at = _fetched_at(folder)

    def sprints(self) -> dict[str, object]:
        return read_json(self._folder, SPRINTS)

    def orders(self, list_id: str, sprint: SprintInfo | None) -> dict[str, object]:
        lists = self._folder / LISTS
        if not has_json(lists, list_id) and self._cache is not None and has_json(self._cache / LISTS, list_id):
            return read_json(self._cache / LISTS, list_id)
        return read_json(lists, list_id)

    def history(self, ids: list[str]) -> dict[str, object]:
        if not has_json(self._folder, HISTORY):
            return {"ok": True, "ids": [], "doi_trang_thai": [], "comment": [], "nguoi": [], "khong_thay": []}
        return read_json(self._folder, HISTORY)


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


def _meta(folder: Path) -> dict[str, object]:
    path = folder / META
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _fetched_at(folder: Path) -> datetime | None:
    raw = _meta(folder).get("fetched_at")
    try:
        return datetime.strptime(str(raw), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
