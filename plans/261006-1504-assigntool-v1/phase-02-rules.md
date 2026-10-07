# Task: phase 2 — the pure rules (orders, familiarity, carry-over, leave, PIC choice, reasons, summary, pipeline)

Repo: `/Users/macbook/Desktop/AssignTools` (Python 3.13, uv). Read first: `LLM.md` §2–§3, §8, §12;
`docs/assignment-spec.md` §1, §6.1–§6.3, §7, §8, §9, §10 ("Tải dev"), §12; `docs/python-best-practices.md` §2, §9, §10.

## Context (verified by the orchestrator)

- `src/assigntool/model.py` defines every type used here: `Dev`, `Level`, `Priority`, `Size` (value = hours),
  `SizeEstimate`, `SprintRow`, `SprintSheet`, `Order(row, priority)`, `HistoryOrder`, `Finding`, `Severity`,
  `Source`, `Assignment`, `DevSummary`, `Result`. Do not change it.
- `src/assigntool/normalize.py`: `text_key` (names, statuses, `Loại`), `app_key` (apps), `parse_priority` (empty →
  NORMAL, unknown → None).
- Phase 1 readers exist (`sprint_reader.py`, `dev_reader.py`, `history_reader.py`) and `tests/conftest.py` has
  `build_sprint_workbook`, `build_devs`, `write_history_csv`. This phase's tests build model values directly; they
  do not need files.
- Everything in `src/assigntool/rules/` is pure: no files, no subprocess, no clock, no printing (LLM.md §2).

## Change

Create these modules in `src/assigntool/rules/`:

1. `validate.py`: `orders_and_findings(target: SprintSheet) -> tuple[tuple[Order, ...], tuple[Finding, ...]]`.
   For each row: `text_key(kind) == "task"` → an `Order` (priority from `parse_priority`, `None` → `NORMAL` plus
   `PRIORITY-UNKNOWN`); `"subtask"` → skipped; anything else → `TYPE-UNKNOWN`. For orders also `APP-MISSING` (empty
   app) and `DUE-BEFORE-CREATED` (both dates set and `due < created`). Messages and levels exactly as spec §9, dates
   as `DD/MM/YYYY`, `where` = `f"Đơn STT {stt}"` (`TYPE-UNKNOWN`: `f"Dòng STT {stt}"`).
2. `familiarity.py`: a frozen dataclass `AppFamiliarity(rank: int, latest: HistoryOrder | None, versions: int)` and
   a class `FamiliarityIndex` built by `FamiliarityIndex.build(history, pool: tuple[Dev, ...])` with
   `get(dev, app) -> AppFamiliarity`, `is_new_app(app) -> bool` and `known_apps(dev) -> tuple[str, ...]`.
   Rules (spec §6.1): group history by `app_key`; per app keep only orders naming at least one pool dev (match by
   `text_key(name)`); the latest version = max by (`created`, original index). Rank 0 if the dev is on the latest
   version, 1 if on another kept order, else 2; `versions` = number of kept orders naming the dev. An app with no
   kept order (or an empty app) is new: rank 2 for everyone, `latest=None`. `known_apps` returns the app names
   (as written in the latest kept order) with rank 0 or 1, sorted by `app_key`.
3. `carry_over.py`: `BUSY_STATUSES` (the six statuses of D8 in `text_key` form) and
   `carry_over(prev: SprintSheet | None, pool) -> dict[str, int]` keyed by `Dev.code`: rows (orders and subtasks)
   whose `text_key(status)` is busy, counted once per pool dev named on the row. `None` → all zero.
4. `leave.py`: `working_days(start, end) -> tuple[date, ...]` (Mon–Fri inclusive; `()` if either is `None`),
   `leave_count(dev, days) -> int`, `on_leave_all_sprint(dev, days) -> bool` (days non-empty and all in leave).
5. `reasons.py`: `PREASSIGNED_REASON = "Đã giao sẵn trong file"` and a function building the spec §8 text for a
   proposed order from: the order's app as written, the PIC's `AppFamiliarity`, the senior cause (`"priority"`,
   `"new_app"` or `None`; part 2 is written only when the PIC's level ≥ MIDDLE), the priority, the PIC's load before
   this order in hours and orders, carry-over, previous sheet name, leave days, and the list of `(code, hours)` for
   devs with a strictly better rank that the load cap excluded. Exact texts:
   `Làm version gần nhất của {app} ({latest.sprint}: {latest.title})`, `Từng làm {app} ({versions} version)`,
   `Chưa làm {app}`, `Đơn không có App Name` (empty app), `Đơn {urgent|high} → ưu tiên middle trở lên`,
   `App chưa ai trong team làm → ưu tiên middle trở lên`, `Tải sprint này: {h}h ({n} đơn)`,
   `Việc dở {prev_name}: {n}`, `Nghỉ {n} ngày` (only n > 0), `{code} quen app hơn nhưng đang có {h}h (cân tải)`;
   joined with `" · "`. When priority is urgent/high and the app is also new, the cause is `"priority"`.
6. `assign.py`: `GAP_HOURS = 16` and
   `assign(orders, sizes: dict[int, SizeEstimate], pool: tuple[Dev, ...], fam: FamiliarityIndex,
   carry: dict[str, int], leave: dict[str, int], prev_name: str) -> tuple[Assignment, ...]` (spec §7):
   - Pre-assigned = `row.assignees` non-empty, whoever is named (D10). `Source.PREASSIGNED`, `pic_names` = the
     assignees, `pic_codes` = codes of pool devs among them (by `text_key`), reason `PREASSIGNED_REASON`, no backups.
     Each pool dev named gets load += `sizes[stt].size.value` hours and +1 order.
   - The rest, sorted by `(priority, due is None, due, created is None, created, stt)`, one at a time:
     `needs_senior = priority in (URGENT, HIGH) or fam.is_new_app(app)`;
     key(dev) = `(rank, 0 if not needs_senior or level >= MIDDLE else 1, load_hours, carry, leave, -level, code)`;
     cap = devs with `load_hours <= min(load_hours over the pool) + GAP_HOURS`; PIC = min of the capped devs by key;
     backups = the next two codes by key over the whole pool minus the PIC. Then the PIC's load += size, +1 order.
   - Return assignments in source STT order.
7. `summary.py`: `summarize(...) -> tuple[DevSummary, ...]` — one row per pool dev in `devs.xlsx` order, plus devs
   removed for leave (`on_leave_all_sprint=True`, zero orders): carry-over, leave count, counts of pre-assigned and
   proposed orders, total hours, `orders` as `"<title> [<size name>]"`, `known_apps` from the index.
8. `pipeline.py`: `build_result(*, target, prev, prev_name, orders, findings, devs, history, sizes, sizing_note)
   -> Result`:
   - working days from the target's `start`/`end`; active devs (`Dev.active`); those on leave all sprint are removed
     with an INFO `DEV-ON-LEAVE` finding; an empty pool raises `InputError("Không còn dev nào để giao …")`.
   - `PREV-SPRINT-MISSING` (WARN, `where` = the sheet name) when `prev is None`.
   - familiarity, carry-over, leave counts, `assign`, `summarize`; findings = given findings + the above, sorted WARN
     before INFO, then by code, then by `where`.
   - `Result(sheet_name=target.name, prev_sheet_name=prev_name, sizing_note=sizing_note, ...)`.

Tests (one file per module, `tests/test_<module>.py`), table-driven, values built in the test:
- every finding code of this phase fires once and does not fire on clean input;
- each key part of spec §7 decides on its own (only that part differs → PIC changes); the load cap overrides
  familiarity; a mixed-size case where hours, not order counts, decide; backups ignore the cap;
- pre-assigned orders naming only non-pool people are kept and add no load;
- familiarity ignores history orders naming nobody from the pool (the PS Remote research case of spec §12);
- `tests/test_pipeline.py` reproduces **both tables of spec §12** from hand-built values: the 6 Sprint 10 orders
  (STT 1 Phone Cleaner, 7 PS Remote urgent, 10 Roblox skin, 14 Auto click, 18 spin wheel 2, 24 Game Emulator high
  due 2026-10-07; created dates 10-05, 10-05, 09-22, 09-17, 10-05, 10-05), the 12 Sprint 9 history orders reduced
  to what matters (app, assignees, created), carry-over facts as previous-sheet rows, every size `M`. Run A keeps
  the 5 pre-assigned orders and proposes MinhNM for STT 10 with backups LinhNV, TiếnBV; run B (no assignees)
  gives 7→MinhNM, 24→AnTD, 14→LinhNV, 10→MinhNM, 1→LinhNV, 18→TiếnBV and final hours 32/32/16/16
  (Linh/Minh/An/Tiến). Use the full names `Ngọc Văn Linh` (LinhNV, middle+), `Nguyễn Nhật Minh` (MinhNM, middle),
  `Trần Đức An` (AnTD, junior+), `Bùi Văn Tiến` (TiếnBV, junior).

## Constraints

- Files you may create: the eight modules above and their tests. Anything else: stop and report.
- Must not change `model.py`, `normalize.py`, `errors.py`, readers, `pyproject.toml`, docs. No new dependencies.
- No I/O in `rules/`. Keep each module under ~200 lines. No weighted scores.

## Done when

- `uv run --frozen pytest`, `uv run --frozen ruff check .`, `uv run --frozen ruff format --check .` all pass.

## Build/test commands you may run

- `uv run --frozen pytest`, `uv run --frozen ruff check .`, `uv run --frozen ruff format .`
