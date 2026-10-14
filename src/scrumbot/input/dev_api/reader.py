"""Turn raw `/api/doc/` replies into the values of the standard input (bot spec §2.5, §8.3). No decisions and no
I/O: the replies come from `cache.LiveSource`. Text is NFC-normalised here, at the boundary (best practices §3)."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime

from scrumbot.core.errors import InputError
from scrumbot.core.inputs import SprintInfo, Task
from scrumbot.core.model import StatusChange
from scrumbot.core.normalize import clean

_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d")


def read_sprints(raw: Mapping[str, object]) -> tuple[SprintInfo, ...]:
    where = "sprints"
    return tuple(
        SprintInfo(
            id=_text(item, "id", where),
            name=clean(item.get("ten")),
            kind=clean(item.get("kieu")),
            total=_int(item.get("tong")),
            start=_day(item.get("bat_dau"), where),
            end=_day(item.get("ket_thuc"), where),
            archived=bool(item.get("luu_tru")),
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
                id=_text(item, "id", where),
                title=clean(item.get("ten")),
                created=created,
                parent_id=clean(item.get("cha_id")),
                is_bug=clean(item.get("loai")).casefold() == "bug",
                status=clean(status.get("ten")),
                status_kind=clean(status.get("kieu")),
                assignees=tuple(name for name in (people.get(person, "") for person in assignees) if name),
                priority_raw=clean(item.get("uu_tien")),
                due=_day(item.get("han"), where),
                hours=_hours(item.get("uoc_luong_gio")),
                app=clean(item.get("app")),
                updated=_time(item.get("ngay_cap_nhat"), where),
                closed=_time(item.get("ngay_dong"), where),
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
        changes.append(StatusChange(_text(item, "task_id", where), clean(item.get("den")), at))
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
