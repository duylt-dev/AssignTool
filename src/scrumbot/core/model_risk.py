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
# "Nếu xảy ra" of bot spec §7.4: one fixed sentence per risk code, the same in every output.
IF_IT_HAPPENS = {
    "CAPACITY-DEV": "Chuyển đơn chưa bắt đầu sang dev còn trống giờ; không còn ai trống thì lùi hạn đơn ưu tiên thấp.",
    "CAPACITY-SPRINT": "Chốt với BA/MO các đơn đẩy sang sprint sau; giữ lại đơn urgent/high.",
    "SCOPE-ADDED": "Báo BA/MO dời hạn đơn mới hoặc tách bớt hạng mục sang sprint sau.",
    "CARRY-OVER": "Làm xong việc dở trước; đơn mới chưa bắt đầu thì chuyển cho người dự phòng.",
    "PIC-UNFAMILIAR": "Chuyển cho người dự phòng đã làm app, hoặc ghép người đó review code.",
    "PIC-ABSENT": "Chuyển đơn cho người dự phòng ngay; không còn ai thì đẩy sang sprint sau.",
    "DUE-AT-RISK": "Báo BA/MO lùi hạn hoặc cắt bớt hạng mục; cần thì thêm người hỗ trợ.",
    "STATUS-STUCK": "Gặp người làm để gỡ vướng; vướng ở khâu test hoặc phát hành thì báo người phụ trách khâu đó.",
    "QA-RETURNS": "Dừng gửi test; review code và tự test lại trước khi gửi QA lần nữa.",
}


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
