# Phase 5 · Step 4a: mid-sprint risks and suggested responses

## Context links

- Spec §16: `PIC-ABSENT`, `DUE-AT-RISK`; §6.3 leave; §7; §9 (`DEV-ON-LEAVE`, `PRE-ASSIGNED-ON-LEAVE`); §3 rule 4
- Form R7, R8, T2, T3; `confirm.md` D2, D10, A12, A34, A35, A43
- `src/assigntool/rules/leave.py` (`working_days`, `on_leave_all_sprint`, `pre_assigned_on_leave`)
- `src/assigntool/rules/assign.py` (`assign`), `src/assigntool/rules/pipeline.py`, `src/assigntool/sprint_reader.py`
  (`_sheet_dates`)
- `eval/scenarios.py` case 3: run day 22/10, MinhNM off the whole sprint, AnTD off 3 days

## Overview

- Priority: P1. This is "respond to change", the second headline of the feedback.
- Status: pending.
- The tool already runs at any time (D2) and keeps pre-assigned orders (D10). This phase makes a mid-sprint run
  aware of three things:
  - leave in the **remaining** days;
  - orders close to their deadline that have not started;
  - orders whose holder is gone.
- For each one, the tool **suggests** a replacement using the §7 rule itself. Nothing is changed (R7 default).

## Key insights

- **A real gap today:** A12 only excludes a dev off for the **whole** sprint. Run on 22/10, the tool can propose a
  new order to a dev who is off 23–30/10. R8 fixes this. It changes A12 (an A row), so it needs an eval check, but
  no D row changes.
- **The status snapshot has a date.** Row 3 of the export says `Xuất ngày 2026-10-06`. Status-based risks are only as
  fresh as that date, so `STATUS-STALE` (INFO) tells the TM when the export is older than the run day.
- **The replacement needs no new rule code.** Call `assign()` again with:
  - every current assignment treated as pre-assigned;
  - the at-risk order emptied;
  - the absent dev out of the pool.

  The PIC it returns for that order is the suggestion, and its `reason` is a §8 sentence the TM already knows how to
  read. The cost of a separate "suggest" ranking: two rules that drift apart.

## Requirements

**Functional**

1. **Export date:**
   - `sprint_reader` reads `Xuất ngày (\d{4}-\d{2}-\d{2})` from row 3 into `SprintSheet.exported` (`None` when absent).
   - `STATUS-STALE` (INFO) fires when `add_working_days(exported, 1) < run day`:
     `Trạng thái đơn lấy từ file xuất ngày <dd/mm/yyyy>, cũ hơn ngày chạy <dd/mm/yyyy>; rủi ro tiến độ có thể đã cũ.`
2. **Remaining-days leave (R8):**
   - The remaining days are the working days from the base day to the sprint end.
   - A dev off every remaining day is removed from the pool for new orders.
   - `DEV-ON-LEAVE` stays as it is for whole-sprint leave (codes are never renamed).
   - A new INFO `DEV-ON-LEAVE-REST`:
     `<Mã> nghỉ hết các ngày còn lại của sprint (từ <dd/mm/yyyy>); không được giao đơn mới.`
   - Key part 5 (leave days) counts remaining days only.
   - When the base day is the sprint's first day, everything is identical to today's behaviour.
3. **`PIC-ABSENT`:**
   - Fires for a target-sprint order whose status is D8-busy or empty, whose pool devs are all off every remaining
     day, and which names no other working pool dev. The holder test is the same as A43.
   - Level `Cao`, owner TM, due = base day.
   - Action: `Chuyển cho <Mã2>: <reason>`, from the re-run of `assign()`. When nobody is left:
     `Không còn dev trong team; cân nhắc người ngoài team hoặc đẩy sang sprint sau`.
   - `PRE-ASSIGNED-ON-LEAVE` stays a finding: a finding is data, a risk is an action.
4. **`DUE-AT-RISK`:**
   - The deadline is `Hạn`, else the sprint end.
   - (a) Status not started (T2: `ready to progress`, `pending`, empty) and `working days(base day, deadline) ≤ 3`:
     `Trung bình`; `Cao` when ≤ 1.
   - (b) Status D8-busy or not started, and `Hạn` < base day: `Cao`. Uses `Hạn` only; the sprint end passing means
     the sprint is over.
   - Only orders with a pool PIC. The owner is the PIC code.
   - Action: `Hỏi <PIC> lý do; nếu kẹt: chuyển cho <Mã2> hoặc lùi hạn`, where `<Mã2>` comes from the same `assign()`
     re-run.
5. **Terminal:** `CAO` lines already print (phase 2). Add the export date line:
   `Trạng thái theo file xuất ngày <dd/mm/yyyy>`.

**Non-functional**

- Pure rules; the run day comes from `cli.py` (`--today` or the clock).
- Statuses in other states (`qa - testing`, `ready to release`, …) never fire `DUE-AT-RISK`: the dev's part is done.
  Spec §16 documents this.

## Architecture

```python
# rules/pic_risks.py
def absent_risks(assignments, pool, removed_rest, rest_days, ...) -> tuple[Risk, ...]: ...
def suggest(order_stt, assignments, pool_without, sizes, fam, carry, leave, prev_name, rules) -> Assignment | None:
    """Re-run assign() with every other assignment pre-assigned and this order empty."""

# rules/progress.py (pure)
NOT_STARTED = frozenset({text_key("ready to progress"), text_key("pending"), ""})
DUE_SOON_DAYS = 3
def due_risks(assignments, base_day, sprint_end, suggest_fn) -> tuple[Risk, ...]: ...

# rules/leave.py
def remaining_days(base_day, start, end) -> tuple[date, ...]: ...
def on_leave_rest(dev, rest_days) -> bool: ...
```

- `pipeline.build_result` builds the pool from `remaining_days`. It keeps `DEV-ON-LEAVE` for whole-sprint leave and
  adds `DEV-ON-LEAVE-REST` for the rest.
- `suggest()` rebuilds the `Order` tuple with `dataclasses.replace(order.row, assignees=pic_names)` for every other
  order. It calls `assign()` unchanged.

## Related code files

- Create:
  - `src/assigntool/rules/progress.py`
  - `tests/test_progress.py`
- Modify:
  - `src/assigntool/sprint_reader.py` (export date)
  - `src/assigntool/model.py` (`SprintSheet.exported`)
  - `src/assigntool/rules/leave.py`
  - `src/assigntool/rules/pic_risks.py`
  - `src/assigntool/rules/pipeline.py`
  - `src/assigntool/rules/validate.py` (`STATUS-STALE`)
  - `src/assigntool/cli.py`
  - `tests/test_leave.py`, `tests/test_pic_risks.py`, `tests/test_pipeline.py`, `tests/test_sprint_reader.py`
  - `tests/test_real_input.py`: pin `--today` wherever a run depends on the clock
  - `eval/scenarios.py` and `eval/build_cases.py`: re-derive case 3 by hand if R8 moves its answers

## Implementation steps

1. Find every test and eval run that uses the clock inside a sprint. Pin it with `--today` or the `run_day`
   parameter first, so the R8 change shows up as a deliberate diff.
2. `sprint_reader`: the export date, with tests for present, absent and malformed. Then `STATUS-STALE` with fire and
   no-fire tests.
3. `leave.remaining_days` and `on_leave_rest`. Change the pool building in the pipeline. Tests:
   - a run on the first day is identical to today's behaviour;
   - a run mid-sprint excludes the dev who is off for the rest;
   - leave before the base day does not count in key part 5.
4. `pic_risks.suggest`:
   - the suggestion equals what `assign()` would pick for an empty order;
   - the absent dev is never suggested;
   - TM rules still act (a `Chỉ định` dev on leave does not pin, as in §7).
5. `absent_risks` and `progress.due_risks`, with table tests per branch: (a) at 3 days, (a) at 1 day, (b) overdue,
   in QA (no fire), no pool PIC (no fire).
6. Re-derive the eval case 3 expected PICs by hand (A37) if R8 changes them, and note the reason in `dap-an.md`.
7. Run on `input/` with `--today 2026-10-15` (inside Sprint 10). Check the risks by hand.

## Todo

- [ ] Clock-dependent tests pinned
- [ ] Export date and `STATUS-STALE`
- [ ] Remaining-days leave, `DEV-ON-LEAVE-REST`, key part 5 over remaining days
- [ ] `suggest()` via `assign()`; `PIC-ABSENT`; `DUE-AT-RISK`
- [ ] Eval case 3 re-checked
- [ ] Lint, format and tests green

## Success criteria

- Runs on a sprint's first day produce exactly the earlier output (acceptance A–F unchanged).
- Every new code has a fire and a no-fire test.
- The backtest stays 43/92: it replays on filing days with today's `devs.xlsx`, so check, do not assume.

## Risk assessment

- **The R8 change shifts eval or acceptance numbers:** pin dates first (step 1), so any diff is visible and
  explained.
- **The `suggest()` re-run is O(orders) per at-risk order:** sprints have ~12 orders and 4 devs, which is
  negligible.
- **A stale export makes progress risks wrong:** `STATUS-STALE` says so, and the TM can re-export.

## Security considerations

- None new.

## Next steps

- Phase 6.
