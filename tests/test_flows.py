"""The flows end to end against a real local HTTP server (bot spec §1–§9): a manual run on two days with the memory,
the scheduled run, the clone and its replay, the end-of-sprint report. Nothing reaches the dev server."""

from __future__ import annotations

import copy
from collections.abc import Iterator
from datetime import date, datetime
from pathlib import Path

import pytest
from openpyxl import load_workbook

from scrumbot.cli import main
from scrumbot.flows import auto as auto_flow
from scrumbot.flows.auto import auto
from scrumbot.flows.clone import clone
from scrumbot.flows.common import Options
from scrumbot.flows.replay_flow import replay
from scrumbot.flows.run_api import run_api
from scrumbot.flows.sprint_end import sprint_end
from scrumbot.model_board import TECH_MANAGER_LIST
from tests.api_builders import AN, DEV_ROWS, LINH, MINH, TIEN, history, item, orders, sprint, sprints
from tests.conftest import build_devs
from tests.http_server import FakeDevServer

TUESDAY = datetime(2026, 10, 13, 9, 0)
ROBLOX = item("a", "1.0.4", people=(AN,), app="Roblox", status="done", created=datetime(2026, 9, 20, 9))
PS = item(
    "b", "1.1.1", people=(MINH, LINH), app="PS Remote", status="need to be clean", created=datetime(2026, 9, 19, 9)
)
EMPTY = item("c", "1.0.5", app="Roblox", status="ready to progress", created=datetime(2026, 10, 1, 9))
DEMO = item("e", "2.0.0", people=(LINH,), app="Demo", created=datetime(2026, 10, 2, 9))
GAME = item("f", "1.2.0", people=(TIEN,), app="Game", created=datetime(2026, 10, 2, 9))
BACKLOG = item("g", "9.9.9", app="Other", status="all issue", created=datetime(2026, 10, 10, 9))


def _data() -> dict[str, object]:
    return {
        "sprints": sprints(
            sprint("S9", "Sprint 9 (9/21 - 10/2)", date(2026, 9, 21), date(2026, 10, 2), archived=True, total=2),
            sprint("S10", "Sprint 10 (10/6 - 10/17)", date(2026, 10, 6), date(2026, 10, 17), total=3),
            sprint("T10", "[Test sprint] Sprint 10 (10/6 - 10/17)", date(2026, 10, 6), date(2026, 10, 17), total=3),
        ),
        "don": {
            "S9": orders(ROBLOX, PS),
            "S10": orders(EMPTY, DEMO, GAME),
            "T10": orders(EMPTY, DEMO, GAME),
            TECH_MANAGER_LIST: orders(ROBLOX, PS, EMPTY, DEMO, GAME, BACKLOG),
        },
        "lich-su": history(("e", "ready to progress", "in progress", datetime(2026, 10, 7, 9))),
    }


@pytest.fixture
def server(monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeDevServer]:
    running = FakeDevServer(_data())
    monkeypatch.setenv("SCRUMBOT_API_BASE", running.base)
    yield running
    running.close()


@pytest.fixture
def options(tmp_path: Path) -> Options:
    (tmp_path / "input").mkdir()
    build_devs(tmp_path / "input" / "devs.xlsx", DEV_ROWS)
    return Options(
        input_dir=tmp_path / "input",
        state_dir=tmp_path / "state",
        out_dir=tmp_path / "out",
        ai="off",
        env_file=tmp_path / "absent.env",
    )


def _sheet(path: Path, name: str) -> list[tuple]:
    return list(load_workbook(path)[name].iter_rows(values_only=True))


def test_a_manual_run_proposes_keeps_the_proposal_and_reports_the_changes_of_the_next_day(
    server: FakeDevServer, options: Options
) -> None:
    lines: list[str] = []
    first = run_api(options, lines.append, TUESDAY)

    assert "STT 1 · Roblox 1.0.5 [M] → AnTD (dự phòng: MinhNM, TiếnBV)" in lines
    assert any(line.startswith("Nguồn: API 127.0.0.1 (dữ liệu mới nhất 10/10/2026 09:00)") for line in lines)
    summary = dict(_sheet(first, "Tóm tắt")[1:])
    assert summary["Đơn trống chưa vào sprint"] == "1 đơn ở list Tech manager, 1 đơn tạo trong 30 ngày gần đây"
    assert summary["Thay đổi"] == "Chưa có lần chạy trước để so"
    header = _sheet(first, "Phân công")[0]
    assert header[:11] == (
        "STT",
        "ID",
        "Task",
        "App Name",
        "Trạng thái",
        "Người làm",
        "Ưu tiên",
        "Hạn",
        "Ngày tạo",
        "Bug mở",
        "Bug tổng",
    )
    assert sum(1 for _ in (options.state_dir / "snapshots").iterdir()) == 1
    assert "/api/doc/don" in server.requests and server.requests.count("/api/doc/sprints") == 1

    again: list[str] = []
    run_api(options, again.append, datetime(2026, 10, 13, 10, 0))
    assert "STT 1 · Roblox 1.0.5 [M] → AnTD (giữ đề xuất) (dự phòng: MinhNM, TiếnBV)" in again

    data = copy.deepcopy(_data())
    data["don"]["S10"] = orders({**EMPTY, "_people": [AN]}, {**DEMO, "uu_tien": "urgent"}, GAME)  # type: ignore[index]
    server.data = data
    next_day = run_api(options, [].append, datetime(2026, 10, 14, 9, 0))

    changes = _sheet(next_day, "Thay đổi")
    assert changes[1][0] == "So với dữ liệu lưu lúc 13/10/2026 10:00"
    assert ("Đổi ưu tiên", "STT 2 · 2.0.0", "trống", "urgent") in changes
    assert ("TM đã giao", "STT 1 · 1.0.5", "AnTD", "AnTD (khớp)") in changes
    risks = {row[1]: row for row in _sheet(next_day, "Rủi ro")[1:]}
    assert risks["ORDER-CHANGED"][:5] == (
        "Trung bình",
        "ORDER-CHANGED",
        "Thay đổi",
        "Đơn STT 2",
        "Đơn STT 2 đổi ưu tiên trống → urgent",
    )


def test_the_scheduled_run_writes_once_then_only_on_change_and_notifies(
    server: FakeDevServer, options: Options, monkeypatch: pytest.MonkeyPatch
) -> None:
    shown: list[str] = []
    monkeypatch.setattr(auto_flow, "notify", lambda message, title="scrumbot": shown.append(message) or True)

    assert auto(options, [].append, TUESDAY) == 0
    assert auto(options, [].append, datetime(2026, 10, 13, 9, 30)) == 0

    reports = sorted(path.name for path in (options.state_dir / "bao-cao").iterdir())
    assert [name.split("_")[0] for name in reports] == ["assignment", "cuoi-sprint"]
    log = (options.state_dir / "log" / "scrumbot-2026-10-13.log").read_text(encoding="utf-8").splitlines()
    assert log[0].startswith("09:00 đầy đủ Sprint 10 (10/6 - 10/17): ghi assignment_sprint-10_") and log[0].endswith(
        "(giao 1 đơn mới)"
    )
    assert log[1].startswith("09:00 cuối sprint Sprint 9 (9/21 - 10/2): ghi cuoi-sprint_sprint-9_")
    assert log[2] == "09:30 nhanh Sprint 10 (10/6 - 10/17): không đổi"
    assert shown[0].startswith("Sprint 10 (10/6 - 10/17): giao 1 đơn mới. Báo cáo: assignment_sprint-10_")
    assert shown[1].startswith("Báo cáo cuối sprint Sprint 9 (9/21 - 10/2): cuoi-sprint_sprint-9_")
    assert len(shown) == 2
    assert [path.name for path in (options.state_dir / "snapshots").iterdir()] == ["20261013-090000"]


def test_the_scheduled_run_skips_a_day_without_a_running_sprint(server: FakeDevServer, options: Options) -> None:
    assert auto(options, [].append, datetime(2026, 10, 5, 8, 30)) == 0

    log = (options.state_dir / "log" / "scrumbot-2026-10-05.log").read_text(encoding="utf-8")
    assert log == "08:30 đầy đủ: không có sprint đang chạy\n"


def test_clone_copies_everything_and_replay_scores_it_without_the_api(server: FakeDevServer, options: Options) -> None:
    lines: list[str] = []
    folder = clone(options, lines.append, datetime(2026, 10, 21, 9, 0))

    assert sorted(path.name for path in (folder / "don").iterdir()) == [
        "901609972453.json.gz",
        "S10.json.gz",
        "S9.json.gz",
        "T10.json.gz",
    ]
    assert (folder / "lich-su.json.gz").is_file() and lines[-1].endswith("request, chỉ GET)")
    server.close()

    said: list[str] = []
    report = replay(options, folder, said.append, datetime(2026, 10, 21, 10, 0))

    assert load_workbook(report).sheetnames == [
        "Giao người theo sprint",
        "Giao người theo đơn",
        "Rủi ro theo loại",
        "Rủi ro theo loại (có lịch sử)",
        "Rủi ro theo sprint",
        "Kết cục đơn",
        "Sổ rủi ro các mốc",
    ]
    assert said[0] == f"Replay: Bản sao {folder}, 2 sprint (mọi đơn M)"
    assert any(line.startswith("Sprint 9 (9/21 - 10/2): khớp ") for line in said)
    assert _sheet(report, "Giao người theo sprint")[-1][0] == "Tổng"

    end = sprint_end(
        Options(**{**options.__dict__, "snapshot": folder, "today": date(2026, 10, 21)}),
        [].append,
        datetime(2026, 10, 21, 11),
    )
    assert end.name.startswith("cuoi-sprint_sprint-10_")
    assert load_workbook(end).sheetnames == [
        "Tóm tắt",
        "Rủi ro theo loại",
        "Kết cục đơn",
        "Sổ rủi ro các mốc",
        "Đề xuất của bot",
    ]


def test_the_cli_refuses_the_production_server(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys) -> None:
    (tmp_path / "input").mkdir()
    build_devs(tmp_path / "input" / "devs.xlsx", DEV_ROWS)
    monkeypatch.setenv("SCRUMBOT_API_BASE", "https://circle.datlt.site")

    code = main(["run", "--input", str(tmp_path / "input"), "--state", str(tmp_path / "state"), "--ai", "off"])

    assert code == 2
    assert "trỏ tới production (circle.datlt.site); bot chỉ đọc server dev" in capsys.readouterr().err
