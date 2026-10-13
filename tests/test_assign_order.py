"""`scrumbot assign <file>` end to end against a real local HTTP server (bot spec §7): the order file in the sprint,
the AI prompt, the Markdown report, the memory left alone. Nothing reaches the dev server."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import closing
from datetime import date, datetime
from pathlib import Path

import pytest

from scrumbot.cli import main
from scrumbot.model import AiReply
from scrumbot.model_board import TECH_MANAGER_LIST
from scrumbot.understanding import ai_cli
from tests.api_builders import AN, DEV_ROWS, LINH, OUTSIDER, item, orders, sprint, sprints
from tests.conftest import build_devs
from tests.http_server import FakeDevServer

DONE = item("old", "1.0.0", people=(LINH,), status="done", hours=12, created=datetime(2026, 9, 23, 9))
TAKEN = item("t", "1.0.1 - Fix UI", people=(AN, OUTSIDER), status="in progress", created=datetime(2026, 10, 7, 9))
ORDER = """# Demo 1.0.2 - Add IAP

| Trường | Giá trị |
|---|---|
| ID | {order_id} |
| App | Demo |
| Ưu tiên | high |
| Hạn | 16/10/2026 |

Thêm IAP gói tháng, liên hệ BA: TestBA.
* Link UI [https://www.figma.com/design/abc/Demo](https://www.figma.com/design/abc/Demo)
"""


@pytest.fixture
def server(monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeDevServer]:
    running = FakeDevServer(
        {
            "sprints": sprints(
                sprint("S1", "Sprint 1 (9/22 - 10/3)", date(2026, 9, 22), date(2026, 10, 3), archived=True),
                sprint("S2", "Sprint 2 (10/6 - 10/17)", date(2026, 10, 6), date(2026, 10, 17)),
            ),
            "don": {"S1": orders(DONE), "S2": orders(TAKEN), TECH_MANAGER_LIST: orders(DONE, TAKEN)},
            "lich-su": {"ok": True, "ids": [], "khong_thay": [], "doi_trang_thai": [], "comment": [], "nguoi": []},
        }
    )
    monkeypatch.setenv("SCRUMBOT_API_BASE", running.base)
    yield running
    running.close()


@pytest.fixture
def source(tmp_path: Path) -> Path:
    folder = tmp_path / "input"
    folder.mkdir()
    build_devs(folder / "devs.xlsx", DEV_ROWS)
    return folder


def _order(source: Path, order_id: str = "") -> Path:
    path = source / "don.md"  # in the input folder itself: never taken for the TM rules file
    path.write_text(ORDER.format(order_id=order_id), encoding="utf-8")
    return path


def _assign(source: Path, tmp_path: Path, order: Path, *flags: str) -> int:
    paths = ["--input", str(source), "--state", str(tmp_path / "state"), "--out", str(tmp_path / "out")]
    return main(["assign", str(order), *paths, *flags])


def test_a_new_order_gets_a_pic_and_the_report_says_why(
    server: FakeDevServer, source: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    prompts = []

    def fake(tool, prompt, *, model, timeout):
        prompts.append(prompt)
        return AiReply(tool, '[{"stt": 1, "size": "S", "reason": "x"}, {"stt": 2, "size": "L", "reason": "IAP"}]', None)

    monkeypatch.setattr(ai_cli, "run_ai", fake)

    assert _assign(source, tmp_path, _order(source), "--ai", "agy") == 0

    (prompt,) = prompts
    assert "Thêm IAP gói tháng, liên hệ BA: [người]. * Link UI [link Figma]" in prompt
    assert all(text not in prompt for text in ("TestBA", "figma.com", LINH, AN, OUTSIDER, "AnTD"))
    report = (tmp_path / "out" / "output.md").read_text(encoding="utf-8")
    assert report.startswith("# Giao đơn: Demo 1.0.2 - Add IAP\n")
    assert "- **PIC đề xuất: LinhNV**" in report
    assert "- Độ lớn (AI): L (32h): IAP" in report
    assert "| Đơn | Đơn mới, chưa có trên hệ thống (tính là STT 2 của Sprint 2) |" in report
    assert "| LinhNV | middle+ | Làm version gần nhất | 1 | 32h / " in report and "| **PIC** |" in report
    assert "## Rủi ro và phương án dự phòng" in report and "## Cảnh báo dữ liệu" in report
    assert OUTSIDER not in report
    printed = capsys.readouterr().out
    assert "Đơn: Demo 1.0.2 - Add IAP (đơn mới, STT 2 của Sprint 2)" in printed
    assert "PIC đề xuất: LinhNV (dự phòng: " in printed
    assert not list((tmp_path / "out").glob("*.xlsx")) and not list((tmp_path / "out").glob("*.tmp"))
    with closing(sqlite3.connect(tmp_path / "state" / "scrumbot.sqlite")) as db:
        assert db.execute("SELECT COUNT(*) FROM proposals").fetchone() == (0,)
        assert db.execute("SELECT COUNT(*) FROM order_marks").fetchone() == (0,)
        assert db.execute("SELECT order_id FROM ai_answers").fetchall() == [("t",)]


def test_the_order_of_the_file_is_sized_again_on_every_run(
    server: FakeDevServer, source: Path, tmp_path: Path, monkeypatch
) -> None:
    sized = []

    def fake(tool, prompt, *, model, timeout):
        sized.append(prompt.count("\n- STT "))
        return AiReply(tool, '[{"stt": 1, "size": "S", "reason": "x"}, {"stt": 2, "size": "M", "reason": "y"}]', None)

    monkeypatch.setattr(ai_cli, "run_ai", fake)
    order = _order(source, "t")

    assert _assign(source, tmp_path, order, "--ai", "agy") == 0
    assert _assign(source, tmp_path, order, "--ai", "agy") == 0

    assert sized == [1, 1]  # the only order is the file's, never taken from the memory


def test_an_order_already_taken_on_the_system_is_kept(server: FakeDevServer, source: Path, tmp_path: Path) -> None:
    assert _assign(source, tmp_path, _order(source, "t"), "--ai", "off") == 0

    report = (tmp_path / "out" / "output.md").read_text(encoding="utf-8")
    assert "- **Đã có người làm trên hệ thống: AnTD.** Bot giữ nguyên, không đề xuất PIC khác." in report
    assert "| Đơn | Đơn trên hệ thống, ID t, STT 1 (nối theo ID) |" in report
    assert "| AnTD | junior+ | Chưa làm | 1 | 16h / " in report and "| **Người làm** |" in report


@pytest.mark.parametrize(
    ("order_id", "missing", "message"),
    [
        ("zz", False, "Không có đơn gốc ID 'zz' trong Sprint 2 (10/6 - 10/17)."),
        ("", True, "Không có file đơn"),
    ],
)
def test_input_errors_exit_2_without_a_report(
    server: FakeDevServer, source: Path, tmp_path: Path, capsys, order_id, missing, message
) -> None:
    order = source / "nope.md" if missing else _order(source, order_id)

    assert _assign(source, tmp_path, order, "--ai", "off") == 2

    assert message in capsys.readouterr().err
    assert not (tmp_path / "out").exists()
