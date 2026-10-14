from datetime import date
from pathlib import Path

import pytest

from scrumbot.core.errors import InputError
from scrumbot.core.model import RuleKind, TeamRule
from scrumbot.input.files.rules_md import read_rules

EXAMPLE = """\
# Luật giao việc

Ghi chú tự do: | dòng này không phải bảng vì không có dòng phân cách.

| Loại       | Dev    | App       | Số đơn | Từ ngày    | Đến ngày   | Ghi chú                 |
|------------|--------|-----------|--------|------------|------------|-------------------------|
| Chỉ định   | LinhNV | AR Dog    |        |            |            | Linh giữ AR Dog         |
| Không giao | MinhNM |           |        | 06/10/2026 | 17/10/2026 | Minh làm MVP sprint này |
|            |        |           |        |            |            |                         |
| Tối đa đơn | AnTD   |           | 1      | 2026-10-06 | 2026-10-17 |                         |

## Bảng khác, không phải luật

| App | Ai giữ |
|:---:|--------|
| VPN | Linh   |

## Sprint 11

| Dev      | Loại    | App         | Ghi chú      | Cột lạ |
|----------|---------|-------------|--------------|--------|
| **TiếnBV** | ưu tiên | `PS Remote` | học app \\| kèm Minh | x |
"""


def write(tmp_path: Path, text: str, *, bom: bool = False) -> Path:
    path = tmp_path / "luat.md"
    path.write_text(text, encoding="utf-8-sig" if bom else "utf-8")
    return path


def test_reads_every_rules_table_by_header_name_and_skips_notes_other_tables_and_empty_rows(tmp_path: Path) -> None:
    rules = read_rules(write(tmp_path, EXAMPLE, bom=True))

    assert rules == (
        TeamRule(kind=RuleKind.PIN, dev="LinhNV", line=7, app="AR Dog", note="Linh giữ AR Dog"),
        TeamRule(
            kind=RuleKind.EXCLUDE,
            dev="MinhNM",
            line=8,
            start=date(2026, 10, 6),
            end=date(2026, 10, 17),
            note="Minh làm MVP sprint này",
        ),
        TeamRule(
            kind=RuleKind.MAX_ORDERS, dev="AnTD", line=10, max_orders=1, start=date(2026, 10, 6), end=date(2026, 10, 17)
        ),
        TeamRule(kind=RuleKind.PREFER, dev="TiếnBV", line=22, app="PS Remote", note="học app | kèm Minh"),
    )


def test_cells_are_nfc_normalised(tmp_path: Path) -> None:
    nfd = "TiếnBV"  # "TiếnBV" written as NFD, as macOS editors may save it
    text = f"| Loại | Dev | App |\n|---|---|---|\n| Ưu tiên | {nfd} | Speak2 |\n"

    (rule,) = read_rules(write(tmp_path, text))

    assert rule.dev == "TiếnBV"


def test_a_table_inside_a_code_block_is_an_example_not_a_rule(tmp_path: Path) -> None:
    example = "| Loại | Dev | App |\n|---|---|---|\n| Chỉ định | LinhNV | AR Dog |\n"
    text = f"Ví dụ:\n\n```markdown\n{example}```\n\n{example.replace('LinhNV', 'MinhNM')}"

    (rule,) = read_rules(write(tmp_path, text))

    assert (rule.dev, rule.line) == ("MinhNM", 11)
    with pytest.raises(InputError, match="không có bảng luật"):
        read_rules(write(tmp_path, f"~~~\n{example}~~~\n"))


def test_a_table_with_only_a_header_gives_no_rules(tmp_path: Path) -> None:
    assert read_rules(write(tmp_path, "| Loại | Dev | App |\n|---|---|---|\n")) == ()


HEADER = "| Loại | Dev | App | Số đơn | Từ ngày | Đến ngày |\n|---|---|---|---|---|---|\n"


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("# Luật\n\nLinh giữ AR Dog.\n", "không có bảng luật (bảng có cột Loại và Dev)."),
        ("| Loại | App |\n|---|---|\n| Chỉ định | AR Dog |\n", "không có bảng luật"),
        (HEADER + "| Giao | LinhNV | AR Dog | | | |\n", "dòng 3, cột 'Loại': 'Giao' không hợp lệ"),
        (HEADER + "| Chỉ định | | AR Dog | | | |\n", "dòng 3: thiếu Dev."),
        (HEADER + "| Chỉ định | LinhNV | | | | |\n", "dòng 3: luật Chỉ định cần cột App."),
        (HEADER + "| Ưu tiên | LinhNV | | | | |\n", "dòng 3: luật Ưu tiên cần cột App."),
        (HEADER + "| Tối đa đơn | LinhNV | | | | |\n", "dòng 3: luật Tối đa đơn cần cột Số đơn."),
        (HEADER + "| Tối đa đơn | LinhNV | VPN | 2 | | |\n", "dòng 3: luật Tối đa đơn không dùng cột App."),
        (HEADER + "| Không giao | LinhNV | | 2 | | |\n", "dòng 3: luật Không giao không dùng cột Số đơn."),
        (HEADER + "| Tối đa đơn | LinhNV | | 0 | | |\n", "dòng 3, cột 'Số đơn' phải là số nguyên từ 1 trở lên."),
        (HEADER + "| Tối đa đơn | LinhNV | | 1.5 | | |\n", "cột 'Số đơn' phải là số nguyên từ 1 trở lên."),
        (HEADER + "| Không giao | LinhNV | | | 6/10 | |\n", "dòng 3, cột 'Từ ngày': không đọc được ngày '6/10'"),
        (HEADER + "| Không giao | LinhNV | | | 17/10/2026 | 06/10/2026 |\n", "dòng 3: Từ ngày sau Đến ngày."),
    ],
)
def test_broken_rules_are_input_errors_naming_the_line(tmp_path: Path, text: str, message: str) -> None:
    path = write(tmp_path, text)

    with pytest.raises(InputError) as error:
        read_rules(path)

    assert str(error.value).startswith(f"File '{path}'")
    assert message in str(error.value)
