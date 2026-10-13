"""Value objects for the risk register, the change log and the memory between runs (bot spec §4–§5).
No I/O here."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date, datetime


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
