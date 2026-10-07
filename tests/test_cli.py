"""CLI: discovery, exit codes, the report's sheets and the AI wiring (spec §2, §10, §11)."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest
from openpyxl import load_workbook

from assigntool import ai_cli
from assigntool.cli import main
from assigntool.model import AiReply
from assigntool.xlsx_report import report_name
from tests.conftest import build_devs, build_sprint_workbook, write_history_csv

ORDER = {
    "STT": 1,
    "Task": "1.0.1 - Add ads",
    "Loại": "Task",
    "App Name.": "Demo",
    "Trạng thái": "ready to progress",
    "Ngày tạo": datetime(2026, 10, 5),
}


def _inputs(directory: Path) -> Path:
    directory.mkdir()
    build_sprint_workbook(
        directory / "export.xlsx",
        {"Sprint 2": [ORDER], "Sprint 1": [{**ORDER, "Người làm": "Dev A", "Trạng thái": "qa - need fix"}]},
    )
    build_devs(directory / "devs.xlsx", [{"Tên": "Dev A", "Mã": "DevA", "Level": "middle", "Nhận việc": "Y"}])
    write_history_csv(
        directory / "history.csv",
        [
            {
                "Sprint": "Sprint 1",
                "Task": "1.0.0",
                "Loại": "Task",
                "App Name": "Demo",
                "Người làm": "Dev A",
                "Ước lượng (h)": 8,
                "Ngày tạo": date(2026, 9, 1).isoformat(),
            }
        ],
    )
    return directory


def _report(out: Path) -> Path:
    (path,) = out.glob("assignment_sprint-2_*.xlsx")
    return path


def test_off_run_discovers_inputs_and_writes_the_three_sheets(tmp_path: Path, capsys) -> None:
    source = _inputs(tmp_path / "input")
    out = tmp_path / "out"

    assert main(["--input", str(source), "--out", str(out), "--ai", "off"]) == 0

    workbook = load_workbook(_report(out))
    assert workbook.sheetnames == ["Phân công", "Cảnh báo", "Tải dev"]
    header, row = list(workbook["Phân công"].iter_rows(values_only=True))
    assert header[-9:] == (
        "Độ lớn",
        "Giờ ước tính",
        "Lý do độ lớn",
        "PIC",
        "Mã PIC",
        "Nguồn",
        "Lý do",
        "Dự phòng 1",
        "Dự phòng 2",
    )
    assert row[-9:-2] == ("M (mặc định)", 16, None, "Dev A", "DevA", "Tool đề xuất", row[-3])
    printed = capsys.readouterr().out
    assert "Sprint: Sprint 2" in printed and "Độ lớn: tắt AI (mọi đơn M)" in printed
    assert "STT 1 · Demo 1.0.1 - Add ads [M] → DevA (dự phòng: không có)" in printed
    assert not list(source.glob("*.tmp")) and not list(out.glob("*.tmp"))


def test_ai_reply_sizes_the_order(tmp_path: Path, monkeypatch, capsys) -> None:
    source = _inputs(tmp_path / "input")
    out = tmp_path / "out"
    calls = []

    def fake(tool, prompt, *, model, timeout):
        calls.append((tool, model, timeout, "Dev A" in prompt))
        return AiReply(tool, '[{"stt": 1, "size": "L", "reason": "Thêm ads"}]', None)

    monkeypatch.setattr(ai_cli, "run_ai", fake)

    assert main(["--input", str(source), "--out", str(out), "--ai-model", "m1", "--ai-timeout", "9"]) == 0

    assert calls == [("gemini", "m1", 9, False)]
    row = list(load_workbook(_report(out))["Phân công"].iter_rows(values_only=True))[1]
    assert row[-9:-6] == ("L", 32, "Thêm ads")
    assert "Độ lớn: AI (gemini, 1/1 đơn)" in capsys.readouterr().out


def test_ai_failure_falls_back_to_m_and_still_writes_the_report(tmp_path: Path, monkeypatch, capsys) -> None:
    source = _inputs(tmp_path / "input")
    out = tmp_path / "out"
    monkeypatch.setattr(ai_cli, "run_ai", lambda tool, prompt, **_: AiReply(tool, None, "mã thoát 41"))

    assert main(["--input", str(source), "--out", str(out)]) == 0

    printed = capsys.readouterr().out
    assert "Độ lớn: mặc định M (mã thoát 41)" in printed
    assert "WARN SIZE-AI-FAILED" in printed
    findings = list(load_workbook(_report(out))["Cảnh báo"].iter_rows(values_only=True))
    assert findings[1][:2] == ("WARN", "SIZE-AI-FAILED")


@pytest.mark.parametrize(
    ("files", "flags", "message"),
    [
        ([], [], "Không tìm thấy file .xlsx export sprint. Chỉ định bằng --sprint."),
        (["a.xlsx", "b.xlsx", "devs.xlsx", "h.csv"], [], "Có nhiều file .xlsx export sprint: a.xlsx, b.xlsx."),
        (["a.xlsx", "h.csv"], [], "Không tìm thấy file devs.xlsx. Chỉ định bằng --devs."),
        (
            ["a.xlsx", "~$a.xlsx", ".b.xlsx", "devs.xlsx", "h.csv", "g.csv"],
            [],
            "Có nhiều file .csv lịch sử: g.csv, h.csv.",
        ),
        ([], ["--sprint", "missing.xlsx"], "Không có file 'missing.xlsx' (--sprint)."),
    ],
)
def test_input_errors_exit_2_with_a_message(tmp_path: Path, capsys, files, flags, message) -> None:
    source = tmp_path / "input"
    source.mkdir()
    for name in files:
        (source / name).write_bytes(b"")

    assert main(["--input", str(source), "--out", str(tmp_path / "out"), "--ai", "off", *flags]) == 2

    assert message in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_missing_input_directory_exits_2(tmp_path: Path, capsys) -> None:
    assert main(["--input", str(tmp_path / "nope"), "--ai", "off"]) == 2
    assert "Không có thư mục input" in capsys.readouterr().err


def test_report_name_uses_a_windows_safe_slug() -> None:
    now = datetime(2026, 10, 6, 14, 30, 0)
    assert report_name("Sprint 10", now) == "assignment_sprint-10_20261006-143000.xlsx"
    assert report_name("Sprint: 1/2", now) == "assignment_sprint_-1_2_20261006-143000.xlsx"


def test_without_csv_the_older_sheets_are_the_history_and_the_report_is_written(tmp_path: Path, capsys) -> None:
    source = _inputs(tmp_path / "input")
    (source / "history.csv").unlink()
    out = tmp_path / "out"

    assert main(["--input", str(source), "--out", str(out), "--ai", "off"]) == 0

    printed = capsys.readouterr().out
    assert "Lịch sử: sheet Sprint 1 trong workbook (không có file .csv)" in printed
    workbook = load_workbook(_report(out))
    assignment = list(workbook["Phân công"].iter_rows(values_only=True))[1]
    assert assignment[-3].startswith("Làm version gần nhất của Demo (Sprint 1: 1.0.1 - Add ads)")
    findings = list(workbook["Cảnh báo"].iter_rows(values_only=True))[1:]
    assert [row[:3] for row in findings] == [("INFO", "HISTORY-FROM-WORKBOOK", "Sprint 1")]
