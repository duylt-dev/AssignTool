from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from assigntool.errors import InputError
from assigntool.history_reader import read_history
from tests.conftest import HISTORY_HEADERS, write_history_csv


def _row(**values: object) -> dict:
    return {
        "Sprint": "Sprint 9",
        "STT": 1,
        "Task": "Build feature",
        "Loại": "Task",
        "App Name": "App",
        "Người làm": "Ngọc Văn Linh",
        "Ước lượng (h)": "16,5",
        "Ngày tạo": "2026-10-06",
        **values,
    }


@pytest.mark.parametrize("bom, delimiter, date_style", [(True, ",", "iso"), (False, ";", "dmy")])
def test_reads_supported_csv_shapes(tmp_path: Path, bom: bool, delimiter: str, date_style: str) -> None:
    path = tmp_path / "history.csv"
    write_history_csv(
        path, [_row(**{"Ngày tạo": date(2026, 10, 6)})], bom=bom, delimiter=delimiter, date_style=date_style
    )

    history = read_history(path)

    assert history[0].created == date(2026, 10, 6)
    assert history[0].hours == 16.5


def test_ignores_subtasks_and_rows_without_app_or_people(tmp_path: Path) -> None:
    path = tmp_path / "history.csv"
    write_history_csv(path, [_row(Loại="Subtask"), _row(**{"App Name": ""}), _row(**{"Người làm": ""})])

    assert read_history(path) == ()


def test_missing_required_header_and_bad_date_name_line(tmp_path: Path) -> None:
    path = tmp_path / "history.csv"
    write_history_csv(path, [_row(**{"Ngày tạo": "not-a-date"})])
    with pytest.raises(InputError, match="dòng 2.*Ngày tạo"):
        read_history(path)

    lines = path.read_text(encoding="utf-8").splitlines()
    headers = lines[0].split(",")
    headers[HISTORY_HEADERS.index("Sprint")] = "Removed"
    path.write_text(",".join(headers) + "\n" + lines[1] + "\n", encoding="utf-8")
    with pytest.raises(InputError, match="thiếu cột 'Sprint'"):
        read_history(path)
