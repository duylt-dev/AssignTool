"""The command line against a real local HTTP server (assignment spec §2, §11; bot spec §1, §7): input discovery,
exit codes, output.md, the TM rules and the AI wiring. Nothing reaches the dev server."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime
from pathlib import Path

import pytest

from scrumbot.cli import main
from scrumbot.model import AiReply
from scrumbot.model_board import TECH_MANAGER_LIST
from scrumbot.understanding import ai_cli
from tests.api_builders import DEV_ROWS, LINH, item, orders, sprint, sprints
from tests.conftest import build_devs
from tests.http_server import FakeDevServer

DONE = item("old", "1.0.0", people=(LINH,), status="done", hours=12, created=datetime(2026, 9, 23, 9))
EMPTY = item("new", "1.0.1 - Add ads", status="ready to progress", created=datetime(2026, 10, 7, 9))
RULES = "# Luật\n\n| Loại | Dev | App | Ghi chú |\n|---|---|---|---|\n| Chỉ định | MinhNM | Demo | thử |\n"
# The file names the empty order of the sprint by its title (bot spec §7.2) and passes the review (§7.3).
ORDER = "# 1.0.1 - Add ads\n\nThêm quảng cáo xen kẽ ở màn hình chính và màn kết quả.\n"


@pytest.fixture
def server(monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeDevServer]:
    running = FakeDevServer(
        {
            "sprints": sprints(
                sprint("S1", "Sprint 1 (9/22 - 10/3)", date(2026, 9, 22), date(2026, 10, 3), archived=True),
                sprint("S2", "Sprint 2 (10/6 - 10/17)", date(2026, 10, 6), date(2026, 10, 17)),
            ),
            "don": {"S1": orders(DONE), "S2": orders(EMPTY), TECH_MANAGER_LIST: orders(DONE, EMPTY)},
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


def _run(source: Path, tmp_path: Path, *flags: str) -> int:
    order = tmp_path / "don" / "order.md"
    order.parent.mkdir(exist_ok=True)
    order.write_text(ORDER, encoding="utf-8")
    paths = ["--input", str(source), "--state", str(tmp_path / "state"), "--out", str(tmp_path / "out")]
    return main(["assign", str(order), *paths, *flags])


def _report(tmp_path: Path) -> str:
    return (tmp_path / "out" / "output.md").read_text(encoding="utf-8")


def test_an_off_run_writes_output_md_and_prints_the_proposal(
    server: FakeDevServer, source: Path, tmp_path: Path, capsys
) -> None:
    assert _run(source, tmp_path, "--ai", "off", "--today", "2026-10-08") == 0

    report = _report(tmp_path)
    assert "- **PIC đề xuất: LinhNV**" in report and "- Độ lớn (AI): M (16h) (mặc định)" in report
    assert "- Lý do: Làm version gần nhất của Demo (Sprint 1 (9/22 - 10/3): 1.0.0)" in report
    assert "Không có câu hỏi của AI (AI tắt hoặc lỗi)." in report
    printed = capsys.readouterr().out
    assert "Ngày chạy: 08/10/2026 (--today)" in printed and "Độ lớn: M (mặc định) · tắt AI (mọi đơn M)" in printed
    assert "Luật TM: không có" in printed and "Review: đạt (0 câu hỏi của AI)" in printed
    assert "PIC đề xuất: LinhNV (dự phòng: MinhNM, AnTD)" in printed
    assert not list((tmp_path / "out").glob("*.tmp"))


def test_ai_reply_sizes_the_order_without_names_and_with_the_history_hours(
    server: FakeDevServer, source: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    calls = []

    def fake(tool, prompt, *, model, timeout):
        calls.append((tool, model, timeout, LINH in prompt, "- Demo · 1.0.0 · 12h" in prompt))
        reply = '[{"stt": 1, "size": "L", "reason": "Thêm ads", "questions": ["Quảng cáo loại nào?"]}]'
        return AiReply(tool, reply, None)

    monkeypatch.setattr(ai_cli, "run_ai", fake)

    assert _run(source, tmp_path, "--ai-model", "m1", "--ai-timeout", "9", "--today", "2026-10-08") == 0

    assert calls == [("gemini", "m1", 9, False, True)]
    report = _report(tmp_path)
    assert "- Độ lớn (AI): L (32h): Thêm ads" in report
    assert "## Review: đạt\n\nCâu hỏi của AI cho người lên đơn" in report and "- Quảng cáo loại nào?" in report
    printed = capsys.readouterr().out
    assert "Độ lớn: L · AI (gemini, 1/1 đơn)" in printed and "Review: đạt (1 câu hỏi của AI)" in printed


def test_ai_failure_falls_back_to_m_and_still_writes_the_report(
    server: FakeDevServer, source: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setattr(ai_cli, "run_ai", lambda tool, prompt, **_: AiReply(tool, None, "mã thoát 41"))

    assert _run(source, tmp_path, "--today", "2026-10-08") == 0

    printed = capsys.readouterr().out
    assert "mặc định M (mã thoát 41)" in printed and "WARN SIZE-AI-FAILED" in printed
    assert "- WARN `SIZE-AI-FAILED`" in _report(tmp_path)


def test_the_md_file_in_the_input_folder_is_the_rules_file_and_its_pin_reaches_the_report(
    server: FakeDevServer, source: Path, tmp_path: Path, capsys
) -> None:
    (source / "luat.md").write_text(RULES.replace("\n", "\r\n"), encoding="utf-8-sig")

    assert _run(source, tmp_path, "--ai", "off", "--today", "2026-10-08") == 0

    printed = capsys.readouterr().out
    assert "Luật TM: file luat.md (1 luật, 1 có hiệu lực ngày 08/10/2026)" in printed
    assert "PIC đề xuất: MinhNM " in printed
    assert "- Lý do: Luật TM dòng 5: chỉ định MinhNM cho Demo (thử)" in _report(tmp_path)


@pytest.mark.parametrize(("today", "pic"), [("2026-10-14", "MinhNM"), ("2026-10-08", "LinhNV")])
def test_today_replaces_the_clock_for_the_rules_day(
    server: FakeDevServer, source: Path, tmp_path: Path, capsys, today, pic
) -> None:
    """A pin dated 12/10–31/10 acts on 14/10 but not on 08/10 (A34)."""
    dated = (
        "| Loại | Dev | App | Từ ngày | Đến ngày |\n|---|---|---|---|---|\n"
        "| Chỉ định | MinhNM | Demo | 12/10/2026 | 31/10/2026 |\n"
    )
    (source / "luat.md").write_text(dated, encoding="utf-8")

    assert _run(source, tmp_path, "--ai", "off", "--today", today) == 0

    assert f"PIC đề xuất: {pic} " in capsys.readouterr().out


@pytest.mark.parametrize(
    ("files", "flags", "message"),
    [
        (["~$devs.xlsx"], [], "Không tìm thấy file devs.xlsx. Chỉ định bằng --devs."),
        (["devs.xlsx", "a.md", "b.md"], [], "Có nhiều file luật .md: a.md, b.md. Chỉ định một file bằng --rules."),
        (["devs.xlsx", "a.md"], [], "không có bảng luật (bảng có cột Loại và Dev)."),
        (["devs.xlsx"], ["--rules", "missing.md"], "Không có file 'missing.md' (--rules)."),
        (["devs.xlsx", "a.md:rules"], [], "dòng 5: không có dev mã 'Nobody' trong file dev."),
        (["devs.xlsx"], ["--today", "31/02/2026"], "--today '31/02/2026': không đọc được ngày"),
    ],
)
def test_input_errors_exit_2_with_a_message(tmp_path: Path, capsys, files, flags, message) -> None:
    source = tmp_path / "input"
    source.mkdir()
    for spec in files:
        name, _, kind = spec.partition(":")
        if name == "devs.xlsx":
            build_devs(source / name, DEV_ROWS)
        elif kind == "rules":
            (source / name).write_text(RULES.replace("MinhNM", "Nobody"), encoding="utf-8")
        else:
            (source / name).write_bytes(b"")

    assert _run(source, tmp_path, "--ai", "off", *flags) == 2

    assert message in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_missing_input_directory_exits_2(tmp_path: Path, capsys) -> None:
    assert _run(tmp_path / "nope", tmp_path, "--ai", "off") == 2
    assert "Không có thư mục input" in capsys.readouterr().err


def test_the_cli_refuses_the_production_server(
    monkeypatch: pytest.MonkeyPatch, source: Path, tmp_path: Path, capsys
) -> None:
    monkeypatch.setenv("SCRUMBOT_API_BASE", "https://circle.datlt.site")

    assert _run(source, tmp_path, "--ai", "off") == 2

    assert "trỏ tới production (circle.datlt.site); bot chỉ đọc server dev" in capsys.readouterr().err


@pytest.mark.parametrize("argv", [[], ["run"], ["input/don/order.md"]])
def test_only_assign_is_a_command(argv: list[str], capsys) -> None:
    """`run` was removed (D62); without `assign` the usage is printed and the exit code is 2 (A91)."""
    with pytest.raises(SystemExit) as stopped:
        main(argv)

    assert stopped.value.code == 2
    assert "usage: scrumbot" in capsys.readouterr().err
