"""Value objects for the risk register (bot spec §4). No I/O here."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date


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


@dataclass(frozen=True, slots=True)
class Risk:
    """One risk of the register (bot spec §4)."""

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
