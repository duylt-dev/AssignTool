"""What the report of the filed order shows (bot spec §7.4): its assignment, the risks of the order, of its PIC and
of the sprint, the dev table and the findings. Pure."""

from __future__ import annotations

from dataclasses import dataclass

from scrumbot.core.assign.familiarity import FamiliarityIndex
from scrumbot.core.assign.pipeline import Team
from scrumbot.core.model import Assignment, Dev, Finding, HistoryOrder, Placement, Result, Source
from scrumbot.core.model_risk import Risk
from scrumbot.core.normalize import app_key
from scrumbot.core.outcome import DevLine
from scrumbot.core.sprint.new_order import PlacedOrder


@dataclass(frozen=True, slots=True)
class OrderReport:
    item: Assignment
    how: Placement
    risks: tuple[Risk, ...]  # of the order, of its PIC and of the sprint
    devs: tuple[DevLine, ...]
    findings: tuple[Finding, ...]  # every finding not about another order


def order_report(result: Result, placed: PlacedOrder, team: Team, history: tuple[HistoryOrder, ...]) -> OrderReport:
    """What the order report shows (bot spec §7.4)."""
    item = next(entry for entry in result.assignments if entry.order.row.stt == placed.stt)
    codes = set(item.pic_codes)
    risks = tuple(
        risk
        for risk in result.risks
        if risk.stt == placed.stt or (risk.stt is None and (risk.where in codes or risk.where == result.sprint_name))
    )
    app = item.order.row.app
    fam = FamiliarityIndex.build(history, team.pool)
    roles = {code: "Dự phòng " + str(number) for number, code in enumerate(item.backups, start=1)}
    roles.update({code: "PIC" if item.source is Source.PROPOSED else "Người làm" for code in item.pic_codes})
    roles.update({dev.code: "Nghỉ hết các ngày còn lại" for dev in team.off_rest})
    roles.update({dev.code: "Nghỉ cả sprint" for dev in team.removed})
    devs = tuple(
        DevLine(
            summary.dev.code,
            summary.dev.level,
            _familiarity(fam, summary.dev, app),
            summary.orders,
            summary.open_hours,
            summary.capacity,
            summary.carry_over,
            summary.leave_days,
            roles.get(summary.dev.code, ""),
        )
        for summary in result.devs
    )
    others = {f"Đơn STT {entry.order.row.stt}" for entry in result.assignments if entry.order.row.stt != placed.stt}
    findings = tuple(finding for finding in result.findings if finding.where not in others)
    return OrderReport(item, placed.how, risks, devs, findings)


def _familiarity(fam: FamiliarityIndex, dev: Dev, app: str) -> str:
    if not app_key(app):
        return "—"
    found = fam.get(dev, app)
    if found.rank == 0:
        return "Làm version gần nhất"
    if found.rank == 1:
        return f"Từng làm ({found.versions} version)"
    return "Chưa làm"
