from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from assigntool.dev_reader import read_devs
from assigntool.errors import InputError
from assigntool.model import Level
from tests.conftest import build_devs


def _dev(**values: object) -> dict:
    return {"Tên": "Ngọc Văn Linh", "Mã": "LinhNV", "Level": "middle+", "Nhận việc": "Y", **values}


def test_reads_leave_dates_from_cells_and_text(tmp_path: Path) -> None:
    path = tmp_path / "devs.xlsx"
    build_devs(
        path,
        [
            _dev(**{"Ngày nghỉ": datetime(2026, 10, 6)}),
            _dev(
                **{
                    "Tên": "Bùi Văn Tiến",
                    "Mã": "TienBV",
                    "Level": "junior",
                    "Nhận việc": "N",
                    "Ngày nghỉ": "07/10/2026, 2026-10-08",
                }
            ),
        ],
    )

    devs = read_devs(path)

    assert devs[0].level is Level.MIDDLE_PLUS
    assert devs[0].leave_days == (date(2026, 10, 6),)
    assert devs[1].active is False
    assert devs[1].leave_days == (date(2026, 10, 7), date(2026, 10, 8))


@pytest.mark.parametrize("field, value, message", [("Level", "lead", "junior"), ("Nhận việc", "maybe", "Y hoặc N")])
def test_rejects_bad_level_and_active_value(tmp_path: Path, field: str, value: str, message: str) -> None:
    path = tmp_path / "devs.xlsx"
    build_devs(path, [_dev(**{field: value})])

    with pytest.raises(InputError, match=message):
        read_devs(path)


@pytest.mark.parametrize("field", ["Tên", "Mã"])
def test_rejects_duplicate_name_or_code(tmp_path: Path, field: str) -> None:
    path = tmp_path / "devs.xlsx"
    second = _dev(Tên="Bùi Văn Tiến", Mã="TienBV")
    second[field] = _dev()[field]
    build_devs(path, [_dev(), second])

    with pytest.raises(InputError, match="bị trùng"):
        read_devs(path)
