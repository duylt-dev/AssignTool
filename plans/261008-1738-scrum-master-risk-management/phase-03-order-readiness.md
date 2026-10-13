# Phase 3 · Step 1: order readiness and feedback to BA

## Context links

- Spec §15 and §16 `READY-GAPS` (phase 1), §6.4 (prompt, reply, parsing), §14 (rules file)
- Form R1–R5, R9, R10, T1, T7; `confirm.md` D14, D17, A18, A33
- `src/assigntool/rules/sizing.py` (`build_prompt`, `parse_reply`, `_json_array`, `_order_lines`)
- `src/assigntool/rules_reader.py` (`read_rules`, `_tables`, `_cells`), `src/assigntool/sprint_reader.py`
- `tests/fake_ai.py`, `tests/test_sizing.py`, `tests/test_rules_reader.py`

## Overview

- Priority: P1. Step 1 is the most concrete ask in the feedback.
- Status: pending.
- Every order of the target sprint gets a list of readiness gaps. Pre-assigned orders are included, because their PIC
  also needs the information (D10 is untouched).
- The gaps are reported three ways:
  - the column `Cần làm rõ` in `Phân công`;
  - one `READY-GAPS` row in `Rủi ro`;
  - one message per `Người tạo` in a new sheet, `Phản hồi BA`.
- A gap never blocks assignment (R1 default).

## Key insights

- **Deterministic gaps** (T1, R2) are cheap, stable and explainable:
  - text description under 30 characters after links are removed;
  - urgent/high order with no `Hạn`;
  - no `App Name`.
- **The AI part is bounded by the checklist.** The AI marks which **given** items are not answered and asks at most 2
  questions. Free-form critique would differ on every run (D27 already shows sizes vary between runs).
- **The checklist lives in the rules file as a second table kind.** `rules_reader` already ignores tables without
  `Loại` and `Dev` (A33), so an old binary reading a new file still works. Discovery (D29) is unchanged: one `.md`.
- **Same AI call as sizing (A18):** no second network round trip, and the same data under D17. The cost: the prompt
  change can move sizes, which phase 7 measures.

## Requirements

**Functional**

1. Rules file:
   - A checklist table has the headers `Loại đơn` · `Từ khoá` · `Cần có`, all required.
   - `Từ khoá` is comma-separated. `Cần có` items are separated by `;`.
   - Several checklist tables are allowed, like rules tables (A33).
   - Input errors, each naming the file, line and column:
     - empty `Từ khoá`;
     - empty `Cần có`;
     - an item over 80 characters.
   - A file with no rules table **and** no checklist table is an input error. One kind alone is fine.
2. Matching:
   - A keyword matches the title after NFC, casefold and whitespace collapse.
   - It matches only on word boundaries (`(?<!\w)kw(?!\w)`), so `ui` does not match `build`.
   - An order that matches several kinds gets the union of their items, in file order, with duplicates removed.
3. Deterministic gaps, as exact texts in spec §15:
   - `không có mô tả bằng chữ`, or `chỉ có <k> link, không có mô tả bằng chữ`;
   - `đơn <urgent|high> chưa có Hạn`;
   - `thiếu App Name`.
4. AI review:
   - Each order line in the prompt gains ` · checklist: <item>; <item>` when items apply.
   - The reply element gains `"missing": [<items copied exactly>]` and `"questions": [<≤ 2, Vietnamese, ≤ 20 words>]`.
   - Parsing:
     - `missing` keeps only items given for that STT (compared after NFC and casefold);
     - `questions` is cut to 2, at 120 characters each;
     - when the keys are absent or wrong, there are no AI gaps for that order;
     - sizes are unaffected in every case.
   - When the AI call fails or is off, only deterministic gaps are shown. There is no new finding:
     `SIZE-AI-FAILED` already says the AI failed.
   - AI gaps are written as `thiếu <item> (AI)` and `hỏi: <question> (AI)`.
5. Deadline (R4), via `clarify_by(base_day, priority, due)`:
   - `add_working_days(base_day, 1 if urgent/high else 2)`;
   - never later than `Hạn`;
   - never earlier than the base day.
6. Output:
   - **Column `Cần làm rõ`:** the last column of `Phân công`. Gaps are joined with `; `; empty when the order is ready.
   - **`READY-GAPS` risk:**
     - level per spec §16;
     - owner: the `Người tạo` cell (R5) or `BA lên đơn`;
     - due: `clarify_by`.
   - **Sheet `Phản hồi BA`:**
     - columns `Người lên đơn` · `Số đơn` · `Hạn bổ sung` · `Tin nhắn`;
     - one row per `Người tạo` value, as written; an empty cell becomes `(không ghi người tạo)`;
     - `Hạn bổ sung` is the earliest deadline among that person's orders;
     - `Tin nhắn` is a ready-to-paste text, one line per order:
       `• STT <n> · <Task>: <gaps>. Cần trước <dd/mm/yyyy>.`
   - **Terminal:** `Đơn cần làm rõ: <k>/<n>`.
7. `sprint_reader` reads the optional `Người tạo` column into `SprintRow.creator` (empty when the column is missing).
   It is never sent to the AI.

**Non-functional**

- The prompt still has no names and no URLs, and stays within the 30,000-character budget. Checklist text counts
  toward the budget. When the budget is hit, checklist items are cut before descriptions are.
- Sizes on `eval/` are no worse than the last results folder (phase 7).

## Architecture

```
rules_reader.read_rules_file(path) -> (tuple[TeamRule], tuple[ChecklistKind])
        │
cli ────┼─► readiness.checklist_items(orders, kinds) -> dict[stt, tuple[str]]
        │        │
        │        └─► sizing.build_prompt(orders, history, items)       (order lines + checklist)
        │                     │
        │   ai_cli.run ───────┘ reply text
        │        ├─► sizing.parse_reply(reply, orders)                 (unchanged contract)
        │        └─► readiness.parse_review(reply, orders, items)      -> dict[stt, AiReview]
        │
pipeline.build_result(..., items, reviews, run_day)
        ├─► readiness.gaps(order, items, review) -> tuple[str]         → Assignment.gaps
        ├─► readiness.ready_risks(assignments, base_day) -> tuple[Risk]
        └─► readiness.feedback_rows(assignments, base_day) -> tuple[FeedbackRow]
```

- New model types:
  - `ChecklistKind(label, keywords, items, line)`
  - `AiReview(missing, questions)`
  - `FeedbackRow(creator, count, due, message)`
  - `Assignment.gaps: tuple[str, ...] = ()`
  - `SprintRow.creator: str = ""`
  - `Result.feedback`
- `sizing._json_array` becomes the public `json_array`, so `readiness.parse_review` reuses it on the same text.

## Related code files

- Create:
  - `src/assigntool/rules/readiness.py` (pure)
  - `tests/test_readiness.py`
  - `docs/checklist-mau.md` (if phase 1 did not create it)
- Modify:
  - `src/assigntool/rules_reader.py`: checklist tables, widened error
  - `src/assigntool/sprint_reader.py`: `Người tạo`
  - `src/assigntool/rules/sizing.py`: checklist in the order lines, reply schema, `json_array`
  - `src/assigntool/model.py`
  - `src/assigntool/rules/pipeline.py`
  - `src/assigntool/xlsx_report.py`: column, sheet
  - `src/assigntool/cli.py`
  - `tests/fake_ai.py`: a canned reply with `missing` and `questions`, and one without them
  - `tests/test_rules_reader.py`, `tests/test_sizing.py`, `tests/test_xlsx_report.py`, `tests/test_pipeline.py`

## Implementation steps

1. `rules_reader`: recognise checklist tables and add the input errors. Tests write real `.md` files:
   - a checklist only;
   - both table kinds;
   - BOM;
   - an escaped pipe;
   - NFD text;
   - each error.

   The backtest keeps reading only the rules.
2. `rules/readiness.py`:
   - `checklist_items`, with keyword boundary tests: `ui` vs `build`, `fix lỗi` as a phrase, Vietnamese diacritics;
   - `deterministic_gaps`: each gap has a fire and a no-fire case;
   - `clarify_by`: across a weekend, capped by `Hạn`, never before the base day.
3. `sizing.build_prompt`: add the checklist to the order lines and the two reply keys to the instructions. Prompt
   tests:
   - items appear for the matching STT only;
   - there are still no names or URLs;
   - the budget order is checklist first, then descriptions.
4. `readiness.parse_review`, with table tests:
   - unknown item dropped;
   - 3 questions cut to 2;
   - keys absent;
   - wrong types;
   - failed reply;
   - sizes unchanged in every case.
5. `pipeline`: attach the gaps and build `READY-GAPS` risks and feedback rows.
6. `xlsx_report`: the `Cần làm rõ` column and the `Phản hồi BA` sheet (empty → `Không có đơn cần làm rõ`).
7. `cli`: read the checklist, pass the items through, print the terminal line.
8. Run on `input/` with `--ai off`. Count the flagged orders in Sprint 10 and compare by hand with the data numbers
   (T1).

## Todo

- [ ] Checklist tables in `rules_reader` with input errors
- [ ] `readiness.py`: items, deterministic gaps, `clarify_by`, `parse_review`, risks, feedback rows
- [ ] Prompt and reply schema in `sizing.py`; `fake_ai.py` replies
- [ ] `Cần làm rõ` column, `Phản hồi BA` sheet, terminal line
- [ ] Spec §15 examples match the real output
- [ ] Lint, format and tests green

## Success criteria

- Each deterministic gap and `READY-GAPS` has a fire and a no-fire test (LLM.md §8).
- With `--ai off`, readiness is fully deterministic: two runs produce the same `Cần làm rõ` column.
- With `--ai gemini` or `agy`, the reply still parses for every order, and sizes are as good as before (phase 7).

## Risk assessment

- **Longer replies:** `agy` already takes about 120 s (`LLM.md` §9). Add about 30% to the timeout guidance in the
  spec, and measure in phase 7.
- **Too many flags:** an order with only AI questions is `Thấp`. The register is sorted by level, so real gaps come
  first.
- **BA ignores the messages:** out of the tool's control. Phase 7 reports the share of flagged orders per sprint so
  management can see the trend.

## Security considerations

- `Người tạo` stays out of the prompt. A test asserts that no creator name appears in the prompt.
- Checklist text goes to the AI under D17. The spec forbids names in checklist items.

## Next steps

- Phase 4.
