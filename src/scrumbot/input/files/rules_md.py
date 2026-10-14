"""Read the TM rules file, a Markdown table, into TeamRule values (assignment spec §14). The only module that reads
the rules file."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from scrumbot.core.errors import InputError
from scrumbot.core.model import RuleKind, TeamRule
from scrumbot.core.normalize import clean, header_key, parse_date, text_key

_KINDS = {text_key(kind.value): kind for kind in RuleKind}
_DELIMITER = re.compile(r"^:?-+:?$")
_PIPE = re.compile(r"(?<!\\)\|")
_WHOLE = re.compile(r"[0-9]+")
_APP, _COUNT = "app", "số đơn"
_HEADERS = {_APP: "App", _COUNT: "Số đơn", "từ ngày": "Từ ngày", "đến ngày": "Đến ngày"}
# Which optional columns each kind needs (True) or must leave empty (False); others are free (spec §14.1, A33).
_USES = {
    RuleKind.PIN: {_APP: True, _COUNT: False},
    RuleKind.EXCLUDE: {_COUNT: False},
    RuleKind.MAX_ORDERS: {_APP: False, _COUNT: True},
    RuleKind.PREFER: {_APP: True, _COUNT: False},
}


def read_rules(path: Path) -> tuple[TeamRule, ...]:
    """Every row of every table whose header has `Loại` and `Dev`, in file order."""
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise InputError(f"Không đọc được file '{path}': {error}") from error
    rules: list[TeamRule] = []
    found = False
    for table in _tables(lines):
        (_, header), *rows = table
        columns = {header_key(cell): index for index, cell in enumerate(header)}
        if "loại" not in columns or "dev" not in columns:
            continue
        found = True
        for number, cells in rows:
            row = {key: cells[index] if index < len(cells) else "" for key, index in columns.items()}
            if any(row.values()):
                rules.append(_rule(path, number, row))
    if not found:
        raise InputError(f"File '{path}' không có bảng luật (bảng có cột Loại và Dev).")
    return tuple(rules)


def _tables(lines: list[str]) -> list[list[tuple[int, list[str]]]]:
    """Runs of `|` lines whose second line is a delimiter row, as (line number, cells); the delimiter is dropped.
    Lines inside a fenced code block are text, not a table, as Markdown renders them."""
    tables: list[list[tuple[int, list[str]]]] = []
    run: list[tuple[int, list[str]]] = []
    fence = ""
    for number, line in enumerate([*lines, ""], start=1):
        marker = line.strip()[:3]
        if marker in ("```", "~~~") and (not fence or marker == fence):
            fence = "" if fence else marker
            line = ""
        if not fence and line.strip().startswith("|"):
            run.append((number, _cells(line)))
            continue
        if len(run) >= 2 and run[1][1] and all(_DELIMITER.match(cell) for cell in run[1][1]):
            tables.append([run[0], *run[2:]])
        run = []
    return tables


def _cells(line: str) -> list[str]:
    text = line.strip()[1:]
    if text.endswith("|") and not text.endswith("\\|"):
        text = text[:-1]
    return [clean(part.replace("\\|", "|")).strip("`*").strip() for part in _PIPE.split(text)]


def _rule(path: Path, number: int, row: dict[str, str]) -> TeamRule:
    where = f"File '{path}', dòng {number}"
    kind = _KINDS.get(text_key(row["loại"]))
    if kind is None:
        raise InputError(
            f"{where}, cột 'Loại': '{row['loại']}' không hợp lệ; dùng Chỉ định, Không giao, Tối đa đơn hoặc Ưu tiên."
        )
    if not row["dev"]:
        raise InputError(f"{where}: thiếu Dev.")
    for key, needed in _USES[kind].items():
        if needed and not row.get(key):
            raise InputError(f"{where}: luật {kind.value} cần cột {_HEADERS[key]}.")
        if not needed and row.get(key):
            raise InputError(f"{where}: luật {kind.value} không dùng cột {_HEADERS[key]}.")
    count = row.get(_COUNT, "")
    if count and not (_WHOLE.fullmatch(count) and int(count) >= 1):
        raise InputError(f"{where}, cột 'Số đơn' phải là số nguyên từ 1 trở lên.")
    start, end = _day(where, row, "từ ngày"), _day(where, row, "đến ngày")
    if start is not None and end is not None and start > end:
        raise InputError(f"{where}: Từ ngày sau Đến ngày.")
    return TeamRule(
        kind=kind,
        dev=row["dev"],
        line=number,
        app=row.get(_APP, ""),
        max_orders=int(count) if count else None,
        start=start,
        end=end,
        note=row.get("ghi chú", ""),
    )


def _day(where: str, row: dict[str, str], key: str) -> date | None:
    try:
        return parse_date(row.get(key, ""))
    except ValueError as error:
        raise InputError(f"{where}, cột '{_HEADERS[key]}': {error}") from error
