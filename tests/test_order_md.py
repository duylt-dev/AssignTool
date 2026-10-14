"""The order file of BA/MO (bot spec §7.1): title, field table, description, input errors."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from scrumbot.core.errors import InputError
from scrumbot.input.files.order_md import read_order

FULL = """# Demo 1.0.2 - Add ads native

| Trường | Giá trị |
|---|---|
| ID | n_1 |
| App Name | Demo |
| Ưu tiên | high |
| Hạn | 16/10/2026 |

Thêm native ad ở màn Home.

| Màn | Vị trí |
|---|---|
| Home | dưới danh sách |
"""


def _write(tmp_path: Path, text: str, name: str = "don.md") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_title_fields_and_every_other_line_as_the_description(tmp_path: Path) -> None:
    draft = read_order(_write(tmp_path, FULL))

    assert (draft.title, draft.order_id, draft.app, draft.priority_raw, draft.due) == (
        "Demo 1.0.2 - Add ads native",
        "n_1",
        "Demo",
        "high",
        date(2026, 10, 16),
    )
    assert draft.description.startswith("Thêm native ad ở màn Home.")
    assert "| Home | dưới danh sách |" in draft.description  # another table stays in the description
    assert "Trường" not in draft.description


def test_free_text_without_title_or_table_takes_the_file_name(tmp_path: Path) -> None:
    draft = read_order(_write(tmp_path, "\nChỉnh sửa luồng scan\n* Link: https://x.test\n", "req_test.md"))

    assert (draft.title, draft.order_id, draft.app, draft.priority_raw, draft.due) == ("req_test", "", "", "", None)
    assert draft.description == "Chỉnh sửa luồng scan\n* Link: https://x.test"


def test_empty_cells_leave_the_fields_empty(tmp_path: Path) -> None:
    text = "# T\n\n| Trường | Giá trị |\n|---|---|\n| ID | |\n| App | Demo |\n| Hạn |  |\n\nMô tả\n"
    draft = read_order(_write(tmp_path, text))

    assert (draft.order_id, draft.app, draft.due, draft.description) == ("", "Demo", None, "Mô tả")


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("| Trường | Giá trị |\n|---|---|\n| Uu tien | high |\n", "dòng 3: trường 'Uu tien' không hợp lệ"),
        ("| Trường | Giá trị |\n|---|---|\n| Hạn | 31/02/2026 |\n", "Hạn '31/02/2026' không đọc được"),
    ],
)
def test_a_wrong_field_is_an_input_error_naming_it(tmp_path: Path, text: str, message: str) -> None:
    with pytest.raises(InputError, match=message):
        read_order(_write(tmp_path, text))
