"""Synthetic `/api/doc/` payloads in the API's real shapes (docs/api-doc-he-thong.md §4–§6). Nothing here comes from
`input/` or the system: the four pool devs' names are configuration (spec §4), everybody else has a made-up name."""

from __future__ import annotations

from datetime import date, datetime

from scrumbot.model import Dev, Level
from scrumbot.model_board import TECH_MANAGER_LIST

LINH, MINH, AN, TIEN = "Ngọc Văn Linh", "Nguyễn Nhật Minh", "Trần Đức An", "Bùi Văn Tiến"
OUTSIDER = "Người Ngoài Team"
POOL = (
    Dev(LINH, "LinhNV", Level.MIDDLE_PLUS, True, ()),
    Dev(MINH, "MinhNM", Level.MIDDLE, True, ()),
    Dev(AN, "AnTD", Level.JUNIOR_PLUS, True, ()),
    Dev(TIEN, "TiếnBV", Level.JUNIOR, True, ()),
)
DEV_ROWS = [
    {"Tên": dev.name, "Mã": dev.code, "Level": level, "Nhận việc": "Y"}
    for dev, level in zip(POOL, ("middle+", "middle", "junior+", "junior"), strict=True)
]
_PEOPLE = {LINH: 101, MINH: 102, AN: 103, TIEN: 104, OUTSIDER: 900}
_KINDS = {
    "all issue": "open",
    "ready to progress": "custom",
    "in progress": "custom",
    "pending": "custom",
    "qa - testing": "custom",
    "qa - need fix": "custom",
    "ready to qa-testing": "custom",
    "ready to internal testing": "custom",
    "need to be clean": "custom",
    "ready to release": "done",
    "done": "done",
    "đã ro": "done",
    "close": "closed",
}


def stamp(value: date | datetime | str | None) -> str | None:
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return f"{value:%Y-%m-%d} 00:00:00"


def sprint(
    sprint_id: str,
    name: str,
    start: date,
    end: date,
    *,
    archived: bool = False,
    total: int = 1,
    kind: str = "sprint",
) -> dict[str, object]:
    return {
        "id": sprint_id,
        "ten": name,
        "kieu": kind,
        "bat_dau": f"{start:%Y-%m-%d} 00:00:00",
        "ket_thuc": f"{end:%Y-%m-%d} 23:59:59",
        "luu_tru": archived,
        "tong": total,
        "xong": 0,
    }


def sprints(*items: dict[str, object]) -> dict[str, object]:
    return {"ok": True, "sprints": list(items)}


def item(
    item_id: str,
    title: str = "1.0.1 - Add ads",
    *,
    parent: str | None = None,
    bug: bool = False,
    status: str = "in progress",
    people: tuple[str, ...] = (),
    app: str = "Demo",
    priority: str | None = None,
    due: date | None = None,
    hours: float | None = None,
    created: date | datetime | str = datetime(2026, 10, 1, 9, 0),
    updated: date | datetime | str | None = None,
    closed: date | datetime | str | None = None,
    home: str = TECH_MANAGER_LIST,
) -> dict[str, object]:
    """One item of `/don`; `status` and `people` are names, turned into ids by `orders`."""
    return {
        "id": item_id,
        "ten": title,
        "cha_id": parent,
        "loai": "bug" if bug else "task",
        "_status": status,
        "_people": list(people),
        "uu_tien": priority,
        "bat_dau": None,
        "han": stamp(due),
        "uoc_luong_gio": hours,
        "app": app,
        "nguoi_tao_id": _PEOPLE[OUTSIDER],
        "ngay_tao": stamp(created),
        "ngay_cap_nhat": stamp(updated or created),
        "ngay_dong": stamp(closed),
        "list_nha_id": home,
        "bug_mo": 0,
        "bug_tong": 0,
    }


def orders(*items: dict[str, object]) -> dict[str, object]:
    """A `/don` reply: items with status and people ids, and the lookup tables of the names they use."""
    statuses: dict[str, int] = {}
    people: dict[str, int] = {}
    shaped = []
    for raw in items:
        entry = {key: value for key, value in raw.items() if not key.startswith("_")}
        status = str(raw["_status"])
        statuses.setdefault(status, 600 + len(statuses))
        entry["trang_thai_id"] = statuses[status]
        entry["nguoi_lam_ids"] = [_PEOPLE[name] for name in raw["_people"]]  # type: ignore[union-attr]
        for name in raw["_people"]:  # type: ignore[union-attr]
            people[name] = _PEOPLE[name]
        shaped.append(entry)
    roots = sum(entry["cha_id"] is None for entry in shaped)
    return {
        "ok": True,
        "trang": 1,
        "goc_moi_trang": 500,
        "tong_goc": roots,
        "don": shaped,
        "trang_thai": [
            {"id": ident, "ten": name, "kieu": _KINDS.get(name, "custom")} for name, ident in statuses.items()
        ],
        "nguoi": [{"id": ident, "ten": name} for name, ident in people.items()],
    }


def history(*changes: tuple[str, str | None, str, datetime]) -> dict[str, object]:
    """A merged `/lich-su` reply from (task id, old status, new status, time)."""
    return {
        "ok": True,
        "ids": sorted({change[0] for change in changes}),
        "khong_thay": [],
        "doi_trang_thai": [
            {"task_id": task, "tu": old, "den": new, "luc": stamp(at), "nguoi_id": None}
            for task, old, new, at in changes
        ],
        "comment": [],
        "nguoi": [],
    }
