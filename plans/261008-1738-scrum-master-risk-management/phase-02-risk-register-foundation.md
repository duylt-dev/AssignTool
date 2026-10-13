# Phase 2 · Risk register foundation

## Context links

- Spec §16 (written in phase 1), §10, §11
- `LLM.md` §2, §11 (V1: `cli.py` 294 lines), best practices §2 (~200 lines per file), §11 checklist
- `src/assigntool/cli.py` (`_run`, `_files`, `_only_one`, `_at_most_one`, `_explicit`, `_print_summary`)
- `src/assigntool/rules/team_rules.py` (`rules_day`: already the later of the run day and the sprint's first day, A34)

## Overview

- Priority: P1. Phases 3–6 add risk producers to what this phase builds.
- Status: pending.
- Scope:
  - the risk types;
  - the pure register helpers;
  - the `Rủi ro` sheet;
  - the terminal summary;
  - moving input discovery out of `cli.py`.
- No risk fires yet. The sheet shows `Không có rủi ro`.

## Key insights

- `rules_day(today, target.start)` already computes the **base day** that every risk needs (the later of the run day
  and the sprint's first day). Reuse it; do not write a second one.
- `cli.py` is 294 lines (deviation V1), and phases 3 and 6 add discovery (checklist, previous report). Split it first,
  with no behaviour change, so later diffs stay readable.
- `eval/score.py` reads sheets by name (`Phân công`, `Cảnh báo`), so a new sheet in second position breaks nothing.

## Requirements

- **Functional:**
  - `Result.risks` exists.
  - Sheet `Rủi ro` is the second sheet. Its columns: `Mức` · `Mã` · `Nhóm` · `Vị trí` · `Vấn đề` · `Ảnh hưởng` ·
    `Đề xuất` · `Ai xử lý` · `Hạn xử lý`.
  - Terminal line `Rủi ro: <a> cao · <b> trung bình · <c> thấp`, plus one line per `Cao` risk:
    `CAO <code> <where>: <problem>`.
- **Non-functional:**
  - No change to any existing output.
  - All 161 tests pass unchanged.
  - The register helpers are pure (`LLM.md` §2).

## Architecture

```python
# model.py
class RiskLevel(enum.IntEnum):  # smaller sorts first
    HIGH = 0  # "Cao"
    MEDIUM = 1  # "Trung bình"
    LOW = 2  # "Thấp"


class RiskGroup(enum.Enum):
    READINESS = "Đơn chưa rõ"
    CAPACITY = "Năng lực"
    ASSIGNMENT = "Phân công"
    PROGRESS = "Tiến độ"


@dataclass(frozen=True, slots=True)
class Risk:
    level: RiskLevel
    code: str  # spec §16
    group: RiskGroup
    where: str  # "Đơn STT 3", "LinhNV", "Sprint 10"
    problem: str  # Vấn đề
    impact: str  # Ảnh hưởng
    action: str  # Đề xuất
    owner: str  # Ai xử lý
    due: date | None  # Hạn xử lý


# Result gains: risks: tuple[Risk, ...] = ()
```

`rules/risk_register.py` (pure):

- `escalate(level, priority) -> RiskLevel`: one step up for urgent/high, never above `HIGH`.
- `ordered(risks) -> tuple[Risk, ...]`: sorts by level, then due date (empty last), then code, then where.
- `LEVEL_TEXT`: the `Cao` / `Trung bình` / `Thấp` labels.

`rules/leave.py` gains `add_working_days(day, n) -> date`, which skips Saturday and Sunday (T5).

`discovery.py`: `_files`, `_only_one`, `_at_most_one`, `_explicit` and the discovery block of `_run` move here as
`discover(args) -> Inputs`. `cli.py` keeps argparse, orchestration, printing and exit codes. Discovery raises
`InputError` and never prints.

Data flow: `cli` → `discovery.discover` → readers → `pipeline.build_result(..., run_day=day)` → `Result.risks`
(empty) → `xlsx_report` + `_print_summary`.

## Related code files

- Create:
  - `src/assigntool/discovery.py`
  - `src/assigntool/rules/risk_register.py`
  - `tests/test_discovery.py` (the discovery cases move here from `tests/test_cli.py`, if they live there)
  - `tests/test_risk_register.py`
- Modify:
  - `src/assigntool/cli.py`
  - `src/assigntool/model.py`
  - `src/assigntool/rules/leave.py`
  - `src/assigntool/rules/pipeline.py`: a `run_day` parameter, passed from `cli.py`
  - `src/assigntool/xlsx_report.py`
  - `tests/test_xlsx_report.py`
  - `LLM.md` §2, §3, §11 (close V1)

## Implementation steps

1. **Commit 1 (refactor):** move discovery to `discovery.py`. Run the whole suite; behaviour must be unchanged. In
   `LLM.md`, close V1 under "Fixed".
2. Add the risk types to `model.py`. It is 224 lines today; if it passes 250, record deviation V2 in `LLM.md` §11.
   Do not split it in this plan.
3. Write `rules/risk_register.py` and `leave.add_working_days`, each with table tests: weekend skipping, n = 0,
   escalation capped at `HIGH`, and the sort order with `None` due dates last.
4. `build_result` gains `run_day: date` and returns `risks=()` for now.
5. `xlsx_report._risks_sheet` writes the `Rủi ro` sheet second, with dates as `DD/MM/YYYY`. An empty register writes
   one row, `Không có rủi ro`.
6. `cli._print_summary` prints the risk line and the `Cao` lines.

## Todo

- [ ] `discovery.py` split; V1 closed
- [ ] `Risk`, `RiskLevel`, `RiskGroup`, `Result.risks`
- [ ] `rules/risk_register.py`, `add_working_days`, with table tests
- [ ] `Rủi ro` sheet, terminal summary
- [ ] Lint, format and tests green

## Success criteria

- `uv run pytest`: all earlier tests pass unchanged, plus the new ones.
- A run on `input/` produces the same `Phân công`, `Cảnh báo` and `Tải dev` as before, and a `Rủi ro` sheet that
  says `Không có rủi ro`.

## Risk assessment

- **The refactor breaks discovery messages:** the tests assert exact messages. Move the code; do not rewrite it.
- **`xlsx_report.py` grows past 250 lines:** keep the row building in pure functions. If it still grows, record V3
  and do not split it in this plan.

## Security considerations

- None new. Nothing leaves the machine.

## Next steps

- Phases 3–6 add producers, in that order.
