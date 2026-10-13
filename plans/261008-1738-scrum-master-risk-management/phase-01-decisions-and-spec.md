# Phase 1 · Decisions and spec

## Context links

- Form: `plans/reports/261008-cau-hoi-scrum-master-quan-ly-rui-ro.md` (R1–R11, T1–T7)
- `confirm.md` (D7, D10, D14, D17, D19, D26, A12, A18, O8)
- `docs/assignment-spec.md` §2, §6.3, §6.4, §7, §9, §10, §11, §14
- `LLM.md` §2, §3, §4, §10, §12; `.claude/CLAUDE.md` "Non-negotiable rules"

## Overview

- Priority: P1. It blocks every later phase: the repo rule is spec and `confirm.md` first, then code.
- Status: in progress. Answers recorded on 2026-10-09: the 09/10 form became D36–D48 and A45–A53, the 08/10
  defaults were applied (D48, A45), and the Chrome measurements became A46, A49, O11–O13. Spec is next.
- Docs only, no code.

## Key insights

- 22/40 sample orders have no text description, and only 3 of those 22 have a link. Clarification is a process gap at
  the BA, so it must not block assignment (R1 default).
- 1 of 178 history orders has a `Ngày đóng`, so lateness cannot be learned from history. Progress risks therefore
  use only current statuses, due dates and the run day.
- 8 of 40 orders have no version in the title, and all 8 are research or `Nhiều App` orders. A "missing version"
  check would only produce false alarms, so it is dropped (T7).
- In 40 sample orders, App + Task + Ngày tạo is unique. That is good enough as the match key until the export has
  an `ID` column (phase 6).

## Requirements

1. Record every answer:
   - An explicit or blank answer becomes a `D` row.
   - With no form at all, Claude's defaults become `A` rows.
   - An ambiguous answer becomes an `O` row.
   - R5 touches D14 and R7 touches D10: without an answer, those D rows stay as they are.
2. Write the spec before any code:
   - **§15 Readiness (new):**
     - the checklist table;
     - the deterministic gaps;
     - the AI review fields;
     - the deadline rule;
     - the `Phản hồi BA` sheet.
   - **§16 Risk register (new):** levels, escalation, sort order, and for each code: when it fires, its level, and the
     exact Vietnamese texts for problem, impact, action, owner and due date.
   - **§17 Change log (new):** the previous report, the match key, the change kinds, and the `Thay đổi` sheet.
   - **§2:** `--compare FILE`.
   - **§6.3 and §7:** remaining-days leave (if R8 is accepted).
   - **§6.4:** the reply gains `missing` and `questions`.
   - **§9:** new finding codes `DEV-ON-LEAVE-REST`, `STATUS-STALE`, `COMPARE-UNREADABLE`, each with its exact message.
   - **§10:** the new sheets and columns.
   - **§11:** the new terminal lines.
   - **§14:** the checklist table kind, its input errors, and the "no rules table" error widened to "neither table".
3. Add `docs/checklist-mau.md`: the R3 seed table, for the TM to copy into the rules file. It is not placed in
   `input/`, because an `.md` there is picked up by discovery (D29).
4. Update the docs:
   - `LLM.md` §2: `report_reader.py` joins the `openpyxl` importers; `discovery.py` joins the layers.
   - `LLM.md` §3: the new modules.
   - `LLM.md` §4: a row for "a new risk".
   - `LLM.md` §12: a new pattern, "risks advise, never change a PIC".
   - The `.claude/CLAUDE.md` non-negotiable list.

## Architecture: draft of spec §16 (finalised in this phase)

| Code | Group | Fires when | Level | Owner |
|---|---|---|---|---|
| `READY-GAPS` | Đơn chưa rõ | An order has at least one readiness gap (§15) | Trung bình; Thấp if the only gaps are AI questions; one step up for urgent/high | `Người tạo` cell (R5), else `BA lên đơn` |
| `CAPACITY-DEV` | Năng lực | A dev's load (D8-busy or empty-status orders, in AI hours) > capacity | Trung bình; Cao above 1.5× | TM |
| `CAPACITY-SPRINT` | Năng lực | The sum of loads > the sum of capacities of the pool | Cao | TM + PO |
| `PIC-UNFAMILIAR` | Phân công | A proposed PIC has familiarity rank 2, and either level < middle or the order is urgent/high | Thấp; one step up for urgent/high | TM |
| `PIC-ABSENT` | Tiến độ | An order whose pool devs are all on leave for every remaining working day | Cao | TM |
| `DUE-AT-RISK` | Tiến độ | (a) status not started and ≤ 3 working days to the deadline; (b) not done and past `Hạn` | Trung bình; Cao when ≤ 1 day or overdue | PIC code |

- **Deadline of an order:** `Hạn`, else the sprint's last day.
- **Base day:** the later of the run day and the sprint's first day.
- **Capacity:** 6h × (the remaining working days from the base day − leave days among them).
- **Sort order:** level, then due date (empty last), then code, then where.

Draft messages (finalised in the spec):

- `READY-GAPS`
  - Problem: `Đơn STT <n> chưa rõ: <gap>; <gap>`
  - Impact: `Độ lớn <class> có thể sai; PIC phải hỏi lại trước khi làm.`
  - Action: `Bổ sung trước <dd/mm/yyyy>: <items>`
- `CAPACITY-DEV`
  - Problem: `<Mã> giữ <h>h việc (<n> đơn), sức chứa còn <c>h (<d> ngày × 6h)`
  - Action: `Cân nhắc chuyển STT <x> cho <Mã2> (còn trống <f>h)`
- `CAPACITY-SPRINT`
  - Problem: `Sprint có <h>h việc, sức chứa của team còn <c>h`
  - Action: `Đề xuất đẩy sang sprint sau: STT <a>, <b> (<k>h), hoặc thêm người ngoài team`
- `PIC-ABSENT`
  - Problem: `Đơn STT <n> giao cho <Mã> nhưng <Mã> nghỉ các ngày còn lại của sprint (từ <dd/mm>)`
  - Action: `Chuyển cho <Mã2>: <§8 reason>`
- `DUE-AT-RISK`
  - Problem (a): `Đơn STT <n> còn <k> ngày làm việc tới hạn <d> nhưng vẫn "<status>"`
  - Problem (b): `Đơn STT <n> quá Hạn <d> (trạng thái "<status>")`
  - Action: `Hỏi <PIC> lý do; nếu kẹt: chuyển cho <Mã2> hoặc lùi hạn`

## Related code files

- Modify: `confirm.md`, `docs/assignment-spec.md`, `LLM.md`, `.claude/CLAUDE.md`, `README.md` (sheet list)
- Create: `docs/checklist-mau.md`

## Implementation steps

1. Wait for the form. If it does not come back, apply the defaults and record them as A rows. Then add rows (next free
   numbers: D36+, A45+, O11+). Close or reference O8 for phase C.
2. Write spec §15–§17. Then patch §2, §6.3, §6.4, §7, §9, §10, §11 and §14, with exact Vietnamese texts.
3. Write `docs/checklist-mau.md` from R3, with any edits the user made.
4. Patch `LLM.md` §2, §3, §4 and §12, and the CLAUDE.md non-negotiables.
5. Check every new code: it is in spec §9 or §16 with its message, and its fire and no-fire tests are planned.

## Todo

- [x] Answers recorded in `confirm.md` (2026-10-09)
- [ ] Spec §15, §16, §17 written; §2, §6.3, §6.4, §7, §9, §10, §11, §14 patched
- [ ] `docs/checklist-mau.md`
- [ ] `LLM.md`, `.claude/CLAUDE.md`, `README.md` patched

## Success criteria

- Every code, column, sheet and terminal line of phases 2–6 is in the spec with its exact text.
- No D row changes without an answer.
- `uv run pytest` is still green (docs-only phase).

## Risk assessment

- **The user rejects R1 and asks for blocking:** spec §15 gains a "not ready" state that leaves the PIC empty. This
  changes D19's flow and needs a D row.
- **The user rejects R5:** messages are addressed to the role `BA lên đơn`, and `Phản hồi BA` has one message for
  the whole sprint instead of one per `Người tạo`. The TM still sees `Người tạo` in `Phân công`, where it is copied
  as written.

## Security considerations

- Checklist items are company text with no personal data. They go to the AI under D17, so the spec says checklist
  items must not contain names.

## Next steps

- Phase 2.
