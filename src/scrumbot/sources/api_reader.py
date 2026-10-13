"""Turn raw `/api/doc/` replies into model values (bot spec §2.5). No decisions and no I/O: the replies come from
`raw_store`. Text is NFC-normalised here, at the boundary (best practices §3)."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime

from scrumbot.errors import InputError
from scrumbot.model import StatusChange
from scrumbot.model_board import Board, SprintInfo, Task
from scrumbot.normalize import clean, text_key

_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d")


def read_board(
    raw_sprints: Mapping[str, object],
    raw_lists: Mapping[str, Mapping[str, object]],
    raw_history: Mapping[str, object] | None,
    fetched_at: datetime,
    source: str,
) -> Board:
    """One Board from the replies of a run: `/sprints`, `/don` per list id, and the merged `/lich-su`."""
    sprints = read_sprints(raw_sprints)
    kinds: dict[str, str] = {}
    for list_id, raw in raw_lists.items():
        for status in _items(raw, "trang_thai", f"don {list_id}"):
            name = clean(status.get("ten"))
            if name:
                kinds.setdefault(text_key(name), clean(status.get("kieu")))
    lists = {list_id: read_tasks(raw, list_id) for list_id, raw in raw_lists.items()}
    changes = read_changes(raw_history) if raw_history is not None else ()
    return Board(sprints, lists, changes, kinds, fetched_at, source)


def read_sprints(raw: Mapping[str, object]) -> tuple[SprintInfo, ...]:
    where = "sprints"
    return tuple(
        SprintInfo(
            _text(item, "id", where),
            clean(item.get("ten")),
            clean(item.get("kieu")),
            _day(item.get("bat_dau"), where),
            _day(item.get("ket_thuc"), where),
            bool(item.get("luu_tru")),
            _int(item.get("tong")),
            _int(item.get("xong")),
        )
        for item in _items(raw, "sprints", where)
    )


def read_tasks(raw: Mapping[str, object], list_id: str) -> tuple[Task, ...]:
    where = f"don {list_id}"
    statuses = {item.get("id"): item for item in _items(raw, "trang_thai", where)}
    people = {item.get("id"): clean(item.get("ten")) for item in _items(raw, "nguoi", where)}
    tasks = []
    for item in _items(raw, "don", where):
        status = statuses.get(item.get("trang_thai_id"), {})
        created = _time(item.get("ngay_tao"), where)
        if created is None:
            raise InputError(f"Dữ liệu API không đúng dạng ({where}): đơn '{item.get('id')}' thiếu 'ngay_tao'.")
        assignees = item.get("nguoi_lam_ids") or []
        if not isinstance(assignees, list):
            raise InputError(f"Dữ liệu API không đúng dạng ({where}): 'nguoi_lam_ids' không phải danh sách.")
        tasks.append(
            Task(
                _text(item, "id", where),
                clean(item.get("ten")),
                clean(item.get("cha_id")),
                clean(item.get("loai")).casefold() == "bug",
                clean(status.get("ten")),
                clean(status.get("kieu")),
                tuple(name for name in (people.get(person, "") for person in assignees) if name),
                clean(item.get("uu_tien")),
                _day(item.get("han"), where),
                _hours(item.get("uoc_luong_gio")),
                clean(item.get("app")),
                created,
                _time(item.get("ngay_cap_nhat"), where),
                _time(item.get("ngay_dong"), where),
                clean(item.get("list_nha_id")),
            )
        )
    return tuple(tasks)


def read_changes(raw: Mapping[str, object]) -> tuple[StatusChange, ...]:
    where = "lich-su"
    changes = []
    for item in _items(raw, "doi_trang_thai", where):
        at = _time(item.get("luc"), where)
        if at is None:
            continue
        changes.append(StatusChange(_text(item, "task_id", where), clean(item.get("tu")), clean(item.get("den")), at))
    return tuple(sorted(changes, key=lambda change: change.at))


def _items(raw: Mapping[str, object], key: str, where: str) -> list[Mapping[str, object]]:
    value = raw.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise InputError(f"Dữ liệu API không đúng dạng ({where}): '{key}' không phải danh sách.")
    return value


def _text(item: Mapping[str, object], key: str, where: str) -> str:
    value = clean(item.get(key))
    if not value:
        raise InputError(f"Dữ liệu API không đúng dạng ({where}): thiếu '{key}'.")
    return value


def _time(value: object, where: str) -> datetime | None:
    if value is None or value == "":
        return None
    text = clean(value)
    for pattern in _FORMATS:
        try:
            return datetime.strptime(text, pattern)
        except ValueError:
            continue
    raise InputError(f"Dữ liệu API không đúng dạng ({where}): không đọc được thời gian '{text}'.")


def _day(value: object, where: str) -> date | None:
    moment = _time(value, where)
    return moment.date() if moment is not None else None


def _int(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _hours(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None
