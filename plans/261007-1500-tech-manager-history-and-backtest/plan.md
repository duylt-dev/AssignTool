# Plan: Tech manager history, cap in orders, backtest

Date 2026-10-07. Decisions: `confirm.md` D2, D5, D6, D8, D19–D27, A21–A29, O8, O9 (answers in
`plans/reports/261007-cau-hoi-export-t2-t10.md`).

## Scope

| # | Change | Decision | Status |
|---|---|---|---|
| 1 | History = Tech manager export (`.xlsx` month sheets or `.csv`, 18 columns), root orders only | D6, A23 | done |
| 2 | Sprint labels parsed (`Sprint N (m/d - m/d)`, several per cell, year from `Ngày lên đơn`) | A24 | done |
| 3 | History window: not the target sprint, nothing filed or started after the run day | A22 | done |
| 4 | Discovery by content: `.xlsx` with `Sprint N` sheets = sprint export, other `.xlsx`/`.csv` = history | A2 | done |
| 5 | Load cap in orders (lowest + 1), hours stay key part 3; reason text in orders | D26 | done |
| 6 | Busy statuses + `internal - need fix`, `đã ro` | D8 | done |
| 7 | Reason quotes the full sprint label, or `Tháng M/YYYY` | A25 | done |
| 8 | `assigntool --backtest`: replay each Maintain sprint by filing day, report match per sprint and per order | D22, A21, A29 | done |
| 9 | Docs: spec, LLM.md, README, best practices, `.claude/CLAUDE.md` | LLM.md §10 | done |

Out of scope: writing `Người làm` into the internal system (D19 blocked by D20, O8); assigning bugs or MVP orders
(D5); a board column (D23).

## Result (2026-10-07)

- 102 tests pass (1 opt-in AI test skipped); acceptance runs A–F on `input/` ran.
- Normal run, `--ai off` and `gemini`: Roblox skin → AnTD (spec §12 run E).
- Backtest: 43/92 orders match the TM (spec §13). Reproduced by a separate script that shares no code with the tool;
  the first disagreement exposed a bug (`parse_priority(...) or NORMAL` turned urgent orders into normal), now fixed
  and covered by `test_urgent_orders_are_replayed_first_even_when_filed_later`.

## Risks

- Board detection by label length (A21) breaks if a Maintain sprint ever lasts more than 3 weeks. Mitigation: a board
  column in the export (D23).
- Backtest sizes every order `M` and has no carry-over (A29): it measures familiarity, seniority and the cap only.
