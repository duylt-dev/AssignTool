"""Value objects shared by readers, rules and the report (LLM.md §2). No I/O here."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date


class Level(enum.IntEnum):
    JUNIOR = 0
    JUNIOR_PLUS = 1
    MIDDLE = 2
    MIDDLE_PLUS = 3
    SENIOR = 4


class Priority(enum.IntEnum):
    """Smaller sorts first (A5)."""

    URGENT = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


class Size(enum.IntEnum):
    """Order size class; the value is the hours it weighs in load (spec §6.4, A7)."""

    S = 4
    M = 16
    L = 32
    XL = 64


class Severity(enum.Enum):
    WARN = "WARN"
    INFO = "INFO"


class Source(enum.Enum):
    PREASSIGNED = "Đã giao sẵn"
    PROPOSED = "Tool đề xuất"


@dataclass(frozen=True, slots=True)
class Dev:
    """One row of devs.xlsx (spec §4)."""

    name: str  # full name as written in "Người làm", NFC-normalised
    code: str  # "Mã"
    level: Level
    active: bool  # "Nhận việc" == Y
    leave_days: tuple[date, ...]


@dataclass(frozen=True, slots=True)
class SprintRow:
    """One data row of a sprint sheet (spec §3). Text fields are NFC-normalised; missing columns give defaults."""

    stt: int
    title: str  # leading spaces and "└ " removed
    kind: str  # "Loại" as written: "Task", "Subtask" or anything else
    app: str  # "" when empty
    assignees: tuple[str, ...]  # "Người làm" split on ","
    status: str  # "Trạng thái"
    priority_raw: str  # "Ưu tiên" as written; "" when empty
    due: date | None
    created: date | None
    description: str  # "Mô tả"
    cells: tuple[object, ...]  # every original cell value, in the sheet's column order (for the report)
    hours: float | None = None  # "Ước lượng (h)"; read only for history built from older sheets (spec §5)


@dataclass(frozen=True, slots=True)
class SprintSheet:
    name: str  # "Sprint 10"
    number: int
    start: date | None  # from row 3 (spec §3 rule 4)
    end: date | None
    headers: tuple[str, ...]  # original header texts, in column order
    rows: tuple[SprintRow, ...]


@dataclass(frozen=True, slots=True)
class Order:
    """A target-sprint row with "Loại" = "Task" and its parsed priority."""

    row: SprintRow
    priority: Priority


@dataclass(frozen=True, slots=True)
class HistoryOrder:
    """One "Loại" = "Task" row of the history CSV (spec §5)."""

    sprint: str
    app: str
    title: str
    assignees: tuple[str, ...]
    hours: float | None  # "Ước lượng (h)"
    created: date


@dataclass(frozen=True, slots=True)
class Finding:
    severity: Severity
    code: str  # spec §9
    where: str  # "Đơn STT 10", "Sheet Sprint 9", "LinhNV", …
    message: str  # Vietnamese, exactly as spec §9


@dataclass(frozen=True, slots=True)
class SizeEstimate:
    size: Size
    reason: str  # the AI's reason; "" for a default
    is_default: bool


@dataclass(frozen=True, slots=True)
class Assignment:
    order: Order
    size: SizeEstimate
    source: Source
    pic_names: tuple[str, ...]  # PREASSIGNED: the original "Người làm"; PROPOSED: the PIC's name
    pic_codes: tuple[str, ...]  # codes of the pool devs among pic_names
    reason: str  # spec §8
    backups: tuple[str, ...]  # codes, at most 2; empty for PREASSIGNED


@dataclass(frozen=True, slots=True)
class DevSummary:
    """One row of the "Tải dev" sheet (spec §10)."""

    dev: Dev
    carry_over: int
    leave_days: int  # leave days on working days of the sprint
    on_leave_all_sprint: bool
    preassigned: int
    proposed: int
    hours: int
    orders: tuple[str, ...]  # "<title> [<size>]"
    known_apps: tuple[str, ...]  # apps where the dev has familiarity rank 0 or 1


@dataclass(frozen=True, slots=True)
class AiReply:
    """What ai_cli returns: either the model's reply text or a short Vietnamese failure reason."""

    tool: str  # "gemini" or "agy"
    text: str | None
    failure: str | None


@dataclass(frozen=True, slots=True)
class Result:
    sheet_name: str
    prev_sheet_name: str
    sizing_note: str  # terminal line of spec §11, e.g. "AI (gemini, 6/6 đơn)"
    assignments: tuple[Assignment, ...]  # in source STT order
    findings: tuple[Finding, ...]
    devs: tuple[DevSummary, ...]
