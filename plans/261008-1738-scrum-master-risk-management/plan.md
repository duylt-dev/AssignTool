---
title: "scrumbot stage 1: four layers, order understanding and the risk register on exports"
description: "Stage 1 (GĐ 1) of the scrum-master bot: restructure assigntool into scrumbot's four layers, widen the AI's order understanding, and add the risk register for risks 1–9 from the export files, with the BA feedback and change sheets."
status: completed
priority: P1
effort: 45h
branch: main
tags: [feature, refactor, risk]
created: 2026-10-08
updated: 2026-10-13
---

# Plan: scrumbot stage 1 (GĐ 1)

**Done 2026-10-13, re-planned by D57** (`confirm.md`): the source became the dev API instead of the export files,
risks 1 and 12 and `Phản hồi BA` moved to stage 2 (D53), and scheduled runs, the replay and the end-of-sprint report
moved into stage 1 (D54–D56, A72). Spec: `docs/bot-spec.md`. Report:
[`261013-bao-cao-trien-khai-scrumbot-gd1.md`](../reports/261013-bao-cao-trien-khai-scrumbot-gd1.md). The text below
is the 09/10 plan, kept as history.

Goal (09/10, `confirm.md` D36): a Python bot that acts as scrum master: it manages, understands and reviews orders,
assigns them, and above all **manages risk**. Decisions: D36–D48, A45–A53; open: O11–O13. Forms:
[`261009-cau-hoi-bot-scrum-master.md`](../reports/261009-cau-hoi-bot-scrum-master.md) (answered),
[`261008-cau-hoi-scrum-master-quan-ly-rui-ro.md`](../reports/261008-cau-hoi-scrum-master-quan-ly-rui-ro.md) (its
defaults applied, D48). System data measured through Chrome:
[`261009-bao-cao-du-lieu-he-thong-qua-chrome.md`](../reports/261009-bao-cao-du-lieu-he-thong-qua-chrome.md).

This plan is stage 1 only (D47): manual runs on the export files, no token (D41). Stages 2–3 get their own plan.

## Principle

**Risks advise; the §7 rule still decides.** The AI never picks a PIC or a risk level (D38). No risk changes a PIC, a
pre-assigned order (D10), the cap (D26) or the exit code. Cost of breaking it: the backtest (D22) and `eval/` stop
measuring the rule.

## Four layers (D46)

| Layer | Holds | From today's code |
|---|---|---|
| Sources | Turn an input into `model.py` values; no decisions | `sprint_reader`, `dev_reader`, `history_reader`, `rules_reader` |
| Understanding | One AI call per sprint: type, items, size, missing checklist items, ≤ 2 questions, technical risks (D38) | `ai_cli` (I/O) + the prompt and parsing of `rules/sizing.py` (pure) |
| Decisions | PIC rule, TM rules, backtest, **risks**; pure, no I/O | `rules/*` (kept, D46) + new risk modules |
| Actions | Write the results somewhere | `xlsx_report`; stage 3 adds comment and assignee writers |

Package and command become **`scrumbot`** (D46). Exact layout and dependency arrows: `LLM.md` §2–§3, rewritten in
phase 2 before any file moves.

## Phases

| # | Phase | Status | Effort | Link |
|---|---|---|---|---|
| 1 | Decisions and spec | Done 13/10: D49–D57, A54–A79, `docs/bot-spec.md` | 4h | [phase-01](./phase-01-decisions-and-spec.md) |
| 2 | Rename to `scrumbot`, four layers, risk register foundation | Done 13/10 | 8h | [phase-02](./phase-02-risk-register-foundation.md) |
| 3 | Order understanding and readiness (risk 1), `Phản hồi BA` | Understanding done (A79); risk 1 and `Phản hồi BA` moved to stage 2 (D53) | 8h | [phase-03](./phase-03-order-readiness.md) |
| 4 | Capacity and assignment risks (2, 3, 4, 5, 8) | Done 13/10, plus risk 6 | 6h | [phase-04](./phase-04-capacity-and-assignment-risks.md) |
| 5 | Mid-sprint risks (6, 7), remaining-days leave (R8) | Done 13/10, plus risks 10, 11 from the API | 6h | [phase-05](./phase-05-mid-sprint-risks-and-responses.md) |
| 6 | Run state and change log (risk 9), sheet `Thay đổi` | Done 13/10 | 7h | [phase-06](./phase-06-change-log-against-previous-report.md) |
| 7 | Evaluation, docs, report to MD/TM | Done 13/10: replay of 29 sprints, `eval/` unchanged, report | 6h | [phase-07](./phase-07-evaluation-and-docs.md) |

Phases run in sequence and each ends green: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
Phase 2 changes no behaviour: all 161 tests and `eval/` scores stay identical.

## What changed on 09/10 (apply when the phase starts)

| Phase | Change | Source |
|---|---|---|
| 1 | Spec gains the AI understanding fields, the 12 risks with codes (stage 1 writes 1–9), the A49 thresholds as a stage 2 note | D38, D45, A49 |
| 2 | Rename `assigntool` → `scrumbot` (pyproject, `src/`, imports, `eval/run_eval.py`, docs). Move the readers under a sources layer and `ai_cli` under an understanding layer. Report file name stays `assignment_<sprint>_<stamp>.xlsx` so `eval/score.py` keeps working | D46 |
| 3 | The AI reply also returns the order type, its items and technical risks; checklist kinds follow D38's seven types | D38, D48 R2–R3 |
| 4 | Add risk 4 (an order filed after the sprint start pushes the sprint over capacity) and risk 8 (carry-over from the previous sprint, from the D8 statuses) | D45 |
| 5 | Risk 7 also fires when the order still has many open subtasks | D45 |
| 6 | The previous run comes from the run state in `state/` (SQLite, not committed), not from the previous report; the state also keeps what was asked and reminded for stage 3 | A51 |
| 7 | Score risks 1–9 on a new synthetic case; the end-of-sprint report (D44) moves to stage 2, since it needs closing dates from the system | D44, D47 |

## Data and open points

- Status history exists only from 10/09/2026. Risks 10–12 and the end-of-sprint report wait for stage 2.
- **O11:** no token. Stage 2 source by default: a JSON snapshot taken through Claude in Chrome on request.
- **O12:** risk 11 by status never fires on real data; QA returns are bugs. Spec writes the O12 default.
- **O13:** precision of `Cần làm rõ` needs TM labels; until then only flag counts and run-to-run stability.

## Out of scope (stages 2–3)

- Reading the system, risks 10–12, scheduled runs (D36), the end-of-sprint report.
- Comments to BA and PIC, writing `Người làm` (A46), the `apply` command (D43), dry-run mode (A47).
- PR review, dev scoring (D37); bugs and MVP orders (D5, D39); velocity and burndown.

## Key risks

- **Alert fatigue:** 22/40 sample orders have no text description, so risk 1 fires on more than half. One register
  row per order, grouped by creator in `Phản hồi BA`.
- **The wider AI reply may move sizes.** Measured against `eval/results/20261008-1610-agy-sau-sua/`; if sizes get
  worse, understanding moves to its own call.
- **The rename touches every import and doc.** Done alone in phase 2 with no behaviour change, so a diff of eval
  scores before and after proves it.
