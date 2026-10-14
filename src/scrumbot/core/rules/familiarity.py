"""History-based app familiarity (assignment spec section 6.1)."""

from __future__ import annotations

from dataclasses import dataclass

from scrumbot.core.model import Dev, HistoryOrder
from scrumbot.core.normalize import app_key, text_key


@dataclass(frozen=True, slots=True)
class AppFamiliarity:
    rank: int
    latest: HistoryOrder | None
    versions: int


class FamiliarityIndex:
    """The kept history orders, grouped by normalized app name."""

    def __init__(self, kept: dict[str, tuple[HistoryOrder, ...]], latest: dict[str, HistoryOrder]) -> None:
        self._kept = kept
        self._latest = latest

    @classmethod
    def build(cls, history: tuple[HistoryOrder, ...], pool: tuple[Dev, ...]) -> FamiliarityIndex:
        pool_names = {text_key(dev.name) for dev in pool}
        grouped: dict[str, list[tuple[int, HistoryOrder]]] = {}
        for index, order in enumerate(history):
            key = app_key(order.app)
            if key and pool_names.intersection(text_key(name) for name in order.assignees):
                grouped.setdefault(key, []).append((index, order))
        kept = {key: tuple(order for _, order in orders) for key, orders in grouped.items()}
        latest = {key: max(orders, key=lambda item: (item[1].created, item[0]))[1] for key, orders in grouped.items()}
        return cls(kept, latest)

    def get(self, dev: Dev, app: str) -> AppFamiliarity:
        key = app_key(app)
        latest = self._latest.get(key)
        if latest is None:
            return AppFamiliarity(rank=2, latest=None, versions=0)
        name = text_key(dev.name)
        orders = self._kept[key]
        versions = sum(name in {text_key(person) for person in order.assignees} for order in orders)
        latest_people = {text_key(person) for person in latest.assignees}
        rank = 0 if name in latest_people else 1 if versions else 2
        return AppFamiliarity(rank=rank, latest=latest, versions=versions)

    def is_new_app(self, app: str) -> bool:
        return app_key(app) not in self._latest
