"""The JSON form of the standard formats (bot spec §8.3, §8.4): dataclasses to plain values and back, driven by their
type hints, so the JSON field names are the Python field names. Pure."""

from __future__ import annotations

import dataclasses
import enum
import types
import typing
import unicodedata
from collections.abc import Mapping
from datetime import date, datetime

from scrumbot.core.errors import InputError
from scrumbot.core.model import Level
from scrumbot.core.normalize import LEVEL_NAMES, text_key

INVALID = "Dữ liệu đầu vào không đúng dạng"
_KINDS = {
    str: "chữ",
    bool: "đúng/sai",
    int: "số nguyên",
    float: "số",
    date: "ngày YYYY-MM-DD",
    datetime: "thời điểm YYYY-MM-DDTHH:MM:SS",
}


def to_plain(value: object) -> object:
    """A dataclass, enum, date, mapping or tuple as JSON values; every field is written, None as null."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {field.name: to_plain(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, enum.Enum):
        return enum_text(value)
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): to_plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [to_plain(item) for item in value]
    return value


def enum_text(member: enum.Enum) -> str:
    """A level as devs.xlsx writes it (`junior+`); any other member by its value, or its lowercase name."""
    if isinstance(member, Level):
        return LEVEL_NAMES[member]
    return member.value if isinstance(member.value, str) else member.name.lower()


def from_plain(kind: object, value: object, path: str) -> object:
    """`value` read as `kind`. A field with a default may be absent or null; text is NFC-normalised."""
    origin = typing.get_origin(kind)
    if origin in (types.UnionType, typing.Union):
        if value is None:
            return None
        (inner,) = (arg for arg in typing.get_args(kind) if arg is not type(None))
        return from_plain(inner, value, path)
    if dataclasses.is_dataclass(kind) and isinstance(kind, type):
        return _record(kind, value, path)
    if origin is tuple:
        if not isinstance(value, list):
            raise invalid(path, "không phải danh sách")
        inner = typing.get_args(kind)[0]
        return tuple(from_plain(inner, item, f"{path}[{index}]") for index, item in enumerate(value))
    if origin is Mapping:
        if not isinstance(value, dict):
            raise invalid(path, "không phải bảng")
        inner = typing.get_args(kind)[1]
        return {str(key): from_plain(inner, item, f"{path}[{key}]") for key, item in value.items()}
    if isinstance(kind, type) and issubclass(kind, enum.Enum):
        return _member(kind, value, path)
    return _scalar(kind, value, path)


def invalid(path: str, problem: str) -> InputError:
    return InputError(f"{INVALID}: {path}: {problem}." if path else f"{INVALID}: {problem}.")


def _record(kind: type, value: object, path: str) -> object:
    if not isinstance(value, dict):
        raise invalid(path, "không phải bảng")
    hints = typing.get_type_hints(kind)
    values: dict[str, object] = {}
    for field in dataclasses.fields(kind):
        where = f"{path}.{field.name}" if path else field.name
        raw = value.get(field.name)
        if raw is None:
            if field.default is dataclasses.MISSING and field.default_factory is dataclasses.MISSING:
                raise invalid(where, "thiếu")
            continue
        values[field.name] = from_plain(hints[field.name], raw, where)
    return kind(**values)


def _member(kind: type[enum.Enum], value: object, path: str) -> enum.Enum:
    members = {text_key(enum_text(member)): member for member in kind}
    found = members.get(text_key(value)) if isinstance(value, str) else None
    if found is None:
        raise invalid(path, f"'{value}' không hợp lệ")
    return found


def _scalar(kind: object, value: object, path: str) -> object:
    if kind is str and isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if kind is bool and isinstance(value, bool):
        return value
    if kind is int and isinstance(value, int) and not isinstance(value, bool):
        return value
    if kind is float and isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if kind in (date, datetime) and isinstance(value, str):
        try:
            moment = datetime.fromisoformat(value)
        except ValueError:
            moment = None
        if moment is not None and (kind is datetime or len(value) == len("YYYY-MM-DD")):
            return moment if kind is datetime else moment.date()
    if kind not in _KINDS:
        raise TypeError(f"no JSON form for {kind!r}")
    raise invalid(path, f"không phải {_KINDS[kind]}")
