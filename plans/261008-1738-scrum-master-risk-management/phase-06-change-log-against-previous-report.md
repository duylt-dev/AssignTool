# Phase 6 · Step 4b: change log against the previous report

## Context links

- Spec §17 (phase 1), §2 (`--compare`), §9 (`COMPARE-UNREADABLE`), §10
- Form R11; data ask 1 (an `ID` column in the sprint export); `confirm.md` D2, D10, D18, D27, O8
- `src/assigntool/xlsx_report.py` (`report_name`, `_assignments_sheet`: original columns, then the tool columns)
- `src/assigntool/discovery.py` (phase 2)

## Overview

- Priority: P2.
- Status: pending.
- Each normal run compares itself with the newest earlier report of the same sprint in `--out`. It writes a
  `Thay đổi` sheet with:
  - new orders and removed orders;
  - priority, due date or description changes;
  - orders the TM entered, and whether the TM followed the tool's proposal.
- It turns "respond to change" into something the TM can read in one place.

## Key insights

- The previous report already holds every original column of each order (spec §10), plus `Độ lớn`, `Mã PIC`,
  `Nguồn` and `Dự phòng`. No new state file is needed; `output/` is committed (D18).
- **Match key:**
  - `ID` when both reports have that column;
  - otherwise App (A10 key) + Task (NFC, casefold, collapsed spaces) + `Ngày tạo`. In 40 sample orders it has no
    duplicates.
  - A renamed title shows up as "removed" plus "new". Spec §17 says so, and this disappears once `ID` exists.
- **Do not report size changes on their own:** sizes vary between runs (D27), so they would only be noise. A size
  change is shown only next to a title or description change.
- **"TM followed the proposal" is a live accuracy number:** a `Tool đề xuất` order in the old report that now has
  `Người làm`. It is the backtest's measure, but on real current decisions.

## Requirements

**Functional**

1. **Previous report:**
   - `--compare FILE`, or automatic: the newest `assignment_<same sheet slug>_*.xlsx` in `--out` by its timestamp.
   - Ignore `.tmp` files, `~$` lock files and reports of other sheets.
   - With no previous report, the sheet says `Không có báo cáo trước để so`.
2. **Errors:**
   - An unreadable file given with `--compare` is an input error (exit 2).
   - An unreadable file found automatically gives WARN `COMPARE-UNREADABLE`:
     `Không đọc được báo cáo trước <file> (<lý do>); bỏ qua phần so sánh.` The run goes on.
3. **Change kinds**, as exact texts in spec §17:

   | Kind | When | Trước → Sau |
   |---|---|---|
   | `Đơn mới` | Key not in the old report | — → title, size |
   | `Đơn bị bỏ` | Key not in the new export | title → — |
   | `Đổi ưu tiên` | `Ưu tiên` differs | old → new |
   | `Đổi hạn` | `Hạn` differs | old → new |
   | `Đổi nội dung` | `Task` (only when matched by `ID`) or `Mô tả` differs | old size → new size |
   | `TM đã giao` | Old `Nguồn` = `Tool đề xuất`, new export has `Người làm` | proposed code → pool codes now (`khớp` / `khác đề xuất`) |
   | `Đổi người làm` | Pool codes on the order differ between the two reports | old codes → new codes |

4. **`Tác động` column** (impact):
   - for `Đơn mới`: `+<h>h vào sprint; team còn trống <x>h` (phase 4 numbers);
   - for `Đổi ưu tiên` to urgent/high: the order's current risks, by code;
   - for any other kind: empty.
5. **Sheet `Thay đổi`:**
   - columns `Loại` · `Đơn` · `Trước` · `Sau` · `Tác động`;
   - first row: `So với báo cáo <file> (<dd/mm/yyyy HH:MM>)`;
   - when nothing changed: `Không có thay đổi`.
6. **Terminal:**
   `Thay đổi so với <file>: <n> đơn mới, <m> đổi ưu tiên/hạn, <k> TM đã giao (<j> khớp đề xuất)`.

**Non-functional**

- `report_reader.py` is the only new `openpyxl` importer. It reads by header name and normalises at the boundary
  (best practices §3).
- The diff is pure (`rules/changes.py`).
- `--backtest` never compares.

## Architecture

```
discovery.previous_report(out_dir, sheet_slug, explicit) -> Path | None
report_reader.read_report(path) -> PreviousReport(stamp, has_id, rows: tuple[PreviousRow, ...])
rules/changes.py:
    match_key(app, title, created, id) -> tuple
    diff(previous, orders, assignments, capacity_left) -> tuple[Change, ...]
model: PreviousRow(key, id, title, app, priority_raw, due, description, assignees, pic_codes, source, size)
       ChangeKind (enum, value = the Vietnamese label), Change(kind, where, before, after, impact)
       Result.changes, Result.compared_with
```

## Related code files

- Create:
  - `src/assigntool/report_reader.py`
  - `src/assigntool/rules/changes.py`
  - `tests/test_report_reader.py`
  - `tests/test_changes.py`
- Modify:
  - `src/assigntool/discovery.py`
  - `src/assigntool/cli.py` (`--compare`)
  - `src/assigntool/model.py`
  - `src/assigntool/rules/pipeline.py`
  - `src/assigntool/xlsx_report.py`
  - `tests/test_discovery.py`, `tests/test_xlsx_report.py`, `tests/test_cli.py`
- Docs:
  - `LLM.md` §2 (the `openpyxl` importers now include `report_reader.py`), §3, §6, §7
  - `.claude/CLAUDE.md` non-negotiables (same list)
  - spec §2, §9, §17

## Implementation steps

1. `report_reader`, tested as a **round trip**: build a `Result`, write it with `write_report`, read it back. No
   hand-made fixture can drift from the writer. Cases:
   - with an `ID` column and without;
   - an extra unknown column;
   - a missing tool column (an input error naming the column).
2. `discovery.previous_report`:
   - the newest same-sheet report wins;
   - other sheets, `.tmp` and `~$` files are ignored;
   - `--compare` wins over discovery;
   - the report being written is never its own baseline.
3. `rules/changes.py`, with one table test per change kind, plus:
   - a duplicate key: both orders reported once as `không so được`, as INFO in the sheet;
   - an `ID` match surviving a title edit;
   - a size change alone is not reported.
4. Pipeline, sheet, terminal line.
5. Manual check: run on `input/` twice, edit a priority in a copy of the export between the runs, and check the sheet.

## Todo

- [ ] `report_reader.py` (round-trip tests)
- [ ] `previous_report` discovery and `--compare`
- [ ] `rules/changes.py` with a test per kind
- [ ] `Thay đổi` sheet, terminal line, `COMPARE-UNREADABLE`
- [ ] `LLM.md`, `.claude/CLAUDE.md`, spec updated
- [ ] Lint, format and tests green

## Success criteria

- A run with no previous report behaves exactly as phase 5 did, apart from the sheet that says so.
- Every change kind and `COMPARE-UNREADABLE` has a fire and a no-fire test.
- Two consecutive runs on unchanged input give `Không có thay đổi`, also with the AI on (sizes differ, but no change
  is reported).

## Risk assessment

- **The match key breaks when BA edits a title:** this is documented. The data ask for `ID` closes it, and the same
  `ID` is needed for O8.
- **The TM edits the old report by hand:** the reader trusts header names only. Unknown edits are ignored; a missing
  tool column is an error naming it.
- **`output/` holds many reports:** discovery reads names only and opens one file.

## Security considerations

- The previous report is the tool's own output and stays local.
- `TM đã giao` and `Đổi người làm` show **pool codes only**, and only fire when a pool dev is on at least one side
  (D14). A change between two people outside the pool is ignored silently.

## Next steps

- Phase 7.
