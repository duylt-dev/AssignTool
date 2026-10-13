# Phase 7 · Evaluation, docs and report to MD/TM

## Context links

- `eval/README.md`, `eval/scenarios.py`, `eval/build_cases.py`, `eval/score.py`, `eval/run_eval.py`
- Last size results: `eval/results/20261008-1610-agy-sau-sua/` (57% in the right class, 95% within one class, on
  Sprint 8–9)
- `confirm.md` A36–A42 (how eval works, and who decides on numbers); data ask 2 (TM labels)
- `plans/reports/261008-bao-cao-po-input-dieu-kien-output.md`: the report the MD/TM already have

## Overview

- Priority: P1. Without numbers, management cannot tell whether the risk register helps or just adds noise.
- Status: pending.
- What this phase does:
  - measure the new behaviour;
  - check that nothing old got worse;
  - close the docs;
  - write a short Vietnamese report for MD/TM.

## Key insights

- Two kinds of check (A37):
  - **By spec:** a synthetic case with hand-computed expected risks. A miss is a defect: fix it with a unit test
    (A42).
  - **Against people:** TM labels on real orders. A miss is a number, not a failure.
- Only `READY-GAPS` touches the AI. Every other risk is deterministic and can be scored exactly with `--ai off`.

## Requirements

**Functional**

1. **New synthetic case `case-6-rui-ro-giua-sprint`** in `eval/scenarios.py`, built by `eval/build_cases.py`.
   - Setup: Sprint 11, run day mid-sprint.
   - It must contain:
     - a dev off for the rest of the sprint, holding one busy order (fires `PIC-ABSENT`);
     - a not-started order due in 2 working days (fires `DUE-AT-RISK` (a));
     - an overdue in-progress order (fires `DUE-AT-RISK` (b));
     - a dev over capacity, and a sprint over capacity (`CAPACITY-*`);
     - a junior on an unfamiliar app (`PIC-UNFAMILIAR`);
     - orders with no description, and an urgent order with no `Hạn` (`READY-GAPS`, deterministic part);
     - a checklist table in the case's rules file;
     - one order of each kind that must **not** fire.
   - `dap-an.json` lists the expected `(code, where, level)` set and the suggested `Mã2` for each `PIC-ABSENT`.
     Claude computes them by hand from the spec before running.
2. **`eval/score.py`:**
   - reads `Rủi ro`;
   - scores precision and recall of `(code, where)` against `dap-an.json`, plus level and suggestion agreement;
   - `bang-diem.md` gains a "Rủi ro" table.
3. **Real cases 1–2 (Sprint 9, Sprint 8):**
   - the number of orders with `READY-GAPS`, split into deterministic and AI;
   - AI gap **stability**: across 3 AI runs, the share of flagged orders whose AI items agree in ≥ 2 of 3 runs;
   - `CAPACITY-*` compared with the real hours (A40): did the dev the tool flags really have > 60h?
4. **No regression:**
   - size accuracy on cases 1–2 (3 `agy` runs) is no worse than the last folder by more than one order per sprint;
   - PIC and backup scores on cases 1–5 are unchanged, except where R8 deliberately changed case 3 (explained in
     `dap-an.md`);
   - the backtest is still 43/92.
5. **When the TM labels arrive** (data ask 2): precision and recall of `READY-GAPS` on the 18 orders of Sprint 9–10.
   Until then, an `O` row says this is not yet measured.

**Docs**

- `README.md`: the new sheets, what a risk level means, how to add a checklist.
- `LLM.md`:
  - the status line;
  - §1 (what the tool is now);
  - §8 (testing conventions for risks: each code fires and does not fire);
  - §9 (the eval command, unchanged).
- `.claude/CLAUDE.md`: the status line.
- `confirm.md`: each A row's numbers (T1–T7, R6) confirmed or changed with the data that changed them.
- Plan status: `plan.md` front matter `status: completed`, and a result section in the style of the earlier plan.

**Report:** `plans/reports/<date>-bao-cao-scrum-master-rui-ro.md`, in Vietnamese, written for MD + TM:

- what the bot now does for each of the 4 feedback steps, with one real example row from the `Sprint 10` register;
- the measured numbers above, and what is still not measured (TM labels, lateness history);
- what is left for phase C after the API (D20, O8), and which decisions it needs (R7 → D10).

## Related code files

- Modify:
  - `eval/scenarios.py`
  - `eval/build_cases.py`
  - `eval/score.py`
  - `eval/README.md`
  - `README.md`
  - `LLM.md`
  - `.claude/CLAUDE.md`
  - `confirm.md`
  - `plans/261008-1738-scrum-master-risk-management/plan.md`
- Create:
  - `eval/case-6-rui-ro-giua-sprint/` (generated)
  - `eval/results/<stamp>/` (generated)
  - `plans/reports/<date>-bao-cao-scrum-master-rui-ro.md`

## Implementation steps

1. Write case 6 and its expected risks by hand. Have them checked against the spec before the first run (A37).
2. Extend `score.py`. Rebuild the cases with `uv run python eval/build_cases.py`.
3. Run `uv run python eval/run_eval.py --ai agy --ai-runs 3 --label rui-ro` (one call at a time, `LLM.md` §9).
4. Compare with `eval/results/20261008-1610-agy-sau-sua/`. Any by-spec miss is fixed in `tests/` first.
5. Run `uv run assigntool --backtest` and check 43/92.
6. Update the docs listed above, and run the done checklist (best practices §11).
7. Write the MD/TM report. Update the plan status.

## Todo

- [ ] Case 6 and expected risks
- [ ] `score.py` risk table
- [ ] Eval run, comparison with the last folder, backtest
- [ ] `README.md`, `LLM.md`, `.claude/CLAUDE.md`, `confirm.md`
- [ ] MD/TM report
- [ ] Plan marked completed

## Success criteria

- Case 6 with `--ai off`: risk precision and recall 100% against the hand-computed answers, and suggestions 100%.
- No regression beyond the tolerance in requirement 4.
- The report states every number together with the folder it came from.

## Risk assessment

- **The AI quota stalls** (seen after ~30 `gemini` calls in an hour, `LLM.md` §9): use `agy`, one call at a time,
  and say which tool was used.
- **AI gap stability is low** (< 70% agreement in ≥ 2 of 3 runs): show AI gaps only in `Cần làm rõ`, not in
  `Phản hồi BA` messages. Record it as an A row with the number.

## Security considerations

- Case 6 is synthetic. No data from `input/` is copied into it beyond the app names already used by cases 3–5 (A39).

## Next steps

- Phase C (after the API): post the `Phản hồi BA` messages as comments on the orders, notify through chat, write
  `Người làm`, and turn the `PIC-ABSENT` suggestions into one-click reassignment with TM approval (needs R7 → a new D
  row).
