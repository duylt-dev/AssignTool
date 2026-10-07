"""The real sample of spec §12 (committed under input/, D18) and the inputs built from it at run time."""

from __future__ import annotations

from pathlib import Path

from assigntool.model import HistoryOrder, SprintSheet
from assigntool.normalize import header_key

SAMPLE = Path(__file__).resolve().parents[1] / "input" / "Maintain_update_Sprint_10_va_9.xlsx"
SKIP_REASON = f"thiếu file mẫu {SAMPLE}"

# The pool of D7 / spec §4. These four names are configuration (devs.xlsx), not data copied from input/.
DEVS = [
    {"Tên": "Ngọc Văn Linh", "Mã": "LinhNV", "Level": "middle+", "Nhận việc": "Y"},
    {"Tên": "Nguyễn Nhật Minh", "Mã": "MinhNM", "Level": "middle", "Nhận việc": "Y"},
    {"Tên": "Trần Đức An", "Mã": "AnTD", "Level": "junior+", "Nhận việc": "Y"},
    {"Tên": "Bùi Văn Tiến", "Mã": "TiếnBV", "Level": "junior", "Nhận việc": "Y"},
]


def history_rows(sheet: SprintSheet) -> list[dict]:
    """The sheet's "Task" rows in the history CSV columns of spec §5."""
    hours_index = next(i for i, header in enumerate(sheet.headers) if header_key(header) == "ước lượng (h)")
    return [
        {
            "Sprint": sheet.name,
            "STT": row.stt,
            "Task": row.title,
            "Loại": "Task",
            "App Name": row.app,
            "Người làm": ", ".join(row.assignees),
            "Ước lượng (h)": row.cells[hours_index] if row.cells[hours_index] is not None else "",
            "Ngày tạo": row.created.isoformat() if row.created else "",
        }
        for row in sheet.rows
        if row.kind == "Task"
    ]


def history_orders(sheet: SprintSheet) -> tuple[HistoryOrder, ...]:
    """The same rows as HistoryOrder values, for tests that skip the CSV."""
    return tuple(
        HistoryOrder(sheet.name, row.app, row.title, row.assignees, _hours(row, sheet), row.created)
        for row in sheet.rows
        if row.kind == "Task" and row.app and row.assignees and row.created
    )


def _hours(row, sheet: SprintSheet) -> float | None:
    index = next(i for i, header in enumerate(sheet.headers) if header_key(header) == "ước lượng (h)")
    value = row.cells[index]
    return float(value) if isinstance(value, (int, float)) else None
