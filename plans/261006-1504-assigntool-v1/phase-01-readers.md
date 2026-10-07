# Task: phase 1 — the three input readers and their tests

Repo: `/Users/macbook/Desktop/AssignTools` (Python 3.13, uv). Read first: `LLM.md` §2–§3 and §8,
`docs/assignment-spec.md` §3–§5, `docs/python-best-practices.md` §3, §5, §7, §10.

## Context (verified by the orchestrator)

- Value objects already exist in `src/assigntool/model.py`: `Dev`, `SprintRow`, `SprintSheet`, `HistoryOrder`,
  `Level`. Use them as they are.
- Helpers already exist in `src/assigntool/normalize.py`: `clean`, `text_key`, `header_key`, `split_people`,
  `parse_level`, `parse_date` (raises `ValueError` with a Vietnamese message for an unreadable string).
- `src/assigntool/errors.py` has `InputError`.
- The real export (`input/Maintain_update_Sprint_10_va_9.xlsx`, not committed) has sheets `Sprint 10` and
  `Sprint 9`. Row 1 `Sprint 10 (10/6 - 10/17)`, row 2 project name, row 3
  `Thời gian: 2026-10-06 → 2026-10-17   ·   Tiến độ: 0/6 task gốc xong (0%)   ·   Xuất ngày 2026-10-06`, row 4 empty,
  row 5 headers, data from row 6 while column A is an int, then a footer row whose B and K cells are formulas
  (`=COUNTIF(...)`, `=SUMIFS(...)`), an empty row, and a note row starting `Ghi chú:`.
- Row 5 headers, in order: `STT, Nhóm trạng thái, Task, Loại, Task cha, App Name., Trạng thái, Người làm, Ưu tiên,
  Hạn, Ước lượng (h), Người tạo, Điểm, Git Pull Request, Ngày tạo, Mô tả`.
- Subtask titles are indented: `"    └ Add tracking"` (4 spaces per level, then `└ `). Dates are `datetime` cells.
  `Người làm` looks like `"Ngọc Văn Linh, Bùi Văn Tiến"`.

## Change

1. Create `src/assigntool/sprint_reader.py` with
   `read_workbook(path: Path, sheet: str | None = None) -> tuple[SprintSheet, SprintSheet | None, str]`
   returning `(target, previous_or_None, previous_sheet_name)`.
   - Open with `openpyxl.load_workbook(path, read_only=True, data_only=True)`; close it in `finally`.
     A file that cannot be opened → `InputError` naming the file.
   - Sprint sheets are those whose trimmed name matches `^Sprint\s+(\d+)$`. Target = `sheet` if given (must be one
     of them, else `InputError` listing the sprint sheets), else the highest number. None at all → `InputError`.
   - Previous = the sprint sheet whose number is target − 1, else `None`; the returned name is always
     `f"Sprint {n-1}"`.
   - Header row = first row in rows 1–10 whose column A has `header_key(...) == "stt"`; else `InputError`.
   - Columns by `header_key` (never by index). Required on the target: `stt, task, loại, app name, trạng thái,
     người làm, ưu tiên, hạn, ngày tạo`; on the previous sheet only `loại, trạng thái, người làm`. Missing →
     `InputError` naming file, sheet and the missing header as the user would write it. `mô tả` is optional.
     A missing optional or previous-sheet column yields `""` / `None` in `SprintRow`.
   - Data rows: from the row after the header while column A is an `int` (not `bool`) or a `float` with
     `is_integer()`; stop at the first row where it is not. Pad short rows with `None` to the header length.
   - `SprintRow.title`: `clean()` of the cell after removing leading whitespace and leading `└` characters.
     Other text fields via `clean()`; `assignees` via `split_people`; dates via `parse_date`, turning `ValueError`
     into `InputError` with file, sheet, Excel row number and header name. `cells` = the raw row values tuple.
   - `SprintSheet.headers` = `clean()` of each header cell, in column order. `start`/`end` from the regex
     `(\d{4}-\d{2}-\d{2})\s*→\s*(\d{4}-\d{2}-\d{2})` searched in the joined text of row 3; `None` if absent.
2. Create `src/assigntool/dev_reader.py` with `read_devs(path: Path) -> tuple[Dev, ...]` (spec §4).
   - First sheet; header row 1; columns by `header_key`: required `tên, mã, level, nhận việc`, optional
     `ngày nghỉ`. Skip rows whose Tên, Mã and Level are all empty.
   - `Level` via `parse_level`; unknown → `InputError` listing `junior, junior+, middle, middle+, senior`.
   - `Nhận việc`: `text_key` must be `y` or `n`, else `InputError`.
   - `Ngày nghỉ`: a date/datetime cell → one day; text → split on `,`, each via `parse_date`; errors → `InputError`
     with row and column.
   - Duplicate `Tên` (by `text_key`) or `Mã` (by `text_key`) → `InputError`. No dev rows → `InputError`.
   - `Dev.name = clean(Tên)`, `Dev.code = clean(Mã)`.
3. Create `src/assigntool/history_reader.py` with `read_history(path: Path) -> tuple[HistoryOrder, ...]` (spec §5).
   - `open(path, encoding="utf-8-sig", newline="")`; `UnicodeDecodeError` → `InputError` ("không phải UTF-8").
   - Delimiter: whichever of `;` and `,` occurs more often in the first line.
   - Headers by `header_key`: required `sprint, loại, app name, người làm, ngày tạo`; optional `task`,
     `ước lượng (h)`. Missing required → `InputError`.
   - Keep only rows with `text_key(Loại) == "task"`, non-empty app and at least one name. `Ngày tạo` must parse to a
     date: empty or unreadable → `InputError` naming the CSV line number. `Ước lượng (h)`: float, accepting `,` as
     decimal separator; empty or unparsable → `None`.
4. Create `tests/conftest.py` with builders used by later phases too:
   - `build_sprint_workbook(path, sheets: dict[str, list[dict]], dates: dict[str, tuple[str, str]] | None = None)`:
     writes rows 1–5 like the real export, one data row per dict (keys = header names; missing keys empty; a dict
     with `"Loại": "Subtask"` gets its `Task` indented as `"    └ " + title`), then the formula footer, an empty
     row and a `Ghi chú:` row.
   - `build_devs(path, rows: list[dict])` and `write_history_csv(path, rows: list[dict], *, bom=False,
     delimiter=",", date_style="iso")` (`"dmy"` writes `DD/MM/YYYY`).
5. Tests: `tests/test_normalize.py`, `tests/test_sprint_reader.py`, `tests/test_dev_reader.py`,
   `tests/test_history_reader.py`. Real files in `tmp_path`, no mocks. Cover at least: footer not read as a row;
   formula cells never appear as text; subtask indentation stripped; NFD name in `Người làm` comes out NFC; target =
   highest sprint; `sheet=` override and its error; previous sheet missing → `None` and name `Sprint N-1`; each
   missing-required-header error; bad date error names row and column; row-3 dates parsed and absent; dev reader:
   bad level, bad `Nhận việc`, duplicates, leave days as date cell and as text in both formats; CSV: BOM and no BOM,
   `;` delimiter, `DD/MM/YYYY`, subtask rows ignored, missing required header, bad date names the line.

## Constraints

- Files you may create: the four modules/tests above, `tests/__init__.py` if needed. Anything else: stop and report.
- Must not change `model.py`, `normalize.py`, `errors.py`, `pyproject.toml`, docs. Must not add dependencies.
- Only these three readers import `openpyxl` or read CSV. No `print`. Every `open()` has `encoding=`.
- Error messages are Vietnamese. Keep each module under ~200 lines.

## Done when

- `uv run --frozen pytest` passes and `uv run --frozen ruff check .` and `uv run --frozen ruff format --check .` pass.

## Build/test commands you may run

- `uv run --frozen pytest`, `uv run --frozen ruff check .`, `uv run --frozen ruff format .`
