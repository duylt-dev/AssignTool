"""`scrumbot review <file>` then `scrumbot assign <file>` end to end against a real local HTTP server (bot spec §7): the
order file in the sprint, the review, the passed review that assign needs, the AI prompts, the Markdown reports, the
memory. Nothing reaches the dev server; the run day is pinned (LLM.md §8)."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import closing
from datetime import date, datetime
from pathlib import Path

import pytest

from scrumbot.ai import tools as ai_cli
from scrumbot.ai.prompt import AiReply
from scrumbot.cli import main
from scrumbot.input.dev_api.config import TECH_MANAGER_LIST
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
| Người chịu trách nhiệm | TestBA – BA |
| Bằng chứng | Ảnh dashboard doanh thu |

Thêm IAP gói tháng, liên hệ BA: TestBA.
* Link UI [https://www.figma.com/design/abc/Demo](https://www.figma.com/design/abc/Demo)
Nghiệm thu khi: mua sandbox gói tháng thành công.
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


def _cli(command: str, source: Path, tmp_path: Path, order: Path, *flags: str) -> int:
    paths = ["--input", str(source), "--state", str(tmp_path / "state"), "--out", str(tmp_path / "out")]
    return main([command, str(order), *paths, "--today", "2026-10-08", *flags])


def _report(tmp_path: Path) -> str:
    return (tmp_path / "out" / "output.md").read_text(encoding="utf-8")


def test_a_new_order_gets_a_pic_and_the_report_says_why(
    server: FakeDevServer, source: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    prompts = []

    def fake(tool, prompt, *, model, timeout):
        prompts.append(prompt)
        if prompt.startswith("You review"):
            return AiReply(tool, '{"type": "iap", "missing": [], "questions": ["Gói tháng giá bao nhiêu?"]}', None)
        return AiReply(tool, '[{"stt": 1, "size": "S", "reason": "x"}, {"stt": 2, "size": "L", "reason": "IAP"}]', None)

    monkeypatch.setattr(ai_cli, "run_ai", fake)
    order = _order(source)

    assert _cli("review", source, tmp_path, order, "--ai", "agy") == 0
    review = _report(tmp_path)
    assert "## Review: đạt\n\nMô tả đủ ý của mẫu IAP (AI chấm).\n\n" in review
    assert "- Gói tháng giá bao nhiêu?" in review
    assert (
        "| Loại đơn | IAP (AI) |\n| Người chịu trách nhiệm | TestBA – BA |\n| Bằng chứng | Ảnh dashboard doanh thu |"
        in (review)
    )
    assert "Review: đạt (đủ ý mẫu IAP; 1 câu hỏi của AI)" in capsys.readouterr().out
    assert _cli("assign", source, tmp_path, order, "--ai", "agy") == 0

    asked, sized = prompts
    for prompt in prompts:
        assert "Thêm IAP gói tháng, liên hệ BA: [người]. * Link UI [link Figma] Nghiệm thu khi:" in prompt
        assert all(text not in prompt for text in ("TestBA", "figma.com", LINH, AN, OUTSIDER, "AnTD", "Ảnh dashboard"))
    assert asked.startswith("You review") and sized.startswith("You estimate")
    report = _report(tmp_path)
    assert report.startswith("# Giao đơn: Demo 1.0.2 - Add IAP\n")
    assert "- **PIC đề xuất: LinhNV**" in report
    assert "- Độ lớn (AI): L (32h): IAP" in report
    assert "| Đơn | Đơn mới, chưa có trên hệ thống (tính là STT 2 của Sprint 2) |" in report
    assert "| LinhNV | middle+ | Làm version gần nhất | 1 | 32h / " in report and "| **PIC** |" in report
    assert "## Rủi ro và phương án dự phòng" in report and "## Cảnh báo dữ liệu" in report
    assert OUTSIDER not in report and "## Review" not in report and "Gói tháng giá" not in report
    printed = capsys.readouterr().out
    assert "Đơn: Demo 1.0.2 - Add IAP (đơn mới, STT 2 của Sprint 2)" in printed
    assert "PIC đề xuất: LinhNV (dự phòng: " in printed
    assert not list((tmp_path / "out").glob("*.xlsx")) and not list((tmp_path / "out").glob("*.tmp"))
    with closing(sqlite3.connect(tmp_path / "state" / "scrumbot.sqlite")) as db:  # only the other orders' answers
        tables = db.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name").fetchall()
        assert tables == [("ai_answers",), ("reviews",)]
        assert db.execute("SELECT order_id FROM ai_answers").fetchall() == [("t",)]
        assert db.execute("SELECT origin FROM reviews").fetchall() == [(str(order),)]


def test_the_order_of_the_file_is_sized_again_on_every_run(
    server: FakeDevServer, source: Path, tmp_path: Path, monkeypatch
) -> None:
    sized = []

    def fake(tool, prompt, *, model, timeout):
        sized.append(prompt.count("\n- STT "))
        return AiReply(tool, '[{"stt": 1, "size": "S", "reason": "x"}, {"stt": 2, "size": "M", "reason": "y"}]', None)

    monkeypatch.setattr(ai_cli, "run_ai", fake)
    order = _order(source, "t")  # held on the system: no review needed (A87)

    assert _cli("assign", source, tmp_path, order, "--ai", "agy") == 0
    assert _cli("assign", source, tmp_path, order, "--ai", "agy") == 0

    assert sized == [1, 1]  # the only order is the file's, never taken from the memory


def test_an_order_already_taken_on_the_system_is_not_reviewed_and_is_kept(
    server: FakeDevServer, source: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    def no_ai(*_, **__):
        raise AssertionError("an order with a Người làm is not reviewed (A87)")

    monkeypatch.setattr(ai_cli, "run_ai", no_ai)
    order = _order(source, "t")

    assert _cli("review", source, tmp_path, order, "--ai", "agy") == 0
    assert (
        "## Review: không cần\n\nĐơn đã có người làm trên hệ thống: bot giữ nguyên, không review. "
        f"Chạy `scrumbot assign {order}` để xem người làm và rủi ro.\n\n## Thông tin đơn\n"
    ) in _report(tmp_path)
    assert "Review: không cần (đơn đã có người làm)" in capsys.readouterr().out
    assert _cli("assign", source, tmp_path, order, "--ai", "off") == 0

    report = _report(tmp_path)
    assert "- **Đã có người làm trên hệ thống: AnTD.** Bot giữ nguyên, không đề xuất PIC khác." in report
    assert "| Đơn | Đơn trên hệ thống, ID t, STT 1 (nối theo ID) |" in report
    assert "| AnTD | junior+ | Chưa làm | 1 | 16h / " in report and "| **Người làm** |" in report


@pytest.mark.parametrize("command", ["review", "assign"])
@pytest.mark.parametrize(
    ("order_id", "missing", "message"),
    [
        ("zz", False, "Không có đơn gốc ID 'zz' trong Sprint 2 (10/6 - 10/17)."),
        ("", True, "Không có file đơn"),
    ],
)
def test_input_errors_exit_2_without_a_report(
    server: FakeDevServer, source: Path, tmp_path: Path, capsys, order_id, missing, message, command
) -> None:
    order = source / "nope.md" if missing else _order(source, order_id)

    assert _cli(command, source, tmp_path, order, "--ai", "off") == 2

    assert message in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_an_order_that_is_not_ready_gets_only_what_to_fix_and_cannot_be_assigned(
    server: FakeDevServer, source: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    def no_ai(*_, **__):
        raise AssertionError("the AI is not called before the review passes (A86)")

    monkeypatch.setattr(ai_cli, "run_ai", no_ai)
    order = source / "don.md"
    order.write_text("# Demo 1.0.3 - Fix\n\n| Trường | Giá trị |\n|---|---|\n| Ưu tiên | urgent |\n\nSửa lỗi.\n")

    assert _cli("review", source, tmp_path, order, "--ai", "agy") == 0

    report = _report(tmp_path)
    assert report.startswith("# Review đơn: Demo 1.0.3 - Fix\n\nSprint 2 (06/10/2026 – 17/10/2026) · chạy 08/10/2026 ")
    assert report.endswith(
        "## Review: chưa đạt\n\n"
        f"Sửa các mục dưới đây rồi chạy lại `scrumbot review {order}`:\n\n"
        "- `REVIEW-APP`: Thiếu App: ghi tên app vào dòng App của file đơn.\n"
        "- `REVIEW-DUE`: Đơn chưa có Hạn: ghi dòng Hạn của file đơn (YYYY-MM-DD hoặc DD/MM/YYYY).\n"
        "- `REVIEW-OWNER`: Thiếu người chịu trách nhiệm: ghi dòng Người chịu trách nhiệm của file đơn (người trả lời "
        "Dev về đơn).\n"
        "- `REVIEW-EVIDENCE`: Đơn urgent là đơn Khẩn cấp nhưng chưa có Bằng chứng: ghi dòng Bằng chứng của file đơn "
        "(ảnh dashboard, email store/đối tác, số liệu KPI), hoặc hạ Ưu tiên về normal.\n"
        "- `REVIEW-DESC`: Mô tả quá ngắn (8 ký tự, cần từ 30, không tính link): ghi rõ các hạng mục cần làm.\n"
        '- `REVIEW-ACCEPT`: Mô tả chưa có mục "Nghiệm thu khi": ghi các điều kiện kiểm tra được, đủ để tester viết '
        "test case.\n"
        "\n## Thông tin đơn\n\n| Trường | Giá trị |\n|---|---|\n"
        "| Đơn | Đơn mới, chưa có trên hệ thống (tính là STT 2 của Sprint 2) |\n"
        f"| File đơn | {order} |\n| App | trống |\n| Ưu tiên | urgent |\n| Hạn | trống |\n| Loại đơn | trống |\n"
        "| Người chịu trách nhiệm | trống |\n| Bằng chứng | trống |\n| Mô tả AI đọc | Sửa lỗi. |\n"
    )
    assert "Kết luận" not in report and "Rủi ro" not in report
    printed = capsys.readouterr().out
    assert "Đơn: Demo 1.0.3 - Fix (đơn mới, STT 2 của Sprint 2)\nReview: chưa đạt (6 mục)\n- REVIEW-APP: " in printed
    assert f"Báo cáo: {tmp_path / 'out' / 'output.md'}" in printed
    assert not (tmp_path / "state" / "scrumbot.sqlite").exists()

    assert _cli("assign", source, tmp_path, order, "--ai", "agy") == 2

    assert f"Lỗi: Đơn chưa qua review, hoặc đã đổi sau lần review đạt gần nhất: review lại '{order}'" in (
        capsys.readouterr().err
    )
    assert _report(tmp_path) == report  # nothing written


def test_a_ready_order_is_reviewed_once_the_file_is_fixed_then_assigned(
    server: FakeDevServer, source: Path, tmp_path: Path, capsys
) -> None:
    order = source / "don.md"
    fields = "| App | Demo |\n| Hạn | 16/10/2026 |\n| Người chịu trách nhiệm | TaiDT – BA |\n"
    order.write_text(f"# Demo 1.0.3 - Fix\n\n| Trường | Giá trị |\n|---|---|\n{fields}\nSửa lỗi.\n")
    assert _cli("review", source, tmp_path, order, "--ai", "off") == 0
    assert "- `REVIEW-DESC`: Mô tả quá ngắn (8 ký tự" in _report(tmp_path)

    order.write_text(order.read_text(encoding="utf-8") + "Sửa crash khi mở màn cài đặt. Nghiệm thu khi: không crash.\n")
    assert _cli("review", source, tmp_path, order, "--ai", "off") == 0

    review = _report(tmp_path)
    assert (
        "## Review: đạt\n\nChưa chấm mô tả theo mẫu loại đơn (AI tắt hoặc lỗi).\n\n"
        "Không có câu hỏi của AI (AI tắt hoặc lỗi).\n\n"
        f"Chạy `scrumbot assign {order}` để bot đề xuất PIC. Sửa file đơn sau lần review này thì phải review lại.\n\n"
        "## Thông tin đơn\n"
    ) in review
    assert "| Mô tả AI đọc | Sửa lỗi. Sửa crash khi mở màn cài đặt. Nghiệm thu khi: không crash. |" in review
    assert (
        f"Review: đạt (chưa chấm theo mẫu; không có câu hỏi của AI: tắt AI)\nTiếp theo: scrumbot assign {order}\n"
        in (capsys.readouterr().out)
    )

    assert _cli("assign", source, tmp_path, order, "--ai", "off") == 0

    report = _report(tmp_path)
    assert "- **PIC đề xuất: LinhNV**" in report and "Sổ rủi ro cả sprint: " in report


def test_the_ai_s_template_check_blocks_an_order_that_misses_points_of_its_type(
    server: FakeDevServer, source: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    """D65: the AI names the missing points of the file's type; the message is the template's, assign is refused."""

    def fake(tool, prompt, *, model, timeout):
        assert "The order's type is iap (IAP)" in prompt and "8 order types" not in prompt
        return AiReply(tool, '{"type": "iap", "missing": [3, 2], "questions": ["Paywall ở màn nào?"]}', None)

    monkeypatch.setattr(ai_cli, "run_ai", fake)
    order = _order(source)
    order.write_text(
        order.read_text(encoding="utf-8").replace("| Hạn | 16/10/2026 |", "| Hạn | 16/10/2026 |\n| Loại đơn | IAP |")
    )

    assert _cli("review", source, tmp_path, order, "--ai", "agy") == 0

    report = _report(tmp_path)
    assert (
        "## Review: chưa đạt\n\n"
        f"Sửa các mục dưới đây rồi chạy lại `scrumbot review {order}`:\n\n"
        "- `REVIEW-TEMPLATE`: Mô tả chưa đủ ý của mẫu IAP (AI chấm): Paywall: màn nào, điều kiện hiển thị; Remote "
        "Config: key, giá trị mặc định.\n\n"
        "Câu hỏi của AI cho người lên đơn (không chặn; trả lời trong file đơn nếu cần):\n\n"
        "- Paywall ở màn nào?\n\n## Thông tin đơn\n"
    ) in report
    assert "| Loại đơn | IAP (file đơn) |" in report
    assert "Review: chưa đạt (1 mục)\n- REVIEW-TEMPLATE: Mô tả chưa đủ ý của mẫu IAP" in capsys.readouterr().out
    assert _cli("assign", source, tmp_path, order, "--ai", "agy") == 2
    assert "Đơn chưa qua review" in capsys.readouterr().err


def test_an_order_outside_the_8_types_passes_without_a_template_check(
    server: FakeDevServer, source: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setattr(
        ai_cli,
        "run_ai",
        lambda tool, *_, **__: AiReply(tool, '{"type": "other", "missing": [], "questions": []}', None),
    )
    order = _order(source)

    assert _cli("review", source, tmp_path, order, "--ai", "agy") == 0

    report = _report(tmp_path)
    assert (
        "## Review: đạt\n\nAI xếp đơn ngoài 8 loại đơn của quy trình (vd app mới, theo SRS riêng): chưa chấm theo "
        "mẫu.\n\nAI không có câu hỏi.\n\n"
    ) in report
    assert "| Loại đơn | ngoài 8 loại (AI) |" in report
    assert "Review: đạt (ngoài 8 loại đơn; 0 câu hỏi của AI)" in capsys.readouterr().out


def test_assign_needs_a_review_of_the_order_as_it_is_now(
    server: FakeDevServer, source: Path, tmp_path: Path, capsys
) -> None:
    order = _order(source)
    assert _cli("assign", source, tmp_path, order, "--ai", "off") == 2  # never reviewed
    assert "Đơn chưa qua review" in capsys.readouterr().err and not (tmp_path / "out").exists()

    assert _cli("review", source, tmp_path, order, "--ai", "off") == 0
    order.write_text(order.read_text(encoding="utf-8").replace("| Hạn | 16/10/2026 |", "| Hạn | 17/10/2026 |"))

    assert _cli("assign", source, tmp_path, order, "--ai", "off") == 2  # changed since the review
    assert "Đơn chưa qua review" in capsys.readouterr().err
    assert _report(tmp_path).startswith("# Review đơn: ")
