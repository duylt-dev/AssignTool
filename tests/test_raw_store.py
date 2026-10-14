"""The list cache on disk (bot spec §2.3; A57, A58)."""

from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path

import pytest

from scrumbot.errors import InputError
from scrumbot.model_board import SprintInfo
from scrumbot.sources.raw_store import LiveSource, read_json

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
        return {"ok": True, "ids": ids, "doi_trang_thai": [], "comment": [], "nguoi": [], "khong_thay": []}


def _sprint(sprint_id: str, *, archived: bool = False, end: date = date(2026, 10, 17)) -> SprintInfo:
    return SprintInfo(sprint_id, sprint_id, "sprint", date(2026, 10, 6), end, archived, 1, 0)


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


def test_plain_json_is_read_too_and_a_missing_file_is_an_input_error(tmp_path: Path) -> None:
    (tmp_path / "sprints.json").write_text('{"ok": true, "sprints": []}', encoding="utf-8")

    assert read_json(tmp_path, "sprints") == {"ok": True, "sprints": []}
    with pytest.raises(InputError, match="không có MISSING.json.gz"):
        read_json(tmp_path, "MISSING")
