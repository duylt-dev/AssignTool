"""Kept proposals between runs (bot spec §5.2, A66): which remembered proposals still stand, which became the TM's
decision, and how a kept proposal enters §7. Pure."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from scrumbot.model import Assignment, Dev, Order, Source
from scrumbot.model_risk import KeptProposal, Outcome
from scrumbot.normalize import text_key


def settle(
    kept: tuple[KeptProposal, ...], orders: tuple[Order, ...], active: tuple[Dev, ...], now: datetime
) -> tuple[dict[int, KeptProposal], tuple[Outcome, ...]]:
    """Proposals still standing (by STT), and outcomes for orders that got a `Người làm` since. A proposal whose
    order left the sprint is simply forgotten."""
    by_id = {order.row.id: order for order in orders if order.row.id}
    standing: dict[int, KeptProposal] = {}
    outcomes: list[Outcome] = []
    for proposal in kept:
        order = by_id.get(proposal.order_id)
        if order is None:
            continue
        if order.row.assignees:
            names = {text_key(name) for name in order.row.assignees}
            actual = tuple(dev.code for dev in active if text_key(dev.name) in names)
            outcomes.append(Outcome(proposal.order_id, order.row.title, proposal.code, actual, now))
        else:
            standing[order.row.stt] = proposal
    return standing, tuple(outcomes)


def with_kept(
    orders: tuple[Order, ...], standing: dict[int, KeptProposal], pool: tuple[Dev, ...]
) -> tuple[tuple[Order, ...], dict[int, KeptProposal]]:
    """Orders for §7 with each kept proposal written in as if pre-assigned, when its dev is still in the pool."""
    devs = {text_key(dev.code): dev for dev in pool}
    used: dict[int, KeptProposal] = {}
    result = []
    for order in orders:
        proposal = standing.get(order.row.stt)
        dev = devs.get(text_key(proposal.code)) if proposal is not None else None
        if proposal is not None and dev is not None and not order.row.assignees:
            used[order.row.stt] = proposal
            result.append(replace(order, row=replace(order.row, assignees=(dev.name,))))
        else:
            result.append(order)
    return tuple(result), used


def restore(
    assignments: tuple[Assignment, ...], originals: tuple[Order, ...], used: dict[int, KeptProposal]
) -> tuple[Assignment, ...]:
    """Turn the kept proposals back into proposals: the original empty order, the stored reason and backups."""
    by_stt = {order.row.stt: order for order in originals}
    result = []
    for item in assignments:
        proposal = used.get(item.order.row.stt)
        if proposal is None:
            result.append(item)
            continue
        result.append(
            replace(
                item,
                order=by_stt[item.order.row.stt],
                source=Source.PROPOSED,
                reason=f"Giữ đề xuất từ {proposal.at:%d/%m/%Y %H:%M} · {proposal.reason}",
                backups=proposal.backups,
                kept=True,
            )
        )
    return tuple(result)
