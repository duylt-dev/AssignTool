"""Write the Excel report (spec §10). The only module that writes openpyxl workbooks."""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from assigntool.model import Assignment, DevSummary, Finding, Level, Result

_EXTRA_HEADERS = (
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
_FINDING_HEADERS = ("Mức", "Mã", "Vị trí", "Nội dung")
_DEV_HEADERS = (
    "Mã",
    "Tên",
    "Level",
    "Việc dở sprint trước",
    "Ngày nghỉ",
    "Đơn giao sẵn",
    "Đơn tool đề xuất",
    "Tổng đơn",
    "Tổng giờ ước tính",
    "Danh sách đơn",
    "App đã làm",
)
_LEVEL_NAMES = {
    Level.JUNIOR: "junior",
    Level.JUNIOR_PLUS: "junior+",
    Level.MIDDLE: "middle",
    Level.MIDDLE_PLUS: "middle+",
    Level.SENIOR: "senior",
}
_MAX_WIDTH = 60


def report_name(sheet_name: str, now: datetime) -> str:
    """`Sprint 10` at 2026-10-06 14:30:00 → `assignment_sprint-10_20261006-143000.xlsx` (best practices §5)."""
    slug = re.sub(r"[^a-z0-9._-]", "_", re.sub(r"\s+", "-", sheet_name.strip().lower()))
    return f"assignment_{slug}_{now:%Y%m%d-%H%M%S}.xlsx"


def write_report(result: Result, headers: tuple[str, ...], out_dir: Path, now: datetime) -> Path:
    """Write the three sheets to `<name>.tmp`, then rename it (best practices §6)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / report_name(result.sheet_name, now)
    workbook = Workbook()
    _assignments_sheet(workbook.active, result.assignments, headers)
    _findings_sheet(workbook.create_sheet("Cảnh báo"), result.findings)
    _devs_sheet(workbook.create_sheet("Tải dev"), result.devs)
    temporary = path.with_name(path.name + ".tmp")
    workbook.save(temporary)
    os.replace(temporary, path)
    return path


def _assignments_sheet(sheet: Worksheet, assignments: tuple[Assignment, ...], headers: tuple[str, ...]) -> None:
    sheet.title = "Phân công"
    sheet.append([*headers, *_EXTRA_HEADERS])
    for item in assignments:
        cells = list(item.order.row.cells[: len(headers)])
        cells += [None] * (len(headers) - len(cells))
        size = item.size
        backups = (*item.backups, "", "")
        sheet.append(
            [
                *cells,
                size.size.name + (" (mặc định)" if size.is_default else ""),
                size.size.value,
                size.reason,
                ", ".join(item.pic_names),
                ", ".join(item.pic_codes),
                item.source.value,
                item.reason,
                backups[0],
                backups[1],
            ]
        )
    _finish(sheet)


def _findings_sheet(sheet: Worksheet, findings: tuple[Finding, ...]) -> None:
    sheet.append(list(_FINDING_HEADERS))
    if not findings:
        sheet.append(["Không có cảnh báo"])
    for finding in findings:
        sheet.append([finding.severity.value, finding.code, finding.where, finding.message])
    _finish(sheet)


def _devs_sheet(sheet: Worksheet, devs: tuple[DevSummary, ...]) -> None:
    sheet.append(list(_DEV_HEADERS))
    for item in devs:
        orders = "Nghỉ cả sprint" if item.on_leave_all_sprint else "\n".join(item.orders)
        sheet.append(
            [
                item.dev.code,
                item.dev.name,
                _LEVEL_NAMES[item.dev.level],
                item.carry_over,
                item.leave_days,
                item.preassigned,
                item.proposed,
                item.preassigned + item.proposed,
                item.hours,
                orders,
                ", ".join(item.known_apps),
            ]
        )
    _finish(sheet)


def _finish(sheet: Worksheet) -> None:
    """Bold, frozen header; wrapped text; widths from the longest line in each column, capped."""
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    sheet.freeze_panes = "A2"
    widths: dict[int, int] = {}
    for row in sheet.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            if cell.value is not None:
                longest = max(len(line) for line in str(cell.value).splitlines() or [""])
                widths[cell.column] = max(widths.get(cell.column, 0), longest)
    for column, width in widths.items():
        sheet.column_dimensions[get_column_letter(column)].width = min(max(width + 2, 8), _MAX_WIDTH)
