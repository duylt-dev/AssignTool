# Plan: assigntool v1

Implements [`docs/assignment-spec.md`](../../docs/assignment-spec.md) as laid out in [`LLM.md`](../../LLM.md) §2–§3.
Decisions: [`confirm.md`](../../confirm.md) (no open questions). Spec approved by the user on 2026-10-06.

## Already done by the orchestrator (the contract; workers must not change it)

| File | Content |
|---|---|
| `pyproject.toml`, `.python-version`, `uv.lock` | Python 3.13, `openpyxl`, dev: `pytest`, `ruff`; markers `real_input`, `ai` |
| `src/assigntool/model.py` | Every value object the phases exchange |
| `src/assigntool/errors.py` | `AssignError`, `InputError` |
| `src/assigntool/normalize.py` | `clean`, `text_key`, `app_key`, `header_key`, `split_people`, `parse_priority`, `parse_level`, `parse_date` |

## Phases

Run in order, one writer at a time. Each phase file is self-contained and is the worker's spec.

| # | Phase | Files owned | Status |
|---|---|---|---|
| 1 | [Readers](phase-01-readers.md) | `sprint_reader.py`, `dev_reader.py`, `history_reader.py`, `tests/conftest.py`, reader + normalize tests | done (27 tests) |
| 2 | [Rules](phase-02-rules.md) | `rules/{validate,familiarity,carry_over,leave,reasons,assign,summary,pipeline}.py` + tests | done (Codex) |
| 3 | [AI sizing](phase-03-ai-sizing.md) | `rules/sizing.py`, `ai_cli.py`, `tests/fake_ai.py` + tests | done (Codex; error parsing fixed by orchestrator) |
| 4 | [Report, CLI, acceptance](phase-04-report-cli.md) | `xlsx_report.py`, `cli.py`, `tests/test_real_input.py`, `tests/test_ai_smoke.py`, `tests/test_cli.py` | done (orchestrator: Codex quota ran out) |

## Gate after every phase (run by the orchestrator)

```bash
uv run ruff check . && uv run ruff format --check . && uv run pytest
```

Read the diff file by file; spot-check one test per finding/key part by mutating the real module (code-reviewer
memory). Phase 4 also: `uv run assigntool --ai off` on `input/` matches spec §12, and one real `gemini` run.

## Risks

- `openpyxl` read-only mode and the export's cached formula values: covered by the reader tests' formula footer.
- AI reply shape drift between CLI versions: parsing is lenient on prose and fences, strict on content (spec §6.4).
- Windows: untested here; rules in best practices §4–§5 (no `shell=True`, stdin for `gemini`, `encoding=`).

## Result (2026-10-06)

- Gate: 77 passed, 1 skipped (`ai`); ruff clean. `ASSIGNTOOL_TEST_AI=gemini uv run pytest -m ai`: passed (34 s).
- Mutation spot-check: 9 mutations of the rule (cap, seniority, carry-over, leave, level tie-break, backups, pool
  filter on history, NFC, busy statuses), each caught by a failing test (the level tie-break needed a new case).
- Cross-review by Gemini (read-only), split in two: rules vs spec §6–§9 → NONE; CLI/report/AI runner → NONE (that run
  ended with status ERROR after answering, so it is a weak signal).
- Two real runs with Gemini on the sample: spec §12 note; open questions `confirm.md` O5, O6.
