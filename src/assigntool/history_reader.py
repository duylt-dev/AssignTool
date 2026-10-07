"""Read the task-history CSV into HistoryOrder values (spec §5)."""

from __future__ import annotations

import csv
from pathlib import Path

from assigntool.errors import InputError
from assigntool.model import HistoryOrder
from assigntool.normalize import clean, header_key, parse_date, split_people, text_key

_REQUIRED = ("sprint", "loại", "app name", "người làm", "ngày tạo")


def read_history(path: Path) -> tuple[HistoryOrder, ...]:
    """Read task rows with an app and assignee from a UTF-8 history export."""
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            first_line = handle.readline()
            handle.seek(0)
            reader = csv.DictReader(handle, delimiter=";" if first_line.count(";") > first_line.count(",") else ",")
            headers = reader.fieldnames or []
            columns = {header_key(value): value for value in headers if value is not None and header_key(value)}
            for key in _REQUIRED:
                if key not in columns:
                    raise InputError(f"File '{path}' thiếu cột '{_display_header(key)}'.")
            orders: list[HistoryOrder] = []
            for row in reader:
                if text_key(_value(row, columns, "loại")) != "task":
                    continue
                app = clean(_value(row, columns, "app name"))
                assignees = split_people(_value(row, columns, "người làm"))
                if not app or not assignees:
                    continue
                try:
                    created = parse_date(_value(row, columns, "ngày tạo"))
                except ValueError as error:
                    raise InputError(f"File '{path}', dòng {reader.line_num}, cột 'Ngày tạo': {error}") from error
                if created is None:
                    raise InputError(f"File '{path}', dòng {reader.line_num}, cột 'Ngày tạo' không được để trống.")
                orders.append(
                    HistoryOrder(
                        clean(_value(row, columns, "sprint")),
                        app,
                        clean(_value(row, columns, "task")),
                        assignees,
                        _hours(_value(row, columns, "ước lượng (h)")),
                        created,
                    )
                )
            return tuple(orders)
    except UnicodeDecodeError as error:
        raise InputError(f"File '{path}' không phải UTF-8.") from error
    except OSError as error:
        raise InputError(f"Không mở được file '{path}': {error}") from error


def _value(row: dict[str | None, str | None], columns: dict[str, str], key: str) -> object:
    return row.get(columns[key]) if key in columns else None


def _hours(value: object) -> float | None:
    text = clean(value)
    if not text:
        return None
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def _display_header(key: str) -> str:
    return {"app name": "App Name", "ngày tạo": "Ngày tạo", "người làm": "Người làm"}.get(key, key.title())
