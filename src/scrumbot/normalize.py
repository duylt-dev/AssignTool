"""Pure text, date and enum parsing shared by the readers and rules (A10, A13, A15). No I/O."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime

from scrumbot.model import Level, Priority

_SPACES = re.compile(r"\s+")
_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:[ T].*)?$")
_DMY = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")

_LEVELS = {
    "junior": Level.JUNIOR,
    "junior+": Level.JUNIOR_PLUS,
    "middle": Level.MIDDLE,
    "middle+": Level.MIDDLE_PLUS,
    "senior": Level.SENIOR,
}
LEVEL_NAMES = {level: name for name, level in _LEVELS.items()}  # Level → the text of devs.xlsx
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
    """Key for header cells: clean(), trailing "." removed, casefold (assignment spec §4)."""
    return clean(value).rstrip(".").strip().casefold()


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
