"""Snapshots, clones and the list cache on disk (bot spec §2.3, §2.4; A57, A58)."""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from scrumbot.actions.housekeeping import append_log, prune
from scrumbot.errors import InputError
from scrumbot.model_board import SprintInfo
from scrumbot.sources.raw_store import LiveSource, Recorder, StoredSource, read_json, write_json

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


def test_archived_lists_come_from_the_cache_and_ended_ones_only_on_the_day_they_were_cached(tmp_path: Path) -> None:
    client = CountingClient()
    source = LiveSource(client, tmp_path / "cache", None, TODAY)  # type: ignore[arg-type]
    archived, ended, running = _sprint("A", archived=True), _sprint("E", end=date(2026, 10, 2)), _sprint("R")

    for _ in range(2):
        source.orders("A", archived)
        source.orders("E", ended)
        source.orders("R", running)
    assert client.fetched == ["A", "E", "R", "R"]

    yesterday = (datetime(2026, 10, 12, 9)).timestamp()
    os.utime(tmp_path / "cache" / "don" / "E.json.gz", (yesterday, yesterday))
    source.orders("E", ended)
    source.orders("A", archived)
    assert client.fetched == ["A", "E", "R", "R", "E"]


def test_a_recorded_snapshot_reads_back_and_falls_back_to_the_cache(tmp_path: Path) -> None:
    client = CountingClient()
    recorder = Recorder(tmp_path / "snap", kind="snapshot", host="test", now=datetime(2026, 10, 13, 9))
    live = LiveSource(client, tmp_path / "cache", recorder, TODAY)  # type: ignore[arg-type]
    live.sprints()
    live.orders("R", _sprint("R"))
    live.history(["x"])
    write_json(tmp_path / "cache" / "don" / "OLD.json.gz", {"ok": True, "don": [{"id": "OLD"}]})

    stored = StoredSource(tmp_path / "snap", tmp_path / "cache")

    assert stored.label == f"Snapshot {tmp_path / 'snap'}" and stored.fetched_at == datetime(2026, 10, 13, 9)
    assert stored.orders("R", None)["don"] == [{"id": "R"}]
    assert stored.orders("OLD", None)["don"] == [{"id": "OLD"}]
    assert stored.history([])["ids"] == ["x"]
    with pytest.raises(InputError, match="không có MISSING.json.gz"):
        stored.orders("MISSING", None)


def test_plain_json_is_read_too_and_a_missing_folder_is_an_input_error(tmp_path: Path) -> None:
    (tmp_path / "sprints.json").write_text('{"ok": true, "sprints": []}', encoding="utf-8")

    assert read_json(tmp_path, "sprints") == {"ok": True, "sprints": []}
    with pytest.raises(InputError, match="Không có thư mục"):
        StoredSource(tmp_path / "nope", None)


def test_prune_removes_entries_older_than_thirty_days_and_logs_append(tmp_path: Path) -> None:
    now = datetime(2026, 10, 13, 9)
    old, fresh = tmp_path / "20260901-090000", tmp_path / "20261012-090000"
    old.mkdir()
    fresh.mkdir()
    stamp = (now - timedelta(days=31)).timestamp()
    os.utime(old, (stamp, stamp))

    assert prune(tmp_path, now) == 1
    assert not old.exists() and fresh.exists()
    log = append_log(tmp_path / "log", now, "đầy đủ Sprint 10: không đổi")
    append_log(tmp_path / "log", now, "nhanh Sprint 10: không đổi")
    assert log.read_text(encoding="utf-8").splitlines() == [
        "09:00 đầy đủ Sprint 10: không đổi",
        "09:00 nhanh Sprint 10: không đổi",
    ]
