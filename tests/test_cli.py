"""CLI on the export files (`run --source file`): discovery, exit codes, the report's sheets and the AI wiring
(assignment spec §2, §10, §11; bot spec §1, §6)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from openpyxl import load_workbook

from scrumbot.actions.xlsx_report import report_name
from scrumbot.cli import main
from scrumbot.model import AiReply
from scrumbot.understanding import ai_cli
from tests.conftest import build_devs, build_history_xlsx, build_sprint_workbook, write_history_csv

FILE = ["run", "--source", "file"]

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
    write_history_csv(directory / "history.csv", [HISTORY])
    return directory


HISTORY = {
    "Ngày lên đơn": "2026-09-01 10:00",
    "Tên task": "1.0.0",
    "Loại": "Task",
    "App Name": "Demo",
    "Người làm": "Dev A",
    "Sprint": "Sprint 1 (9/22 - 10/3)",
}


RULES = "# Luật\n\n| Loại | Dev | App | Ghi chú |\n|---|---|---|---|\n| Chỉ định | DevB | Demo | thử |\n"
TWO_DEVS = [
    {"Tên": "Dev A", "Mã": "DevA", "Level": "middle", "Nhận việc": "Y"},
    {"Tên": "Dev B", "Mã": "DevB", "Level": "junior", "Nhận việc": "Y"},
]


def _report(out: Path) -> Path:
    (path,) = out.glob("assignment_sprint-2_*.xlsx")
    return path


def test_off_run_discovers_inputs_and_writes_the_six_sheets(tmp_path: Path, capsys) -> None:
    source = _inputs(tmp_path / "input")
    out = tmp_path / "out"

    assert main([*FILE, "--input", str(source), "--out", str(out), "--ai", "off", "--today", "2026-10-06"]) == 0

    workbook = load_workbook(_report(out))
    assert workbook.sheetnames == ["Tóm tắt", "Phân công", "Rủi ro", "Thay đổi", "Cảnh báo", "Tải dev"]
    header, row = list(workbook["Phân công"].iter_rows(values_only=True))
    assert header[-13:] == (
        "Độ lớn",
        "Giờ ước tính",
        "Lý do độ lớn",
        "Loại đơn (AI)",
        "Hạng mục (AI)",
        "Rủi ro kỹ thuật (AI)",
        "PIC",
        "Mã PIC",
        "Nguồn",
        "Lý do",
        "Dự phòng 1",
        "Dự phòng 2",
        "Rủi ro",
    )
    assert row[-13:-4] == ("M (mặc định)", 16, None, None, None, None, "Dev A", "DevA", "Tool đề xuất")
    changes = list(workbook["Thay đổi"].iter_rows(values_only=True))
    assert changes[1][0] == "Nguồn file export không có id đơn; không so được."
    summary = dict(list(workbook["Tóm tắt"].iter_rows(values_only=True))[1:])
    assert summary["Nguồn"] == "File export.xlsx" and summary["Rủi ro"] == "0 cao · 0 trung bình · 1 thấp"
    risks = list(workbook["Rủi ro"].iter_rows(values_only=True))
    assert risks[1][:5] == ("Thấp", "CARRY-OVER", "Năng lực", "DevA", "DevA còn 1 việc dở ở Sprint 1")
    assert row[-1] is None  # CARRY-OVER is about the dev, not the order
    printed = capsys.readouterr().out
    assert "Sprint: Sprint 2" in printed and "Độ lớn: tắt AI (mọi đơn M)" in printed
    assert "Luật TM: không có" in printed
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

    assert main([*FILE, "--input", str(source), "--out", str(out), "--ai-model", "m1", "--ai-timeout", "9"]) == 0

    assert calls == [("gemini", "m1", 9, False)]
    row = list(load_workbook(_report(out))["Phân công"].iter_rows(values_only=True))[1]
    assert row[-13:-10] == ("L", 32, "Thêm ads")
    assert "Độ lớn: AI (gemini, 1/1 đơn)" in capsys.readouterr().out


def test_ai_failure_falls_back_to_m_and_still_writes_the_report(tmp_path: Path, monkeypatch, capsys) -> None:
    source = _inputs(tmp_path / "input")
    out = tmp_path / "out"
    monkeypatch.setattr(ai_cli, "run_ai", lambda tool, prompt, **_: AiReply(tool, None, "mã thoát 41"))

    assert main([*FILE, "--input", str(source), "--out", str(out)]) == 0

    printed = capsys.readouterr().out
    assert "Độ lớn: mặc định M (mã thoát 41)" in printed
    assert "WARN SIZE-AI-FAILED" in printed
    findings = list(load_workbook(_report(out))["Cảnh báo"].iter_rows(values_only=True))
    assert findings[1][:2] == ("WARN", "SIZE-AI-FAILED")


@pytest.mark.parametrize(
    ("files", "flags", "message"),
    [
        ([], [], "Không tìm thấy file .xlsx export sprint (có sheet Sprint N). Chỉ định bằng --sprint."),
        (
            ["a.xlsx:sprint", "b.xlsx:sprint", "devs.xlsx:devs", "h.csv"],
            [],
            "Có nhiều file .xlsx export sprint (có sheet Sprint N): a.xlsx, b.xlsx.",
        ),
        (["a.xlsx:sprint", "h.csv"], [], "Không tìm thấy file devs.xlsx. Chỉ định bằng --devs."),
        (
            ["a.xlsx:sprint", "~$a.xlsx", ".b.xlsx", "devs.xlsx:devs", "h.csv", "g.csv"],
            [],
            "Có nhiều file lịch sử: g.csv, h.csv.",
        ),
        (["a.xlsx:sprint", "devs.xlsx:devs", "t.xlsx:history", "h.csv"], [], "Có nhiều file lịch sử: h.csv, t.xlsx."),
        (["a.xlsx"], [], "Không mở được file"),
        ([], ["--sprint", "missing.xlsx"], "Không có file 'missing.xlsx' (--sprint)."),
        (
            ["a.xlsx:sprint", "devs.xlsx:devs", "a.md", "b.md"],
            [],
            "Có nhiều file luật .md: a.md, b.md. Chỉ định một file bằng --rules.",
        ),
        (["a.xlsx:sprint", "devs.xlsx:devs", "a.md"], [], "không có bảng luật (bảng có cột Loại và Dev)."),
        (["a.xlsx:sprint", "devs.xlsx:devs"], ["--rules", "missing.md"], "Không có file 'missing.md' (--rules)."),
        (["a.xlsx:sprint", "devs.xlsx:devs", "a.md:rules"], [], "dòng 5: không có dev mã 'Nobody' trong file dev."),
        (["a.xlsx:sprint", "devs.xlsx:devs"], ["--today", "31/02/2026"], "--today '31/02/2026': không đọc được ngày"),
    ],
)
def test_input_errors_exit_2_with_a_message(tmp_path: Path, capsys, files, flags, message) -> None:
    """Discovery reads content: an .xlsx with `Sprint N` sheets is the export, any other .xlsx or .csv is history."""
    source = tmp_path / "input"
    source.mkdir()
    for spec in files:
        name, _, kind = spec.partition(":")
        if kind == "sprint":
            build_sprint_workbook(source / name, {"Sprint 1": [ORDER]})
        elif kind == "devs":
            build_devs(source / name, [{"Tên": "Dev A", "Mã": "DevA", "Level": "middle", "Nhận việc": "Y"}])
        elif kind == "history":
            build_history_xlsx(source / name, {"Tháng 9": [HISTORY]})
        elif kind == "rules":
            (source / name).write_text(RULES.replace("DevB", "Nobody"), encoding="utf-8")
        else:
            (source / name).write_bytes(b"")

    assert main([*FILE, "--input", str(source), "--out", str(tmp_path / "out"), "--ai", "off", *flags]) == 2

    assert message in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_missing_input_directory_exits_2(tmp_path: Path, capsys) -> None:
    assert main([*FILE, "--input", str(tmp_path / "nope"), "--ai", "off"]) == 2
    assert "Không có thư mục input" in capsys.readouterr().err


def test_report_name_uses_a_windows_safe_slug() -> None:
    now = datetime(2026, 10, 6, 14, 30, 0)
    assert report_name("Sprint 10", now) == "assignment_sprint-10_20261006-143000.xlsx"
    assert report_name("Sprint: 1/2", now) == "assignment_sprint_-1_2_20261006-143000.xlsx"


def test_without_history_file_the_older_sheets_are_the_history_and_the_report_is_written(tmp_path: Path, capsys):
    source = _inputs(tmp_path / "input")
    (source / "history.csv").unlink()
    out = tmp_path / "out"

    assert main([*FILE, "--input", str(source), "--out", str(out), "--ai", "off"]) == 0

    printed = capsys.readouterr().out
    assert "Lịch sử: sheet Sprint 1 trong workbook (không có file lịch sử)" in printed
    workbook = load_workbook(_report(out))
    assignment = list(workbook["Phân công"].iter_rows(values_only=True))[1]
    assert assignment[-4].startswith("Làm version gần nhất của Demo (Sprint 1: 1.0.1 - Add ads)")
    findings = list(workbook["Cảnh báo"].iter_rows(values_only=True))[1:]
    assert [row[:3] for row in findings] == [("INFO", "HISTORY-FROM-WORKBOOK", "Sprint 1")]


def test_tech_manager_xlsx_beside_the_export_is_found_as_history(tmp_path: Path, capsys) -> None:
    source = _inputs(tmp_path / "input")
    (source / "history.csv").unlink()
    target_order = {**HISTORY, "Tên task": "1.0.1 - Add ads", "Người làm": "", "Sprint": "Sprint 2 (10/6 - 10/17)"}
    build_history_xlsx(source / "tech.xlsx", {"Tháng 9": [HISTORY], "Tháng 10": [target_order]})
    out = tmp_path / "out"

    assert main([*FILE, "--input", str(source), "--out", str(out), "--ai", "off"]) == 0

    assert "Lịch sử: file tech.xlsx (1 đơn gốc)" in capsys.readouterr().out
    assignment = list(load_workbook(_report(out))["Phân công"].iter_rows(values_only=True))[1]
    assert assignment[-4].startswith("Làm version gần nhất của Demo (Sprint 1 (9/22 - 10/3): 1.0.0)")


def test_the_md_file_in_the_input_folder_is_the_rules_file_and_its_pin_reaches_the_report(tmp_path: Path, capsys):
    source = _inputs(tmp_path / "input")
    build_devs(source / "devs.xlsx", TWO_DEVS)
    (source / "luat.md").write_text(RULES.replace("\n", "\r\n"), encoding="utf-8-sig")
    out = tmp_path / "out"

    assert main([*FILE, "--input", str(source), "--out", str(out), "--ai", "off"]) == 0

    printed = capsys.readouterr().out
    assert "Luật TM: file luat.md (1 luật, 1 có hiệu lực ngày " in printed
    assert "STT 1 · Demo 1.0.1 - Add ads [M] → DevB (dự phòng: DevA)" in printed
    assignment = list(load_workbook(_report(out))["Phân công"].iter_rows(values_only=True))[1]
    assert assignment[-4].startswith("Luật TM dòng 5: chỉ định DevB cho Demo (thử) · Chưa làm Demo")


@pytest.mark.parametrize(
    ("today", "shown", "count"), [("2026-09-15", "15/09/2026", 0), ("30/09/2026", "30/09/2026", 1)]
)
def test_today_replaces_the_clock_for_the_history_window(tmp_path: Path, capsys, today, shown, count) -> None:
    """The history order's sprint starts 22/09: on 15/09 it has not started, so it is not history yet (spec §5.1)."""
    source = _inputs(tmp_path / "input")

    assert main([*FILE, "--input", str(source), "--out", str(tmp_path / "out"), "--ai", "off", "--today", today]) == 0

    printed = capsys.readouterr().out
    assert f"Ngày chạy: {shown} (--today)" in printed
    assert f"Lịch sử: file history.csv ({count} đơn gốc)" in printed


@pytest.mark.parametrize(
    ("today", "rules_day", "pic"), [("2026-10-20", "20/10/2026", "DevB"), ("2026-10-01", "06/10/2026", "DevA")]
)
def test_today_replaces_the_clock_for_the_rules_day(tmp_path: Path, capsys, today, rules_day, pic) -> None:
    """A pin dated 18/10–31/10 acts on 20/10; on 01/10 the rules day is the sprint's first day, 06/10 (A34)."""
    source = _inputs(tmp_path / "input")
    build_devs(source / "devs.xlsx", TWO_DEVS)
    dated = (
        "| Loại | Dev | App | Từ ngày | Đến ngày |\n|---|---|---|---|---|\n"
        "| Chỉ định | DevB | Demo | 18/10/2026 | 31/10/2026 |\n"
    )
    (source / "luat.md").write_text(dated, encoding="utf-8")

    assert main([*FILE, "--input", str(source), "--out", str(tmp_path / "out"), "--ai", "off", "--today", today]) == 0

    printed = capsys.readouterr().out
    assert f"có hiệu lực ngày {rules_day})" in printed
    assert f"STT 1 · Demo 1.0.1 - Add ads [M] → {pic} " in printed


def test_without_hours_in_the_history_the_older_sheets_calibrate_the_ai(tmp_path: Path, monkeypatch) -> None:
    """The Tech manager export has no hours; Sprint 1's `Ước lượng (h)` becomes the AI's example (spec §6.4, A19)."""
    source = _inputs(tmp_path / "input")
    older = {**ORDER, "Task": "1.0.0 - First release", "Người làm": "Dev A", "Ước lượng (h)": 12}
    build_sprint_workbook(source / "export.xlsx", {"Sprint 2": [ORDER], "Sprint 1": [older]})
    prompts = []
    monkeypatch.setattr(ai_cli, "run_ai", lambda tool, prompt, **_: prompts.append(prompt) or AiReply(tool, "[]", None))

    assert main([*FILE, "--input", str(source), "--out", str(tmp_path / "out")]) == 0

    (prompt,) = prompts
    assert "(for calibration):\n- Demo · 1.0.0 - First release · 12h\n" in prompt
