"""The standard outcome of the core (bot spec §8.4): what one `review` or one `assign` decided about the filed order.
Every output adapter reads an `Outcome`. No I/O here."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date, datetime

from scrumbot.core.codec import to_plain
from scrumbot.core.model import ORDER_TYPES, Assignment, Finding, Level, Placement, SizeEstimate
from scrumbot.core.model_risk import IF_IT_HAPPENS, LEVEL_TEXT, Risk

FORMAT = "scrumbot-outcome/2"


class Status(enum.Enum):
    NOT_READY = "not_ready"  # review: a check blocks (bot spec §7.3)
    READY = "ready"  # review: nothing blocks; `assign` may run
    PROPOSED = "proposed"  # assign: the bot proposes a PIC
    PRE_ASSIGNED = "pre_assigned"  # review or assign: the order has a `Người làm` and is kept (D10)


@dataclass(frozen=True, slots=True)
class ReviewItem:
    """One blocking item of the review (bot spec §7.3)."""

    code: str
    message: str  # Vietnamese, exactly as bot spec §7.3


@dataclass(frozen=True, slots=True)
class Questions:
    """The AI's questions to the person who filed the order (bot spec §7.3, A102); they never block."""

    items: tuple[str, ...] = ()  # at most 2
    answered: bool = False  # the AI answered, even with no question
    note: str = ""  # "AI (agy)", "tắt AI", or why the call failed


@dataclass(frozen=True, slots=True)
class DevLine:
    """One row of the dev table (bot spec §7.4)."""

    code: str
    level: Level
    familiarity: str
    orders: int
    open_hours: int
    capacity: int | None
    carry_over: int
    leave_days: int
    role: str


@dataclass(frozen=True, slots=True)
class SprintRef:
    id: str
    name: str  # "Sprint 10 (10/6 - 10/17)"
    start: date | None
    end: date | None
    previous: str  # the previous sprint's name (bot spec §2.3); "sprint trước" without one


@dataclass(frozen=True, slots=True)
class OrderRef:
    """The filed order as placed in the sprint (bot spec §7.2)."""

    title: str
    stt: int
    id: str  # "" for a new order
    placement: Placement
    origin: str
    app: str
    priority_raw: str
    due: date | None
    description: str  # as the AI read it
    fingerprint: str  # the order as placed; `assign` needs a passed review of it (bot spec §7.4, A101)


@dataclass(frozen=True, slots=True)
class RiskCounts:
    high: int = 0
    medium: int = 0
    low: int = 0


@dataclass(frozen=True)
class Outcome:
    status: Status
    run_at: datetime
    source: str
    freshness: datetime | None  # the newest update read (D49)
    sprint: SprintRef
    order: OrderRef
    review: tuple[ReviewItem, ...] = ()  # blocking items; empty unless NOT_READY
    questions: Questions | None = None  # review only, when READY
    assignment: Assignment | None = None  # assign only
    sizing_note: str = ""  # e.g. "AI (agy, 6/6 đơn; 5 từ bộ nhớ)"
    risks: tuple[Risk, ...] = ()  # of this order, of its PIC and of the sprint, in register order
    sprint_risks: RiskCounts = RiskCounts()  # over the whole register
    devs: tuple[DevLine, ...] = ()
    findings: tuple[Finding, ...] = ()  # every finding except those about another order

    def to_dict(self) -> dict[str, object]:
        """The JSON form (bot spec §8.4)."""
        item = self.assignment
        return {
            "format": FORMAT,
            "status": self.status.value,
            "run_at": to_plain(self.run_at),
            "source": self.source,
            "freshness": to_plain(self.freshness),
            "sprint": to_plain(self.sprint),
            "order": to_plain(self.order),
            "review": to_plain(self.review),
            "questions": to_plain(self.questions),
            "assignment": None if item is None else _assignment(item),
            "size": None if item is None else _size(item.size, self.sizing_note),
            "risks": [_risk(risk) for risk in self.risks],
            "sprint_risks": to_plain(self.sprint_risks),
            "devs": to_plain(self.devs),
            "findings": to_plain(self.findings),
        }


def _assignment(item: Assignment) -> dict[str, object]:
    return {
        "pic_codes": list(item.pic_codes),
        "pic_names": list(item.pic_names),
        "reason": item.reason,
        "backups": list(item.backups),
        "rule_lines": list(item.rule_lines),
        "rules_relaxed": item.rules_relaxed,
    }


def _size(size: SizeEstimate, note: str) -> dict[str, object]:
    return {
        "size": size.size.name,
        "hours": size.size.value,
        "is_default": size.is_default,
        "reason": size.reason,
        "kind": size.kind,
        "kind_label": ORDER_TYPES.get(size.kind, ""),
        "items": list(size.items),
        "tech_risks": list(size.tech_risks),
        "remembered": size.remembered,
        "note": note,
    }


def _risk(risk: Risk) -> dict[str, object]:
    return {
        "level": to_plain(risk.level),
        "level_text": LEVEL_TEXT[risk.level],
        "code": risk.code,
        "group": risk.group.value,
        "where": risk.where,
        "problem": risk.problem,
        "impact": risk.impact,
        "action": risk.action,
        "if_it_happens": IF_IT_HAPPENS.get(risk.code, ""),
        "owner": risk.owner,
        "due": to_plain(risk.due),
        "stt": risk.stt,
    }
