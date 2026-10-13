"""Read an order file written by BA/MO (bot spec §7.1) into an OrderDraft. The only module that reads order files."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from scrumbot.errors import InputError
from scrumbot.model import OrderDraft
from scrumbot.normalize import clean, header_key, parse_date

_TITLE = re.compile(r"^#\s+(.+?)\s*#*\s*$")
_DELIMITER = re.compile(r"^:?-+:?$")
_FIELDS = {
    "id": "id",
    "id trên hệ thống": "id",
    "app": "app",
    "app name": "app",
    "ưu tiên": "priority",
    "hạn": "due",
}
_TABLE_HEAD = "trường"


def read_order(path: Path) -> OrderDraft:
    """The `#` title, the `| Trường | Giá trị |` table, and every other line as the description."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as error:
        raise InputError(f"Không đọc được file đơn '{path}': {error}") from error
    lines = unicodedata.normalize("NFC", text).splitlines()
    title = ""
    fields: dict[str, str] = {}
    rest: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not title and (match := _TITLE.match(line.strip())):
            title = clean(match[1])
            index += 1
            continue
        if not fields and _is_field_table(lines, index):
            index = _read_fields(path, lines, index, fields)
            continue
        rest.append(line)
        index += 1
    due_text = fields.get("due", "")
    try:
        due = parse_date(due_text)
    except ValueError:
        raise InputError(
            f"File đơn '{path}': Hạn '{due_text}' không đọc được; dùng YYYY-MM-DD hoặc DD/MM/YYYY."
        ) from None
    return OrderDraft(
        title=title or clean(path.stem),
        order_id=fields.get("id", ""),
        app=fields.get("app", ""),
        priority_raw=fields.get("priority", ""),
        due=due,
        description="\n".join(rest).strip(),
    )


def _cells(line: str) -> list[str]:
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return [clean(cell) for cell in inner.split("|")]


def _is_field_table(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines) or not lines[index].strip().startswith("|"):
        return False
    head, delimiter = _cells(lines[index]), _cells(lines[index + 1])
    return bool(head) and header_key(head[0]) == _TABLE_HEAD and all(_DELIMITER.match(cell) for cell in delimiter)


def _read_fields(path: Path, lines: list[str], index: int, fields: dict[str, str]) -> int:
    """Rows of the field table into `fields`; returns the index of the first line after the table."""
    index += 2
    while index < len(lines) and lines[index].strip().startswith("|"):
        cells = [*_cells(lines[index]), ""]
        key, value = header_key(cells[0]), cells[1]
        if key or value:
            if key not in _FIELDS:
                raise InputError(
                    f"File đơn '{path}' dòng {index + 1}: trường '{cells[0]}' không hợp lệ; "
                    "dùng ID, App, Ưu tiên hoặc Hạn."
                )
            fields[_FIELDS[key]] = value
        index += 1
    return index
