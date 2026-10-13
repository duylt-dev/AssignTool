"""Assignment risks (bot spec §4.2): PIC-UNFAMILIAR and PIC-ABSENT, and the suggestion every risk shares: what §7
itself would pick if the order were empty. Pure."""

from __future__ import annotations

from dataclasses import replace

from scrumbot.model import Assignment, Dev, Order, SizeEstimate, Source, TeamRule
from scrumbot.model_risk import Risk, RiskGroup, RiskLevel
from scrumbot.normalize import text_key
from scrumbot.rules.assign import assign
from scrumbot.rules.familiarity import FamiliarityIndex
from scrumbot.rules.reasons import familiarity_text
from scrumbot.rules.risk_register import (
    URGENT,
    RiskContext,
    Suggest,
    escalate,
    is_open,
    make,
    order_where,
    pic_codes,
)


def suggester(
    orders: tuple[Order, ...],
    assignments: tuple[Assignment, ...],
    sizes: dict[int, SizeEstimate],
    pool: tuple[Dev, ...],
    fam: FamiliarityIndex,
    carry: dict[str, int],
    leave: dict[str, int],
    prev_name: str,
    rules: tuple[TeamRule, ...],
) -> Suggest:
    """The suggestion of bot spec §4.1: §7 run again with the order emptied, every other order keeping its PIC, and
    some devs left out. Re-using assign() keeps one rule; a separate ranking would drift from it."""
    current = {item.order.row.stt: item for item in assignments}

    def suggest(stt: int, left_out: frozenset[str]) -> Assignment | None:
        candidates = tuple(dev for dev in pool if dev.code not in left_out)
        if not candidates or stt not in current:
            return None
        rebuilt = []
        for order in orders:
            item = current.get(order.row.stt)
            if order.row.stt == stt:
                rebuilt.append(replace(order, row=replace(order.row, assignees=())))
            elif item is not None and item.source is Source.PROPOSED:
                rebuilt.append(replace(order, row=replace(order.row, assignees=item.pic_names)))
            else:
                rebuilt.append(order)
        chosen = assign(tuple(rebuilt), sizes, candidates, fam, carry, leave, prev_name, rules)
        return next(item for item in chosen if item.order.row.stt == stt)

    return suggest


def unfamiliar_risks(context: RiskContext) -> tuple[Risk, ...]:
    """PIC-UNFAMILIAR: an open urgent/high order whose every PIC dev has never worked on its app (D45 risk 5)."""
    risks: list[Risk] = []
    for item in context.assignments:
        row, priority = item.order.row, item.order.priority
        if priority not in URGENT or not row.app or not is_open(row):
            continue
        codes = pic_codes(item, context.active)
        devs = [dev for dev in context.active if dev.code in codes]
        if not devs or any(context.fam.get(dev, row.app).rank < 2 for dev in devs):
            continue
        helpers = sorted(
            (dev for dev in context.pool if dev.code not in codes and context.fam.get(dev, row.app).rank < 2),
            key=lambda dev: (context.fam.get(dev, row.app).rank, -dev.level, dev.code),
        )
        if helpers and not context.fam.is_new_app(row.app):
            helper = helpers[0]
            action = (
                f"Nhờ {helper.code} ({familiarity_text(row.app, context.fam.get(helper, row.app))}) hỗ trợ khởi động"
            )
        else:
            action = "App mới với team: tính thêm thời gian tìm hiểu."
        who = ", ".join(codes)
        risks.append(
            make(
                context,
                escalate(RiskLevel.LOW, priority),
                "PIC-UNFAMILIAR",
                RiskGroup.ASSIGNMENT,
                order_where(row.stt),
                f"Đơn STT {row.stt} ({priority.name.lower()}) giao cho {who} nhưng {who} chưa làm {row.app}",
                "PIC mất thêm thời gian tìm hiểu app trên một đơn gấp.",
                action,
                "TM",
                stt=row.stt,
                covers=(row.stt,),
            )
        )
    return tuple(risks)


def absent_risks(context: RiskContext) -> tuple[Risk, ...]:
    """PIC-ABSENT: an open order whose pool devs are all off every remaining day (D45 risk 6)."""
    if not context.rest:
        return ()
    working = {text_key(dev.name) for dev in context.pool}
    risks: list[Risk] = []
    for item in context.assignments:
        row = item.order.row
        if item.source is not Source.PREASSIGNED or not is_open(row):
            continue
        people = {text_key(name) for name in row.assignees}
        off = [dev for dev in context.active if text_key(dev.name) in people and dev not in context.pool]
        if not off or people & working:
            continue
        who = ", ".join(dev.code for dev in off)
        suggestion = context.suggest(row.stt, frozenset(dev.code for dev in off))
        action = (
            f"Chuyển cho {suggestion.pic_codes[0]}: {suggestion.reason}"
            if suggestion is not None
            else "Không còn dev trong team; cân nhắc người ngoài team hoặc đẩy sang sprint sau."
        )
        risks.append(
            make(
                context,
                RiskLevel.HIGH,
                "PIC-ABSENT",
                RiskGroup.ASSIGNMENT,
                order_where(row.stt),
                f"Đơn STT {row.stt} giao cho {who} nhưng {who} nghỉ các ngày còn lại của sprint "
                f"(từ {context.base:%d/%m/%Y})",
                "Đơn không có ai làm tới hết sprint.",
                action,
                "TM",
                stt=row.stt,
                covers=(row.stt,),
            )
        )
    return tuple(risks)
