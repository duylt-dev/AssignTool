"""How the core sizes orders (assignment spec §6.4, bot spec §8.5): the sizer it is given, else `M` for every order.
Pure."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from scrumbot.core.model import Finding, HistoryOrder, Order, Size, SizeEstimate

AI_OFF_NOTE = "tắt AI (mọi đơn M)"


@dataclass(frozen=True)
class Sizing:
    sizes: Mapping[int, SizeEstimate]  # by STT
    findings: tuple[Finding, ...] = ()  # SIZE-AI-FAILED, SIZE-AI-INVALID (assignment spec §9)
    note: str = ""  # the sizing note of the run, e.g. "AI (gemini, 6/6 đơn)"


class Sizer(Protocol):
    """The AI (bot spec §8.5). The STTs in `fresh` are sized by this call and never remembered. A sizer never raises
    for an AI failure: it sizes the orders `M` and says why in the note."""

    def __call__(
        self, orders: tuple[Order, ...], examples: tuple[HistoryOrder, ...], fresh: frozenset[int]
    ) -> Sizing: ...


def default_sizes(orders: tuple[Order, ...]) -> dict[int, SizeEstimate]:
    """The safe fallback: every order `M`."""
    return {order.row.stt: SizeEstimate(Size.M, "", True) for order in orders}


def size_orders(
    orders: tuple[Order, ...], examples: tuple[HistoryOrder, ...], fresh: frozenset[int], sizer: Sizer | None
) -> Sizing:
    """`None` is the AI turned off. An order the sizer leaves out is `M`."""
    if sizer is None:
        return Sizing(default_sizes(orders), (), AI_OFF_NOTE)
    if not orders:
        return Sizing({}, (), "không có đơn")
    sizing = sizer(orders, examples, fresh)
    sizes = default_sizes(orders)
    sizes.update((stt, estimate) for stt, estimate in sizing.sizes.items() if stt in sizes)
    return Sizing(sizes, sizing.findings, sizing.note)
