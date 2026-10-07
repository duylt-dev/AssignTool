"""Pure text, date and enum parsing shared by the readers and rules (A10, A13, A15). No I/O."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime

from assigntool.model import Level, Priority, SprintLabel

_SPACES = re.compile(r"\s+")
_SPRINT_LABEL = re.compile(r"Sprint\s+(\d+)\s*\(\s*(\d{1,2})/(\d{1,2})\s*-\s*(\d{1,2})/(\d{1,2})\s*\)", re.IGNORECASE)
_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:[ T].*)?$")
_DMY = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")

_LEVELS = {
    "junior": Level.JUNIOR,
    "junior+": Level.JUNIOR_PLUS,
    "middle": Level.MIDDLE,
    "middle+": Level.MIDDLE_PLUS,
    "senior": Level.SENIOR,
}
_PRIORITIES = {
    "": Priority.NORMAL,
    "urgent": Priority.URGENT,
    "high": Priority.HIGH,
    "normal": Priority.NORMAL,
    "low": Priority.LOW,
}


def clean(value: object) -> str:
    """NFC, trimmed, inner whitespace collapsed. None becomes ""."""
    if value is None:
        return ""
    return _SPACES.sub(" ", unicodedata.normalize("NFC", str(value))).strip()


def text_key(value: object) -> str:
    """Key for names and statuses: clean() then casefold (A10)."""
    return clean(value).casefold()


def app_key(value: object) -> str:
    """Key for "App Name": NFC, every whitespace removed, casefold (A10)."""
    return _SPACES.sub("", unicodedata.normalize("NFC", "" if value is None else str(value))).casefold()


def header_key(value: object) -> str:
    """Key for header cells: clean(), trailing "." removed, casefold (spec §3 rule 2)."""
    return clean(value).rstrip(".").strip().casefold()


def split_people(value: object) -> tuple[str, ...]:
    """ "A, B" -> ("A", "B"), each cleaned; empty parts dropped."""
    return tuple(p for p in (clean(part) for part in clean(value).split(",")) if p)


def parse_priority(value: object) -> Priority | None:
    """Empty means NORMAL; an unknown value returns None (PRIORITY-UNKNOWN)."""
    return _PRIORITIES.get(text_key(value))


def parse_level(value: object) -> Level | None:
    return _LEVELS.get(text_key(value))


def parse_date(value: object) -> date | None:
    """A datetime, a date, "YYYY-MM-DD" or "DD/MM/YYYY". Empty gives None; anything else raises ValueError."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = clean(value)
    if not text:
        return None
    if m := _ISO.match(text):
        return date(int(m[1]), int(m[2]), int(m[3]))
    if m := _DMY.match(text):
        return date(int(m[3]), int(m[2]), int(m[1]))
    raise ValueError(f"không đọc được ngày '{text}'")


def parse_sprint_labels(value: object, created: date) -> tuple[SprintLabel, ...]:
    """ "Sprint 18 (4/17 - 4/29), Sprint 19 (5/6 - 5/20)" -> two labels (A24).

    Labels carry month/day only: the start gets the year that puts it nearest to `created` (the day the order was
    filed), so a sprint across New Year is dated right. Text that is not a label is skipped.
    """
    labels: list[SprintLabel] = []
    for match in _SPRINT_LABEL.finditer(clean(value)):
        number, start_month, start_day, end_month, end_day = (int(part) for part in match.groups())
        starts = [day for year in (-1, 0, 1) if (day := _date(created.year + year, start_month, start_day))]
        if not starts:
            continue
        start = min(starts, key=lambda day: abs((day - created).days))
        end = _date(start.year, end_month, end_day)
        if end is not None and end < start:
            end = _date(start.year + 1, end_month, end_day)
        if end is not None:
            labels.append(SprintLabel(number, start, end, match[0]))
    return tuple(labels)


def _date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None
