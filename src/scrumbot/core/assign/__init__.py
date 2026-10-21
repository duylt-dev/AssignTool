"""The assign step (bot spec §7.4, D64): for an order that passed `review`, size the orders, pick the PIC (assignment
spec §7) and build the risk register (bot spec §4) on the whole sprint with the order in it. Pure; it never imports
`core.review`."""

from __future__ import annotations

from collections.abc import Container
from dataclasses import replace

from scrumbot.core.assign.pipeline import build_result, team_for
from scrumbot.core.assign.report import order_report
from scrumbot.core.assign.sizing import Sizer, size_orders
from scrumbot.core.errors import InputError
from scrumbot.core.model import Source
from scrumbot.core.model_risk import RiskLevel
from scrumbot.core.outcome import Outcome, RiskCounts, Status
from scrumbot.core.place import Placed
from scrumbot.core.sprint.board import sprint_view
from scrumbot.core.sprint.validate import orders_and_findings

NOT_REVIEWED = "Đơn chưa qua review, hoặc đã đổi sau lần review đạt gần nhất: review lại '{}' trước khi giao."


def assign(placed: Placed, *, reviewed: Container[str], sizer: Sizer | None = None) -> Outcome:
    """`reviewed` holds the fingerprints of the passed reviews (A101); an order with a `Người làm` needs none (A87).
    The checks are not run again: the same fingerprint gives the same review."""
    inputs, order, previous = placed.inputs, placed.order, placed.previous
    if not order.row.assignees and placed.fingerprint not in reviewed:
        raise InputError(NOT_REVIEWED.format(inputs.order.origin or order.row.title))
    orders, findings = orders_and_findings(order.view)
    sizing = size_orders(orders, placed.history, frozenset({order.stt}), sizer)
    result = build_result(
        target=order.view,
        prev=sprint_view(inputs, previous) if previous is not None else None,
        prev_name=placed.previous_name,
        orders=orders,
        findings=findings + sizing.findings,
        devs=inputs.devs,
        history=placed.history,
        sizes=dict(sizing.sizes),
        sizing_note=sizing.note,
        rules=placed.rules,
        run_day=placed.today,
        now=placed.run_at,
    )
    report = order_report(result, order, team_for(inputs.devs, order.view, placed.today), placed.history)
    proposed = report.item.source is Source.PROPOSED
    return replace(
        placed.outcome(Status.PROPOSED if proposed else Status.PRE_ASSIGNED),
        assignment=report.item,
        sizing_note=result.sizing_note,
        risks=report.risks,
        sprint_risks=RiskCounts(*(sum(risk.level is level for risk in result.risks) for level in RiskLevel)),
        devs=report.devs,
        findings=report.findings,
    )
