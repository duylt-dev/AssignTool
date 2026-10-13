from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import Workbook

DEV_HEADERS = ["Tên", "Mã", "Level", "Nhận việc", "Ngày nghỉ"]


@pytest.fixture(autouse=True)
def _never_the_real_server(monkeypatch: pytest.MonkeyPatch) -> None:
    """The environment wins over `.env` (A54): a test that reaches for the API by mistake fails fast on a closed local
    port instead of calling the dev server with the real token."""
    monkeypatch.setenv("SCRUMBOT_API_BASE", "http://127.0.0.1:9")
    monkeypatch.setenv("SCRUMBOT_API_TOKEN", "test-token")


def build_devs(path: Path, rows: list[dict]) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(DEV_HEADERS)
    for row in rows:
        worksheet.append([row.get(header, "") for header in DEV_HEADERS])
    workbook.save(path)
