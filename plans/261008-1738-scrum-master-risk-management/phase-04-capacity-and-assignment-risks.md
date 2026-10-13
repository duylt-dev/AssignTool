# Phase 4 · Steps 2–3: capacity and assignment risks

## Context links

- Spec §16: `CAPACITY-DEV`, `CAPACITY-SPRINT`, `PIC-UNFAMILIAR` (phase 1); §6.1, §6.3, §7, §10 `Tải dev`
- Form R6, T4, T6; `confirm.md` D7, D8, D26, D27, A5, A7, A12
- `src/assigntool/rules/carry_over.py` (`BUSY_STATUSES`), `src/assigntool/rules/leave.py`,
  `src/assigntool/rules/familiarity.py` (`FamiliarityIndex.get`, `is_new_app`), `src/assigntool/rules/summary.py`

## Overview

- Priority: P2.
- Status: pending.
- Step 2 ("compute"):
  - each dev's load against their capacity;
  - the sprint's total load against the pool's capacity, with a list of orders to defer.
- Step 3 ("propose"): flag a proposed PIC who has never worked on the app when the order is risky, and name who
  could help.

## Key insights

- Load in hours already exists: key part 3 sums sizes (spec §7).
- Capacity is new. A12 says there is no measured hours-per-dev, so R6 sets a stated assumption: 6h per working day.
  The message says the hours are estimates.
- **Only work still to do counts.** In a mid-sprint run, orders whose status is neither D8-busy nor empty (in QA,
  done, ready to release) are out of the load (T6). D8's set is reused, so no new status list is needed.
- Carry-over has no hours (counts of rows only), so it is quoted in the message, not added to the load.
- The defer list must be deterministic and explainable. It is the reverse of the A5 processing order: the lowest
  priority, then the latest due date, then the newest. Orders are taken until the load fits.
- The defer list includes pre-assigned orders, because deferring is a PO/TM call, not a reassignment (D10 untouched).
- **When `PIC-UNFAMILIAR` fires.** Familiarity outranks seniority (LLM.md §12), so a junior on an unfamiliar app
  happens only when the familiar or senior devs were capped. That is exactly when the TM should arrange support.

## Requirements

**Functional**

- **Capacity of a dev:** `6 × (working days from the base day to the sprint end − the dev's leave days among them)`.
  The base day is the later of the run day and the sprint's first day (`rules_day`). A sheet with no dates gives no
  capacity, and no capacity risks fire.
- **Remaining load of a dev:** the sum of the size hours of the target-sprint orders they hold (pre-assigned or
  proposed) whose status is in `BUSY_STATUSES` or empty.
- **`CAPACITY-DEV`:** load > capacity, for each pool dev.
  - Level: `Trung bình`; `Cao` when load > 1.5 × capacity.
  - Action: name the dev with the most free hours. When the overloaded dev holds a proposed order, name the
    lowest-ranked one (reverse A5): `Cân nhắc chuyển STT <x> cho <Mã2> (còn trống <f>h)`. When nobody has free
    hours: `Không có dev còn trống; xem rủi ro CAPACITY-SPRINT`.
  - The message quotes the carry-over count when it is > 0.
- **`CAPACITY-SPRINT`:** sum of loads > sum of capacities of the pool.
  - Level: `Cao`.
  - Action: the defer list (`STT a, b (<k>h)`) plus `hoặc thêm người ngoài team` (D7 allows QA/RnD/TM only when
    pushing a deadline).
- **`PIC-UNFAMILIAR`:** a proposed order whose PIC has familiarity rank 2, when the PIC's level < middle or the order
  is urgent/high.
  - Level: `Thấp`, one step up for urgent/high.
  - Action: the pool dev with the best rank (0, then 1; ties by the §7 key order), with the §6.1 text:
    `Nhờ <Mã> (<familiarity text>) hỗ trợ khởi động`. When the app is new: `App mới với team: tính thêm thời gian
    tìm hiểu`.
- **Sheet `Tải dev`:** two columns at the end, `Sức chứa còn lại (h)` and `Giờ việc còn lại (h)`.

**Non-functional**

- Pure functions. No PIC changes; every §7 test passes unchanged.
- With `--ai off` every order is `M` (16h), so `CAPACITY-DEV` fires at 4 or more open orders on a full 10-day
  sprint (64h > 60h). State this in spec §16 so the TM can read an `--ai off` run correctly.

## Architecture

```python
# rules/capacity.py (pure)
HOURS_PER_DAY = 6  # R6 / A row
HIGH_FACTOR = 1.5  # R6 / A row


def capacities(pool, days_left, leave) -> dict[str, int]: ...
def open_load(assignments, pool) -> dict[str, int]: ...  # BUSY_STATUSES or empty status
def capacity_risks(assignments, pool, days_left, leave, carry, base_day) -> tuple[Risk, ...]: ...
def defer_list(assignments, excess_hours) -> tuple[Assignment, ...]: ...  # reverse A5


# rules/pic_risks.py (pure); PIC-ABSENT joins it in phase 5
def unfamiliar_risks(assignments, pool, fam, base_day) -> tuple[Risk, ...]: ...
```

- `leave.working_days(base_day, target.end)` gives `days_left`.
- `pipeline.build_result` calls both producers and adds their output to `Result.risks`.
- `summary.summarize` gains the two numbers.

## Related code files

- Create:
  - `src/assigntool/rules/capacity.py`
  - `src/assigntool/rules/pic_risks.py`
  - `tests/test_capacity.py`
  - `tests/test_pic_risks.py`
- Modify:
  - `src/assigntool/rules/pipeline.py`
  - `src/assigntool/rules/summary.py`
  - `src/assigntool/model.py` (`DevSummary` gains `capacity` and `open_hours`)
  - `src/assigntool/xlsx_report.py`
  - `tests/test_summary.py`, `tests/test_xlsx_report.py`

## Implementation steps

1. `capacities` and `open_load`, with table tests:
   - full sprint;
   - run day mid-sprint;
   - leave inside and outside the remaining days;
   - a sheet with no dates;
   - the status filter (busy, empty, in QA, done).
2. `capacity_risks`:
   - fire and no-fire at exactly the capacity;
   - `Cao` above 1.5×;
   - the suggested receiver is the dev with the most free hours (ties by `Mã`);
   - the carry-over text.
3. `defer_list`: the reverse A5 order; stop as soon as the excess is covered; pre-assigned orders included.
4. `unfamiliar_risks`:
   - junior + rank 2 fires;
   - middle + rank 2 + normal priority does not fire;
   - middle + rank 2 + urgent fires;
   - new app gives the "app mới" action;
   - the helper picked is the best rank.
5. Wire into the pipeline and the summary, then the `Tải dev` columns.
6. Run on `input/` (Sprint 10, `--ai off` and `agy`). Record the risk counts in the phase-7 report.

## Todo

- [ ] `capacity.py` with tests
- [ ] `pic_risks.unfamiliar_risks` with tests
- [ ] Pipeline, summary, `Tải dev` columns
- [ ] Spec §16 numbers checked against a real run
- [ ] Lint, format and tests green

## Success criteria

- Each code has a fire and a no-fire test.
- No §7 or §12 assertion changes.
- On Sprint 10 the output can be checked by hand: capacity = 6 × the remaining working days, minus leave.

## Risk assessment

- **AI sizes underestimate** (eval round 1: `S` given to 68h orders). Capacity risks then fire too rarely. They are
  advisory, and phase 7 compares them with real hours on Sprint 8–9.
- **6h/day is wrong for this team:** it is one constant and an A row, and becomes a `devs.xlsx` column only if R6
  says so.

## Security considerations

- None new.

## Next steps

- Phase 5.
