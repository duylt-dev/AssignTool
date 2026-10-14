"""The list cache on disk (bot spec §2.3; A57, A58)."""

from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path

import pytest

from scrumbot.core.errors import InputError
from scrumbot.core.inputs import SprintInfo
from scrumbot.input.dev_api.cache import LiveSource, read_json, write_json

TODAY = date(2026, 10, 13)


class CountingClient:
    """Stands in for ApiClient at the source boundary: counts which lists were fetched."""

    host = "test"

    def __init__(self) -> None:
        self.fetched: list[str] = []

    def sprints(self, folder_id: str) -> dict[str, object]:
        return {"ok": True, "sprints": []}

    def orders(self, list_id: str) -> dict[str, object]:
        self.fetched.append(list_id)
        return {"ok": True, "don": [{"id": list_id}], "trang_thai": [], "nguoi": []}

    def history(self, ids: list[str]) -> dict[str, object]:
        return {"doi_trang_thai": []}


def _sprint(sprint_id: str, *, archived: bool = False, end: date = date(2026, 10, 17)) -> SprintInfo:
    return SprintInfo(
        id=sprint_id, name=sprint_id, kind="sprint", total=1, start=date(2026, 10, 6), end=end, archived=archived
    )


def _written_at(path: Path, moment: datetime) -> None:
    os.utime(path, (moment.timestamp(), moment.timestamp()))


def test_archived_lists_come_from_the_cache_and_ended_ones_only_on_the_day_they_were_cached(tmp_path: Path) -> None:
    client = CountingClient()
    source = LiveSource(client, tmp_path / "cache", TODAY)  # type: ignore[arg-type]
    archived, ended, running = _sprint("A", archived=True), _sprint("E", end=date(2026, 10, 2)), _sprint("R")

    cached = tmp_path / "cache" / "don" / "E.json.gz"
    for _ in range(2):
        source.orders("A", archived)
        source.orders("E", ended)
        _written_at(cached, datetime(2026, 10, 13, 9))  # the run day, not the machine's clock
        source.orders("R", running)
    assert client.fetched == ["A", "E", "R", "R"]

    _written_at(cached, datetime(2026, 10, 12, 9))
    source.orders("E", ended)
    source.orders("A", archived)
    assert client.fetched == ["A", "E", "R", "R", "E"]


def test_a_cached_list_round_trips_and_a_broken_one_is_an_input_error(tmp_path: Path) -> None:
    path = tmp_path / "L.json.gz"
    write_json(path, {"ok": True, "don": [{"id": "Lê"}]})

    assert read_json(path) == {"ok": True, "don": [{"id": "Lê"}]}
    path.write_bytes(b"not gzip")
    with pytest.raises(InputError, match="Không đọc được file"):
        read_json(path)
