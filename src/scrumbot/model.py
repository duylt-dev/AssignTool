"""Core value objects shared by sources, rules and actions (LLM.md §2). No I/O here.

API items live in `model_board.py`; risks and changes in `model_risk.py`.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scrumbot.model_risk import Change, Risk


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


class RuleKind(enum.Enum):
    """The four kinds of TM rule (spec §14, D30); the value is the `Loại` cell."""

    PIN = "Chỉ định"
    EXCLUDE = "Không giao"
    MAX_ORDERS = "Tối đa đơn"
    PREFER = "Ưu tiên"


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
    """One row of the target sprint, built from the API (assignment spec §3, bot spec §2.5). Text is NFC-normalised."""

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
    hours: float | None = None  # "Ước lượng (h)" (`uoc_luong_gio`); never sizes a target order (D3)
    # Filled by the API source only (bot spec §2.5); file rows keep the defaults.
    id: str = ""
    root_id: str = ""  # id of the nearest root order; the row's own id for a root
    status_kind: str = ""  # "open", "custom", "done", "closed"; "" when unknown
    created_at: datetime | None = None
    updated: datetime | None = None
    closed: datetime | None = None  # "ngay_dong"


@dataclass(frozen=True, slots=True)
class SprintSheet:
    name: str  # "Sprint 10"
    number: int
    start: date | None  # the sprint's first day
    end: date | None
    headers: tuple[str, ...]  # original header texts, in column order
    rows: tuple[SprintRow, ...]
    # Filled by the API source only (bot spec §2.5).
    id: str = ""
    bugs: tuple[SprintRow, ...] = ()  # bug items of the orders' trees; never orders
    changes: tuple[StatusChange, ...] = ()  # status history of the rows and bugs, oldest first


@dataclass(frozen=True, slots=True)
class StatusChange:
    """One status change of an item, from `/api/doc/lich-su` (bot spec §2.2)."""

    task_id: str
    old: str  # "" when the item was created
    new: str
    at: datetime


@dataclass(frozen=True, slots=True)
class Order:
    """A target-sprint row with "Loại" = "Task" and its parsed priority."""

    row: SprintRow
    priority: Priority


@dataclass(frozen=True, slots=True)
class SprintLabel:
    """One sprint an order belongs to, e.g. "Sprint 10 (10/6 - 10/17)" (assignment spec §5, A24).

    Two labels are the same sprint when number, start and end agree: "Sprint 1" exists on two boards with the same
    start date (A21).
    """

    number: int
    start: date
    end: date
    name: str = field(default="", compare=False)  # the label as written


@dataclass(frozen=True, slots=True)
class HistoryOrder:
    """One root order of the history (assignment spec §5)."""

    sprint: str  # quoted in reasons: the "Sprint" cell as written ("" when empty), or the sheet name
    app: str
    title: str
    assignees: tuple[str, ...]
    hours: float | None  # "Ước lượng (h)", when the file has it
    created: date  # "Ngày lên đơn" / "Ngày tạo"
    sprints: tuple[SprintLabel, ...] = ()  # parsed from `sprint`; empty for sheet history
    priority_raw: str = ""  # "Ưu tiên" as written
    due: date | None = None  # "Due date"


@dataclass(frozen=True, slots=True)
class TeamRule:
    """One row of the TM rules file (spec §14). Text fields are NFC-normalised."""

    kind: RuleKind
    dev: str  # "Dev": a "Mã" of devs.xlsx, as written
    app: str  # "" = every app (EXCLUDE only)
    max_orders: int | None  # "Số đơn"; MAX_ORDERS only
    start: date | None  # "Từ ngày"; None = no lower limit
    end: date | None  # "Đến ngày"; None = no upper limit
    note: str  # "Ghi chú"
    line: int  # line number in the file, quoted in messages and reasons


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
    kind: str = ""  # AI order type (bot spec §2.6): ads, iap, flow_ui, policy, crash, sdk, feature, other
    items: tuple[str, ...] = ()  # AI work items
    tech_risks: tuple[str, ...] = ()  # AI technical risks; shown, never scored (A79)
    remembered: bool = False  # taken from the memory of A67 instead of this run's AI call


@dataclass(frozen=True, slots=True)
class Assignment:
    order: Order
    size: SizeEstimate
    source: Source
    pic_names: tuple[str, ...]  # PREASSIGNED: the original "Người làm"; PROPOSED: the PIC's name
    pic_codes: tuple[str, ...]  # codes of the pool devs among pic_names
    reason: str  # spec §8
    backups: tuple[str, ...]  # codes, at most 2; empty for PREASSIGNED
    rule_lines: tuple[int, ...] = ()  # lines of the TM rules that shaped the choice
    rules_relaxed: bool = False  # the rules left no candidate, so EXCLUDE and MAX_ORDERS were ignored (A31)
    kept: bool = False  # a proposal remembered from an earlier run (A66)


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
    capacity: int | None = None  # hours left in the sprint (bot spec §4.1); None without sprint dates
    open_hours: int = 0  # size hours of the dev's open orders


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
    risks: tuple[Risk, ...] = ()  # bot spec §4, sorted
    changes: tuple[Change, ...] = ()  # bot spec §5.3
    change_note: str = ""  # first row of the "Thay đổi" sheet
    summary: tuple[tuple[str, str], ...] = ()  # rows of the "Tóm tắt" sheet, filled by the flow (bot spec §6)
