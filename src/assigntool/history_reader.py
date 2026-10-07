"""Read the history export, list "Tech manager" (spec §5, D6), into HistoryOrder values: `.xlsx` or `.csv`."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from datetime import date
from pathlib import Path
from zipfile import BadZipFile

import openpyxl
from openpyxl.utils.exceptions import InvalidFileException

from assigntool.errors import InputError
from assigntool.model import HistoryOrder
from assigntool.normalize import clean, header_key, parse_date, parse_sprint_labels, split_people, text_key

_REQUIRED = ("ngày lên đơn", "tên task", "loại", "task cha", "app name", "người làm", "sprint")
_HEADER_NAMES = {
    "ngày lên đơn": "Ngày lên đơn",
    "tên task": "Tên task",
    "loại": "Loại",
    "task cha": "Task cha",
    "app name": "App Name",
    "người làm": "Người làm",
    "sprint": "Sprint",
    "due date": "Due date",
}


def read_history(path: Path) -> tuple[HistoryOrder, ...]:
    """Root orders ("Loại" = Task, empty "Task cha") of a Tech manager export; subtasks and bugs are skipped."""
    if path.suffix.lower() == ".csv":
        return _read_csv(path)
    return _read_xlsx(path)


def _read_csv(path: Path) -> tuple[HistoryOrder, ...]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            first_line = handle.readline()
            handle.seek(0)
            reader = csv.reader(handle, delimiter=";" if first_line.count(";") > first_line.count(",") else ",")
            columns = _columns(next(reader, []), f"File '{path}'")
            return tuple(
                order
                for record in reader
                if (order := _order(record, columns, f"File '{path}', dòng {reader.line_num}")) is not None
            )
    except UnicodeDecodeError as error:
        raise InputError(f"File '{path}' không phải UTF-8.") from error
    except OSError as error:
        raise InputError(f"Không mở được file '{path}': {error}") from error


def _read_xlsx(path: Path) -> tuple[HistoryOrder, ...]:
    """Every sheet whose row 1 has "Ngày lên đơn" is data (one per month); others, like "Tổng hợp", are skipped."""
    try:
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    except (BadZipFile, InvalidFileException, OSError) as error:
        raise InputError(f"Không mở được file '{path}': {error}") from error
    try:
        orders: list[HistoryOrder] = []
        data_sheets = 0
        for worksheet in workbook.worksheets:
            rows = worksheet.iter_rows(values_only=True)
            header = next(rows, ())
            if "ngày lên đơn" not in {header_key(value) for value in header}:
                continue
            data_sheets += 1
            where = f"File '{path}', sheet '{worksheet.title}'"
            columns = _columns(header, where)
            for number, record in enumerate(rows, start=2):
                if (order := _order(record, columns, f"{where}, dòng {number}")) is not None:
                    orders.append(order)
        if not data_sheets:
            raise InputError(f"File '{path}' không có sheet nào có cột 'Ngày lên đơn'.")
        return tuple(orders)
    finally:
        workbook.close()


def _columns(header: Iterable[object], where: str) -> dict[str, int]:
    columns: dict[str, int] = {}
    for index, value in enumerate(header):
        columns.setdefault(header_key(value), index)
    for key in _REQUIRED:
        if key not in columns:
            raise InputError(f"{where} thiếu cột '{_HEADER_NAMES[key]}'.")
    return columns


def _order(record: Sequence[object], columns: dict[str, int], where: str) -> HistoryOrder | None:
    def cell(key: str) -> object:
        index = columns.get(key)
        return record[index] if index is not None and index < len(record) else None

    if text_key(cell("loại")) != "task" or clean(cell("task cha")):
        return None
    created = _date(cell("ngày lên đơn"), where, "ngày lên đơn")
    if created is None:
        raise InputError(f"{where}, cột 'Ngày lên đơn' không được để trống.")
    sprint = clean(cell("sprint"))
    return HistoryOrder(
        sprint,
        clean(cell("app name")),
        clean(cell("tên task")),
        split_people(cell("người làm")),
        _hours(cell("ước lượng (h)")),
        created,
        parse_sprint_labels(sprint, created),
        clean(cell("ưu tiên")),
        _date(cell("due date"), where, "due date"),
    )


def _date(value: object, where: str, key: str) -> date | None:
    try:
        return parse_date(value)
    except ValueError as error:
        raise InputError(f"{where}, cột '{_HEADER_NAMES[key]}': {error}") from error


def _hours(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = clean(value)
    if not text:
        return None
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None
