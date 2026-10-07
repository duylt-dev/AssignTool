from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

from openpyxl import Workbook

SPRINT_HEADERS = [
    "STT",
    "Nhóm trạng thái",
    "Task",
    "Loại",
    "Task cha",
    "App Name.",
    "Trạng thái",
    "Người làm",
    "Ưu tiên",
    "Hạn",
    "Ước lượng (h)",
    "Người tạo",
    "Điểm",
    "Git Pull Request",
    "Ngày tạo",
    "Mô tả",
]

DEV_HEADERS = ["Tên", "Mã", "Level", "Nhận việc", "Ngày nghỉ"]
HISTORY_HEADERS = ["Sprint", "STT", "Task", "Loại", "App Name", "Người làm", "Ước lượng (h)", "Ngày tạo"]


def build_sprint_workbook(
    path: Path, sheets: dict[str, list[dict]], dates: dict[str, tuple[str, str]] | None = None
) -> None:
    workbook = Workbook()
    workbook.remove(workbook.active)
    for name, rows in sheets.items():
        worksheet = workbook.create_sheet(name)
        worksheet.append([f"{name} (10/6 - 10/17)"])
        worksheet.append(["Project"])
        start, end = (dates or {}).get(name, ("2026-10-06", "2026-10-17"))
        worksheet.append([f"Thời gian: {start} → {end}"])
        worksheet.append([])
        worksheet.append(SPRINT_HEADERS)
        for values in rows:
            row = dict(values)
            if row.get("Loại") == "Subtask":
                row["Task"] = f"    └ {row.get('Task', '')}"
            worksheet.append([row.get(header, "") for header in SPRINT_HEADERS])
        footer = [""] * len(SPRINT_HEADERS)
        footer[1] = '=COUNTIF(A:A,">0")'
        footer[10] = '=SUMIFS(K:K,A:A,">0")'
        worksheet.append(footer)
        worksheet.append([])
        worksheet.append(["Ghi chú:"])
    workbook.save(path)


def build_devs(path: Path, rows: list[dict]) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(DEV_HEADERS)
    for row in rows:
        worksheet.append([row.get(header, "") for header in DEV_HEADERS])
    workbook.save(path)


def write_history_csv(
    path: Path, rows: list[dict], *, bom: bool = False, delimiter: str = ",", date_style: str = "iso"
) -> None:
    with path.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HISTORY_HEADERS, delimiter=delimiter)
        writer.writeheader()
        for values in rows:
            row = {header: values.get(header, "") for header in HISTORY_HEADERS}
            if date_style == "dmy" and isinstance(row["Ngày tạo"], (date, datetime)):
                row["Ngày tạo"] = row["Ngày tạo"].strftime("%d/%m/%Y")
            elif date_style == "dmy" and row["Ngày tạo"]:
                parsed = datetime.fromisoformat(str(row["Ngày tạo"]))
                row["Ngày tạo"] = parsed.strftime("%d/%m/%Y")
            writer.writerow(row)
