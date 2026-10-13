"""Value objects for the risk register, the change log, the memory between runs and the replay (bot spec §4–§9).
No I/O here."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date, datetime

from scrumbot.model import Assignment, Order, SprintLabel


class RiskLevel(enum.IntEnum):
    """Smaller sorts first."""

    HIGH = 0
    MEDIUM = 1
    LOW = 2


LEVEL_TEXT = {RiskLevel.HIGH: "Cao", RiskLevel.MEDIUM: "Trung bình", RiskLevel.LOW: "Thấp"}


class RiskGroup(enum.Enum):
    CAPACITY = "Năng lực"
    ASSIGNMENT = "Phân công"
    PROGRESS = "Tiến độ"
    QUALITY = "Chất lượng"
    CHANGE = "Thay đổi"


@dataclass(frozen=True, slots=True)
class Risk:
    """One row of the "Rủi ro" sheet (bot spec §4)."""

    level: RiskLevel
    code: str
    group: RiskGroup
    where: str  # "Đơn STT 3", "LinhNV", or the sprint label
    problem: str
    impact: str
    action: str
    owner: str
    due: date | None
    stt: int | None = None  # the order an order risk is about
    covers: tuple[int, ...] = ()  # STTs of the orders the risk covers (bot spec §4.3)


class ChangeKind(enum.Enum):
    """`Loại` of the "Thay đổi" sheet (bot spec §5.3); the value is the Vietnamese label."""

    NEW = "Đơn mới"
    REMOVED = "Đơn bị bỏ"
    PRIORITY = "Đổi ưu tiên"
    DUE = "Đổi hạn"
    TITLE = "Đổi tên"
    TM_ASSIGNED = "TM đã giao"
    PEOPLE = "Đổi người làm"


@dataclass(frozen=True, slots=True)
class Change:
    kind: ChangeKind
    order: str  # "STT <n> · <title>"
    before: str
    after: str


@dataclass(frozen=True, slots=True)
class OrderMark:
    """What the memory stored about one order at the end of a run (bot spec §5.1)."""

    id: str
    title: str
    priority_raw: str
    due: date | None
    codes: tuple[str, ...]  # pool codes in "Người làm"


@dataclass(frozen=True, slots=True)
class KeptProposal:
    """A proposal remembered between runs (A66)."""

    order_id: str
    code: str
    reason: str
    backups: tuple[str, ...]
    at: datetime


@dataclass(frozen=True, slots=True)
class Outcome:
    """The TM gave a `Người làm` to an order the bot had proposed (bot spec §5.2)."""

    order_id: str
    title: str
    proposed: str
    actual: tuple[str, ...]  # pool codes now
    at: datetime

    @property
    def matched(self) -> bool:
        return self.proposed in self.actual


@dataclass(frozen=True, slots=True)
class ReplayOrder:
    """One compared order of the assignment replay (bot spec §8.1)."""

    order: Order
    tm_codes: tuple[str, ...]  # pool devs the TM named
    assignment: Assignment  # the bot's choice, made without the TM's names

    @property
    def matched(self) -> bool:
        return self.assignment.pic_codes[0] in self.tm_codes


@dataclass(frozen=True, slots=True)
class ReplaySprint:
    label: SprintLabel
    pool: tuple[str, ...]  # codes of the devs in the pool for this sprint
    orders: tuple[ReplayOrder, ...]  # compared orders, in the order they were assigned
    kept: int  # carried orders, kept as the TM assigned them


@dataclass(frozen=True, slots=True)
class Checkpoint:
    """The register the bot would have written at one checkpoint of a past sprint (bot spec §8.2)."""

    at: datetime
    risks: tuple[Risk, ...]


@dataclass(frozen=True, slots=True)
class OrderOutcome:
    """The real outcome of one root order with a pool dev, and the risks that covered it in time."""

    order: Order
    tm_codes: tuple[str, ...]
    reasons: tuple[str, ...]  # why the outcome is bad; empty when good
    flagged: tuple[tuple[str, date], ...]  # (code, first checkpoint day) at level Cao or Trung bình

    @property
    def bad(self) -> bool:
        return bool(self.reasons)


@dataclass(frozen=True, slots=True)
class RiskSprint:
    label: SprintLabel
    has_history: bool  # at least one root order has status history
    checkpoints: tuple[Checkpoint, ...]
    outcomes: tuple[OrderOutcome, ...]


@dataclass(frozen=True, slots=True)
class CodeScore:
    """One row of "Rủi ro theo loại" (bot spec §8.2)."""

    code: str
    flagged: int  # covered orders
    flagged_bad: int  # covered orders with a bad outcome
    bad: int  # orders with a bad outcome
    bad_flagged: int  # bad orders covered before the end
    lead_median: float | None  # working days
