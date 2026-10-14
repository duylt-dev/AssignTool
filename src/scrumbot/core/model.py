"""Value objects of the core (bot spec §8). No I/O here.

The system's sprints and items and the standard input are in `inputs.py`; risks in `model_risk.py`; the standard
outcome in `outcome.py`.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scrumbot.core.model_risk import Risk


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


class Placement(enum.Enum):
    """How the filed order met the sprint (bot spec §7.2)."""

    NEW = "new"
    BY_ID = "id"
    BY_TITLE = "title"


# The AI order types (bot spec §2.6) and their labels in every output.
ORDER_TYPES = {
    "ads": "Ads",
    "iap": "IAP",
    "flow_ui": "Luồng/UI",
    "policy": "Policy",
    "crash": "Crash",
    "sdk": "SDK",
    "feature": "Tính năng",
    "other": "Khác",
}


@dataclass(frozen=True, slots=True)
class Dev:
    """One dev of the team (assignment spec §4, bot spec §8.3)."""

    name: str  # full name as written in "Người làm", NFC-normalised
    code: str  # "Mã"
    level: Level
    active: bool  # "Nhận việc" == Y
    leave_days: tuple[date, ...] = ()


@dataclass(frozen=True, slots=True)
class SprintRow:
    """One numbered item of the sprint (bot spec §2.5): an order, or a subtask, or a bug. Text is NFC-normalised."""

    stt: int
    title: str
    kind: str  # "Task" (an order), "Subtask" or "Bug"
    app: str  # "" when empty
    assignees: tuple[str, ...]  # "Người làm"
    status: str  # status name; "" when empty
    priority_raw: str  # as written; "" when empty
    due: date | None
    created: date | None
    description: str  # only the filed order has one (D50, bot spec §7.2)
    hours: float | None = None  # `uoc_luong_gio`; never sizes an order of the sprint (D3)
    id: str = ""  # "" for a new order (bot spec §7.2)
    root_id: str = ""  # id of the nearest root order; the row's own id for a root
    status_kind: str = ""  # "open", "custom", "done", "closed"; "" when unknown
    updated: datetime | None = None
    closed: datetime | None = None


@dataclass(frozen=True, slots=True)
class SprintView:
    """One sprint as the rules see it (bot spec §2.5): its orders numbered by filing, then subtasks; bugs apart."""

    name: str  # "Sprint 10 (10/6 - 10/17)"
    number: int
    start: date | None  # the sprint's first day
    end: date | None
    rows: tuple[SprintRow, ...]
    id: str = ""
    bugs: tuple[SprintRow, ...] = ()  # bug items of the orders' trees; never orders
    changes: tuple[StatusChange, ...] = ()  # status history of the rows and bugs, oldest first


@dataclass(frozen=True, slots=True)
class StatusChange:
    """One status change of an item (bot spec §2.2, §8.3)."""

    task_id: str
    new: str  # the status entered
    at: datetime


@dataclass(frozen=True, slots=True)
class Order:
    """A row of kind "Task" with its parsed priority."""

    row: SprintRow
    priority: Priority


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderDraft:
    """The order being filed (bot spec §7.1, §8.3). Text is NFC-normalised; empty fields are ""/None."""

    title: str
    order_id: str = ""  # the order on the system; "" to match by title or file a new order (§7.2)
    app: str = ""
    priority_raw: str = ""
    due: date | None = None
    description: str = ""  # as written
    origin: str = ""  # where the order came from, e.g. the order file


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

    sprint: str  # quoted in reasons: the labels of its Maintain sprints, "" when none
    app: str
    title: str
    assignees: tuple[str, ...]
    hours: float | None  # `uoc_luong_gio`: an AI example only (A19)
    created: date
    sprints: tuple[SprintLabel, ...] = ()
    priority_raw: str = ""
    due: date | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class TeamRule:
    """One TM rule (assignment spec §14, bot spec §8.3). Text fields are NFC-normalised."""

    kind: RuleKind
    dev: str  # a dev code, as written
    line: int  # names the rule in messages and reasons: its line in the rules file
    app: str = ""  # "" = every app (EXCLUDE only)
    max_orders: int | None = None  # MAX_ORDERS only
    start: date | None = None  # None = no lower limit
    end: date | None = None  # None = no upper limit
    note: str = ""


@dataclass(frozen=True, slots=True)
class Finding:
    severity: Severity
    code: str  # spec §9
    where: str  # "Đơn STT 10", "LinhNV", …
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
    questions: tuple[str, ...] = ()  # AI questions to the person who filed the order (A90); never remembered


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


@dataclass(frozen=True, slots=True)
class DevSummary:
    """One active dev with the facts of the dev table of output.md (bot spec §7.4)."""

    dev: Dev
    carry_over: int
    leave_days: int  # leave days on working days of the sprint
    orders: int  # orders held, pre-assigned or proposed
    capacity: int | None = None  # hours left in the sprint (bot spec §4.1); None without sprint dates
    open_hours: int = 0  # hours left on the dev's open orders (bot spec §4.1)


@dataclass(frozen=True, slots=True)
class Result:
    sprint_name: str
    prev_sprint_name: str
    sizing_note: str  # e.g. "AI (gemini, 6/6 đơn)"
    assignments: tuple[Assignment, ...]  # in source STT order
    findings: tuple[Finding, ...]
    devs: tuple[DevSummary, ...]
    risks: tuple[Risk, ...] = ()  # bot spec §4, sorted
