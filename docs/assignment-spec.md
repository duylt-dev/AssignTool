# Assignment spec: `assigntool`

What the tool reads, how it sizes orders, how it picks a PIC for each order, and what it writes.
[`LLM.md`](../LLM.md) says where each part lives in code; [`confirm.md`](../confirm.md) holds the decisions cited
here as `Dn` (user-locked), `An` (defaults) and `On` (open).

**Status:** approved 2026-10-06 and implemented; updated 2026-10-07 for the history export of list "Tech manager"
(D6), the load cap in orders (D26) and the backtest (D22, §13), then for the TM rules file (D28–D35, §14). Every number in §12 and §13 is asserted by
`tests/test_real_input.py` and `tests/test_pipeline.py`; the §13 table was also reproduced by a separate script that
shares no code with the tool.

User-facing text (column headers, finding messages, reasons, terminal lines) is Vietnamese (D12). It is quoted here
exactly as the tool must print it.

| § | Contents |
|---|---|
| 1 | Terms |
| 2 | Command line |
| 3 | Input: sprint workbook |
| 4 | Input: dev workbook |
| 5 | Input: history export (list "Tech manager") |
| 6 | Derived facts: familiarity, carry-over, leave, size |
| 7 | Choosing the PIC |
| 8 | Reason text |
| 9 | Findings |
| 10 | Output workbook |
| 11 | Exit codes and terminal output |
| 12 | Acceptance on the sample |
| 13 | Backtest |
| 14 | Input: TM rules |

---

## 1 · Terms

| Term | Meaning |
|---|---|
| Order (*đơn*) | A row whose `Loại` is `Task`: one version of one app, e.g. `1.0.2 - Add ads/Add SDK` for Phone Cleaner. The unit of assignment (D5). |
| PIC | The one dev who owns an order and later splits it into subtasks (D5). |
| Pool | Devs in `devs.xlsx` with `Nhận việc` = `Y`, minus those on leave for the whole sprint (A12). Today: LinhNV, MinhNM, AnTD, TiếnBV (D7). Everyone else is ignored everywhere, silently (D14). |
| Target sprint | The sheet the tool assigns: the highest `Sprint N` (A3). The tool may run at any time during it (D2): orders already assigned are kept, empty ones are assigned. |
| Previous sprint | Sheet `Sprint N-1` of the same workbook. Source of carry-over only (A9). |
| Size | The AI's class for an order, `S`/`M`/`L`/`XL`, worth 4/16/32/64 hours (§6.4, A7). |
| Load | The orders a pool dev holds in the target sprint, pre-assigned or proposed: counted in orders for the load cap (§7, D26) and summed in hours (their sizes) for key part 3. |
| Carry-over | Number of rows in the previous sprint assigned to the dev whose status is busy (D8). |
| Familiarity | How well a dev knows the order's app, from the history (§5, §6.1). |
| TM rule | One row of the TM's rules file (§14): pin a dev to an app, keep a dev off an app or off everything, cap a dev's orders, or prefer a dev for an app. Read without AI (D28). |
| Board | List "Tech manager" holds two boards: Maintain (two-week sprints, the orders this tool assigns) and MVP / research (one- to two-month sprints). Only Maintain orders are assigned (D5); MVP orders are history only (D23). |

## 2 · Command line

```
assigntool [--input DIR] [--sprint FILE] [--devs FILE] [--history FILE] [--rules FILE] [--sheet NAME] [--out DIR]
           [--ai gemini|agy|off] [--ai-model NAME] [--ai-timeout SECONDS] [--backtest] [-v]
```

| Option | Default | Meaning |
|---|---|---|
| `--input DIR` | `input/` | Where inputs are discovered. |
| `--sprint FILE` | the only `*.xlsx` in `--input`, other than `devs.xlsx`, that has a `Sprint N` sheet | Sprint workbook (§3). |
| `--devs FILE` | `<input>/devs.xlsx` | Dev workbook (§4). |
| `--history FILE` | the only other `*.xlsx` (no `Sprint N` sheet) or `*.csv` in `--input`; none → the workbook's older sprint sheets (§5) | History export (§5). |
| `--rules FILE` | the only `*.md` in `--input`; none → no rules | TM rules (§14, D29). |
| `--sheet NAME` | highest `Sprint N` | Target sprint sheet. The previous sprint is then `Sprint N-1`. |
| `--out DIR` | `output/` | Where the report is written. Created if missing. |
| `--ai` | `gemini` | AI tool used for sizing (§6.4, D16, A17). `agy` is for the dev machine; `off` sizes every order `M`. |
| `--ai-model` | the AI tool's own default | Model name passed through to the AI tool. |
| `--ai-timeout` | `180` | Seconds before the AI call is killed and sizes fall back to `M`. |
| `--backtest` | off | Replay every Maintain sprint of the history export and compare with the TM (§13). Needs only `--history` and `--devs` (and uses `--rules`); `--sprint`, `--sheet` and the `--ai` options are ignored. |
| `-v` | off | Show tracebacks for input errors and the AI tool's raw output. |

Discovery reads content, not names (A2): each `.xlsx` other than `devs.xlsx` is opened, and the one with a `Sprint N`
sheet is the sprint workbook; every other `.xlsx`, and every `.csv`, is a history candidate; an `.md` file is the
rules file. Discovery never guesses: zero sprint workbooks, several, several history candidates or several `.md` files
is an input error that names the candidates and the flag
to use; an `.xlsx` that cannot be opened is an input error naming it. Files whose names start with `~$` (Excel lock
files) and `.` are ignored.

## 3 · Input: sprint workbook

The export of the internal tool, one sheet per sprint. Layout as observed in the sample:

| Rows | Content |
|---|---|
| 1 | `Sprint 10 (10/6 - 10/17)` |
| 2 | Project name |
| 3 | `Thời gian: 2026-10-06 → 2026-10-17   ·   Tiến độ: …` |
| 5 | Header row |
| 6 … | Data rows; column A (`STT`) is an integer |
| after the data | A formula footer, a blank row and a note; column A is not an integer |

**Reading rules**

1. Sheets are selected by name `Sprint <N>` (regex `^Sprint\s+(\d+)$` after trimming). Other sheets are ignored.
2. The header row is the first row within rows 1–10 whose column A is `STT`. Columns are found **by header name**,
   never by position. Header names are compared after NFC, trimming, removing a trailing `.` and casefolding, so
   `App Name.` and `App Name` both match.
3. Data rows run from the row after the header while column A is an integer, and stop at the first row where it is
   not. The workbook is opened with cached values (`data_only=True`) so the formula footer is never read as text.
4. Sprint dates come from row 3, regex `(\d{4}-\d{2}-\d{2})\s*→\s*(\d{4}-\d{2}-\d{2})`. If absent, the sprint has no
   known dates: leave days are ignored (§6.3) and nobody is excluded for leave.
5. Indentation of `Task` gives the tree: each `└` level is 4 leading spaces. The title is the cell with leading spaces
   and `└ ` removed. The tree is used only to skip subtasks; `Task cha` is not used (A4).

**Columns**

| Header | Required | Use |
|---|---|---|
| `STT` | ✓ | Row identity in findings, output and the AI exchange; last sort key. |
| `Task` | ✓ | Order title. Sent to the AI (§6.4). |
| `Loại` | ✓ | `Task` = order; `Subtask` = skipped. Any other value: the row is skipped with `TYPE-UNKNOWN`. |
| `App Name.` | ✓ | Order's app (A10 matching). Empty on an order: `APP-MISSING`, treated as an app nobody knows. |
| `Trạng thái` | ✓ | Previous sprint only: busy statuses (D8, §6.2). |
| `Người làm` | ✓ | Comma-separated full names. A non-empty value on a target-sprint order means pre-assigned and kept (D10), whoever is named. Only pool devs named get load; other names are ignored silently (D14). |
| `Ưu tiên` | ✓ | `urgent`, `high`, `normal`, `low` or empty (= normal). Other: `PRIORITY-UNKNOWN`, treated as normal. |
| `Hạn` | ✓ | Date or empty. Sort key (A5). Before `Ngày tạo`: `DUE-BEFORE-CREATED`. |
| `Ngày tạo` | ✓ | Date. Sort key (A5). |
| `Mô tả` | — | Sent to the AI, with links removed and truncated (§6.4). |
| `Ước lượng (h)` | — | **Ignored** on the target sprint (D3, A19). |
| all other columns | — | Copied to the output unchanged (§10). |

A required header missing from the **target** sheet is an input error. On the **previous** sheet only `Loại`,
`Trạng thái` and `Người làm` are required.

## 4 · Input: dev workbook

`devs.xlsx`, maintained by hand (D11). First sheet, header on row 1, one dev per row, empty rows ignored.

| Header | Required | Values |
|---|---|---|
| `Tên` | ✓ | Full name exactly as the internal tool writes it in `Người làm`, e.g. `Ngọc Văn Linh`. Unique. |
| `Mã` | ✓ | Short code shown in the output, e.g. `LinhNV`. Unique. |
| `Level` | ✓ | `junior`, `junior+`, `middle`, `middle+`, `senior`, case-insensitive (A13). |
| `Nhận việc` | ✓ | `Y` or `N`. `N` takes a dev out of the pool without deleting the row. |
| `Ngày nghỉ` | — | Leave days inside the sprint, separated by `,`: `YYYY-MM-DD` or `DD/MM/YYYY`, or real date cells. |

Example (the pool of D7; the full names are the ones the sample export uses):

| Tên | Mã | Level | Nhận việc | Ngày nghỉ |
|---|---|---|---|---|
| Ngọc Văn Linh | LinhNV | middle+ | Y | |
| Nguyễn Nhật Minh | MinhNM | middle | Y | |
| Trần Đức An | AnTD | junior+ | Y | |
| Bùi Văn Tiến | TiếnBV | junior | Y | |

Input errors: a missing required header, an invalid level, `Nhận việc` not `Y`/`N`, a duplicate `Tên` or `Mã`, an
unreadable date, and an empty pool after leave exclusion.

**Known cost of D14:** a pool dev's name spelled differently in an export (missing diacritic, extra word) is treated
as a stranger, so that dev's load is silently too low. NFC and whitespace normalisation (A10) remove the common
cases; the remaining ones are not reported.

## 5 · Input: history export (list "Tech manager")

The export of list "Tech manager" from the internal system's database (D6, D20), as `.xlsx` or `.csv`. It replaces
the history CSV the project once defined itself (A20). The sample, `input/Tech_manager_T2-T10_2026.xlsx`, covers
February to October 2026: 3,144 rows, 178 root orders.

**Layout.** `.xlsx`: one sheet per month (`Tháng 2` … `Tháng 10`), header on row 1, data from row 2; a sheet whose
row 1 has no `Ngày lên đơn` (the sample's `Tổng hợp` summary) is skipped, and a file with no such sheet is an input
error. `.csv`: the same columns in one file; encoding, delimiter and dates as A15 (UTF-8 with or without BOM, `,` or
`;`, `YYYY-MM-DD` or `DD/MM/YYYY`). Header names are matched like §3 rule 2; extra columns are ignored.

**Rows used.** Only **root orders**: `Loại` = `Task` and `Task cha` empty. Subtasks (`Task cha` set) and bugs
(`Loại` = `Bug`) are skipped: the PIC splits subtasks (D5), and familiarity counts the root order's `Người làm`
only (A26). `Task cha` holds a name, not an ID, so the task tree is never rebuilt from this file.

| Header | Required | Use |
|---|---|---|
| `Ngày lên đơn` | ✓ | Filing date (`2026-09-22 09:36`): recency for the latest version (§6.1), the history window (§5.1), the replay day (§13). Empty or unreadable on a root order: input error naming the sheet, row and column. |
| `Tên task` | ✓ | Quoted in the reason text; sent to the AI as an example when it has hours. |
| `Loại` | ✓ | `Task` = order or subtask; `Bug` = skipped. |
| `Task cha` | ✓ | Empty = root order; set = subtask, skipped. |
| `App Name` | ✓ | App (A10 matching, no alias table: A27). Root orders with an empty app are kept but never make anyone familiar. |
| `Người làm` | ✓ | Comma-separated full names; names outside the pool are ignored (D14). |
| `Sprint` | ✓ | Sprint labels, §5.2. Quoted in the reason text as written (A25). |
| `Ưu tiên` | — | Order of the replay (§13), as A5. |
| `Due date` | — | Order of the replay (§13). Unreadable: input error. |
| `Ước lượng (h)` | — | Not in the export today (D25). When present: hours sent to the AI as examples (A19). |
| `ID`, `Trạng thái`, `Người tạo`, `Điểm`, … | — | Not used. `Điểm` is not hours (4h → 2.5, 24h → 9, 83h → 21.5). `Trạng thái` is the status today, not at the time of a past sprint, so carry-over still comes from the sprint workbook (§6.2). |

### 5.1 History window (A22)

A run uses the history orders that existed **before it**:

1. not an order of the target sprint (a label equal to it, §5.2): an order never serves as its own history;
2. filed (`Ngày lên đơn`) on or before the run day;
3. its earliest sprint, if it has one, started on or before the run day.

The run day is today for a normal run, and the day the order was filed for the backtest (§13). The same rule in both
places means the backtest measures exactly what a normal run does, and never sees an assignment made later.
History includes MVP / research orders and orders with no sprint (A23, D23). A history file is never combined with
the workbook's older sheets (A8).

### 5.2 Sprint labels (A24)

A `Sprint` cell holds zero, one or several labels `Sprint <n> (<m>/<d> - <m>/<d>)`, comma-separated:
`Sprint 18 (4/17 - 4/29), Sprint 19 (5/6 - 5/20)`. An order belongs to every sprint it lists. A label has no year:
the start gets the year that puts it nearest to `Ngày lên đơn`, and the end the first date on or after the start, so a
sprint across New Year is dated right. Text that is not a label is skipped. Two labels are the same sprint when the
number, the start and the end all agree: `Sprint 1 (5/22 - 6/5)` (Maintain) and `Sprint 1 (5/22 - 7/15)` (MVP) share
number and start date. A label of at most 21 days is a Maintain sprint, longer is MVP / research (A21; Maintain
sprints last 4–17 days in the sample, MVP sprints 27–54).

The target sprint of a normal run is matched by its sheet number and the dates of §3 rule 4; when the sheet has no
dates, by number only.

**No history file (A8).** When `--history` is not given and discovery finds no candidate, the history is every sprint
sheet of the workbook numbered below the target (the sample: `Sprint 6` to `Sprint 9`, 34 orders): `Task` rows with an
app, a name and a `Ngày tạo`, `Ước lượng (h)` as hours, the sheet name as the sprint quoted in reasons. Required headers
on those sheets: `Loại`, `App Name.`, `Người làm`, `Ngày tạo`. The run then reports `HISTORY-FROM-WORKBOOK`, or
`HISTORY-MISSING` when there is no older sheet either.

## 6 · Derived facts

§6.1–§6.3, §7 and the prompt and parsing of §6.4 are pure computation over values from §3–§5 (LLM.md §2). Only the
call to the AI tool itself is I/O.

### 6.1 Familiarity of a dev with an app

For each app, consider the history orders of that app that name **at least one pool dev**. The most recent of them
by `Ngày tạo` is the app's **latest version**. Orders naming only people outside the pool are ignored here: an RnD
research order is not a version a pool dev worked on.

| Rank | Meaning | Reason text |
|---|---|---|
| 0 | The dev is named on the app's latest version. | `Làm version gần nhất của <app> (<Sprint>: <Task>)`; `<Sprint>` is the history order's `Sprint` cell as written, `Tháng <m>/<yyyy>` of `Ngày lên đơn` when it is empty, or the sheet name for workbook history (A25) |
| 1 | The dev is named on an older version only. | `Từng làm <app> (<k> version)` |
| 2 | Never named on this app. | `Chưa làm <app>` |

An app with no history order naming a pool dev is a **new app**: every dev has rank 2.

### 6.2 Carry-over

For each pool dev: the number of previous-sprint rows (orders **and** subtasks) that name the dev in `Người làm` and
whose `Trạng thái` is busy (D8): `qa - need fix`, `all issue`, `in progress`, `ready to progress`, `need to be clean`,
`internal - cant fix`, `internal - need fix`, `đã ro`. Every other status (`pending`, `qa - cant fix`, waiting for test,
done) is not busy. Statuses are compared after NFC, trimming and casefolding. `đã ro` is busy by the user's choice
(D8), although in the sample it occurs only in Sprint 8, whose 11 orders are all done.

### 6.3 Leave

Working days of the sprint are Monday to Friday between the dates of §3 rule 4, inclusive. A dev whose leave days
cover every working day is removed from the pool (`DEV-ON-LEAVE`). Otherwise the number of leave days on working days
is a tie-breaker only (A12). Leave days outside the sprint are ignored.

### 6.4 Size (AI)

Every order of the target sprint gets a size, **pre-assigned ones included**, because their size counts toward
load (D13). The AI only sizes; it never sees people and never picks a PIC.

**Classes** (A7):

| Class | Hours | Meaning given to the AI |
|---|---|---|
| `S` | 4 | At most a day: a crash fix, a policy fix, a text or config change. |
| `M` | 16 | Two to three days. |
| `L` | 32 | About a week. |
| `XL` | 64 | More than a week: a new feature, a new SDK, several flows at once. |

**Tool selection** (`--ai`, A17):

| Value | Command |
|---|---|
| `gemini` (default) | `gemini -p "" -o json --approval-mode plan --skip-trust [-m <m>]`, with the prompt on **stdin**. Found with `shutil.which`. Authentication is the user's: a valid `GEMINI_API_KEY` in the environment (D16). Flags checked against 0.57.0. |
| `agy` | `agy -p <prompt> --mode plan --output-format json --print-timeout <t>s [--model <m>]`. Found in `PATH`, then in `~/.gemini/bin/`. The prompt goes in the argument list: `agy` does not read stdin (measured, 1.2.17). For the dev machine, where `gemini` cannot authenticate. |
| `off` | No call; every order is `M`, with no finding. |

A tool that is not found is a failed call (`SIZE-AI-FAILED`), not an input error: the run still produces a report.

The child runs in a **fresh empty temporary directory** with the user's environment, so the agent cannot read
`input/`. It is killed after `--ai-timeout` seconds.

**Prompt.** One call for the whole sprint (A18), built by a pure function:

1. Instructions: the class table above; "judge from the text only, do not open links or use tools"; the output
   format below.
2. Up to 30 **examples**: history orders with `Ước lượng (h)` > 0, the target sprint's apps first, then most recent
   first. Each line: app · title · hours. No names.
3. The **orders**: each line `STT` · app · priority · title · description. In the description every URL is replaced
   by `[link]` and the text is cut to 600 characters.
4. If the prompt is longer than 30,000 characters, descriptions are cut to 200 characters, then dropped. This keeps
   the `agy` argument under Windows' 32,767-character command-line limit.

**Expected reply:** a JSON array, one element per order:

```json
[{"stt": 10, "size": "M", "reason": "Sửa luồng export và thêm 2 vị trí ads"}]
```

**Parsing:** the tool's stdout is a JSON envelope with the model's text in `response` (both tools). `gemini`
0.57.0 writes `{session_id, response, stats, error, warnings}` (read from its `JsonFormatter`); an `error` object, or
a non-zero exit, is a failure whose `error.message` becomes the short reason. `agy` has `status`, which must be
`SUCCESS`. From `response`, code fences are stripped and the first `[` … last `]` is parsed.
An element is valid when `stt` is one of the orders, appears once, and `size` is one of the four classes; `reason`
is cut to 120 characters.

**Fallback:** an order without a valid element is sized `M`. A failed call (tool not found, non-zero exit, timeout,
`status` not `SUCCESS`, no parsable array) sizes every order `M`. Either way the run continues and the report says
which sizes are defaults (§9, §10).

**Determinism:** the same input can be sized differently on two runs. Sizes and the AI's reasons are shown in the
report so the TM can see why a load is what it is. Tests never call a real AI except the opt-in smoke test
(LLM.md §8).

## 7 · Choosing the PIC

1. **Pre-assigned orders are kept** (D10). Each pool dev named on one gets load + the order's size.
2. **Remaining orders are processed one at a time** in the order of A5: priority, due date (empty last), creation
   date, `STT`. The TM rules in force (§14.3) apply to these orders only.
3. For each order:
   - **Candidates:** the pool minus every dev a `Không giao` rule keeps off the order's app (or off every app), and
     every dev who already holds the number of orders of their `Tối đa đơn` rule (pre-assigned orders count). When
     the rules leave nobody, the order is assigned as if those two kinds of rule did not exist, with
     `RULE-NO-CANDIDATE` (A31). Without rules the candidates are the pool.
   - **Pin (D31):** when a `Chỉ định` rule names the order's app and its dev is a candidate, that dev is the PIC; the
     load cap and the key below are skipped, as for a pre-assigned order. A pinned dev who is not a candidate (on
     leave for the whole sprint, `Nhận việc` = `N`, or at their `Tối đa đơn`) does not pin; the order goes through
     the steps below.
   - `needs_senior` is true when the priority is `urgent` or `high`, or the app is new (§6.1).
   - **Load cap (D26, A30):** only candidates holding at most **one order more** than the candidate with the fewest
     orders can be chosen. This keeps a dev who knows many apps from taking every order. It counts orders, not
     hours: in hours, the AI's sizes decided who was capped, and they vary between runs (D27; §12, "Sensitivity").
   - Among them, the PIC is the dev with the **smallest key**, compared left to right:

     | # | Key part | Smaller is better |
     |---|---|---|
     | 0 | TM preference (D32) | 0 when an `Ưu tiên` rule names this dev for the order's app; else 1 |
     | 1 | familiarity rank (§6.1) | 0 = latest version |
     | 2 | seniority gap | 0 when `needs_senior` is false or level ≥ `middle`; else 1 |
     | 3 | load (hours) | less work in this sprint |
     | 4 | carry-over (§6.2) | fewer busy rows left from the previous sprint |
     | 5 | leave days (§6.3) | fewer days off |
     | 6 | level, descending | higher level first |
     | 7 | `Mã` | alphabetical, so the result is deterministic |

     Without rules, part 0 is 1 for everyone and the choice is exactly the one before rules existed.
   - **Backups:** the next two candidates by the same key, ignoring the load cap. A backup excluded by the cap is
     still useful to the TM, who may prefer familiarity over balance; a dev the TM's rules keep off the order is not
     (A32).
   - The PIC's load is increased by the order's size before the next order.

**Why a key and not a weighted score.** Every part of the key can be stated as a sentence in the reason (§8), and the
TM can check it by eye. Weights would need tuning against data we do not have, and a score of 0.73 explains nothing.

**Why familiarity comes before seniority, even on urgent orders.** The person who built the last version is the
fastest on the next one. The sample agrees: the TM gave a `high` Game Emulator order to AnTD (junior+), the only dev
who had worked on that app.

**Why the AI sizes but does not choose.** The choice must be explainable and repeatable; a size is one input among
seven, and a wrong size moves load by a few hours, not the whole decision. With the cap in orders, a size only
changes key part 3 (hours), never who is allowed to take the order.

## 8 · Reason text

The `Lý do` cell joins these parts with ` · `, in this order, leaving out parts that do not apply:

0. The TM rule that chose the PIC: `Luật TM dòng <n>: chỉ định <Mã> cho <app>` for a pin, or
   `Luật TM dòng <n>: ưu tiên <Mã> cho <app>` when the PIC has key part 0 = 0; followed by ` (<Ghi chú>)` when the
   rule has a note. `<n>` is the rule's line in the rules file.
1. Familiarity text of §6.1.
2. `Đơn <priority> → ưu tiên middle trở lên` when `needs_senior` is caused by priority; `App chưa ai trong team làm →
   ưu tiên middle trở lên` when it is caused by a new app. Only when the PIC is middle or above.
3. `Tải sprint này: <h>h (<n> đơn)` (load before this order).
4. `Việc dở <previous sprint>: <n>`.
5. `Nghỉ <n> ngày` when n > 0.
6. For each dev with a better familiarity rank who was excluded by the load cap:
   `<Mã> quen app hơn nhưng đang có <n> đơn (cân tải)`.
7. For each dev with the same rank but a better seniority gap (middle or above when `needs_senior`) who was excluded
   by the load cap: `<Mã> là middle trở lên nhưng đang có <n> đơn (cân tải)`. Without it, a junior chosen for a
   new-app order looks like a mistake (first real run, §12 note).
8. For each dev with a better TM preference (key part 0) who was excluded by the load cap:
   `<Mã> được ưu tiên (luật TM dòng <n>) nhưng đang có <k> đơn (cân tải)` (D32).
9. For each dev a rule kept off the order (not a candidate) whose key is smaller than the PIC's, or who is the dev of
   a `Chỉ định` rule for the app: `<Mã> không nhận đơn (luật TM dòng <n>)` for `Không giao`, `<Mã> đã đủ <k> đơn
   (luật TM dòng <n>)` for `Tối đa đơn`.

Parts 6–8 compare keys from the left: a dev is listed under the first key part where they beat the PIC.

A pinned order's reason is parts 0, 1, 3, 4 and 5: the pin decided, so the seniority and cap parts do not apply.

Example: `Làm version gần nhất của PS Remote (Sprint 9 (9/21 - 10/2): 1.1.1 - Fix ads/FIx luồng/ fix policy) · Đơn
urgent → ưu tiên middle trở lên · Tải sprint này: 0h (0 đơn) · Việc dở Sprint 9: 0`.

With a pin: `Luật TM dòng 5: chỉ định LinhNV cho AR Dog (Linh giữ AR Dog) · Làm version gần nhất của AR Dog (…) ·
Tải sprint này: 32h (2 đơn) · Việc dở Sprint 9: 1`.

When the order has no app, part 1 is `Đơn không có App Name`. Pre-assigned orders get the reason
`Đã giao sẵn trong file`. Dates in messages are written `DD/MM/YYYY`.

## 9 · Findings

A finding is a row in the `Cảnh báo` sheet, not an exception: the run goes on and the report is written. Codes are
never renamed once released. Nothing is ever reported about people outside the pool (D14).

| Code | Level | When | Message (Vietnamese, exact) |
|---|---|---|---|
| `SIZE-AI-FAILED` | WARN | The AI call failed (§6.4). | `Không ước lượng được độ lớn bằng AI (<lý do ngắn>); mọi đơn tính là M (16h).` |
| `SIZE-AI-INVALID` | WARN | The call worked but some orders have no valid element. One finding listing them. | `AI không trả độ lớn hợp lệ cho đơn STT <danh sách>; các đơn này tính là M (16h).` |
| `APP-MISSING` | WARN | An order has an empty `App Name.`. | `Đơn STT <n> không có App Name; coi như app chưa ai làm.` |
| `PRIORITY-UNKNOWN` | WARN | `Ưu tiên` is not urgent/high/normal/low/empty. | `Đơn STT <n> có Ưu tiên "<giá trị>" không hợp lệ; coi như normal.` |
| `DUE-BEFORE-CREATED` | WARN | `Hạn` is before `Ngày tạo`. | `Đơn STT <n> có Hạn <hạn> trước Ngày tạo <ngày tạo>.` |
| `TYPE-UNKNOWN` | WARN | `Loại` is neither `Task` nor `Subtask`. | `Dòng STT <n> có Loại "<giá trị>" không hợp lệ; bỏ qua dòng này.` |
| `PREV-SPRINT-MISSING` | WARN | No sheet `Sprint N-1`. | `Không có sheet <tên>; coi như không dev nào còn việc dở.` |
| `HISTORY-MISSING` | WARN | No history file and no sprint sheet older than the target (§5). | `Không có file lịch sử và workbook không có sheet sprint cũ; coi như chưa ai làm app nào.` |
| `HISTORY-FROM-WORKBOOK` | INFO | No history file; the older sheets were used (§5). `where` = the sheet names. | `Không có file lịch sử; dùng sheet <các sheet> trong workbook làm lịch sử.` |
| `DEV-ON-LEAVE` | INFO | A pool dev is off for every working day. | `<Mã> nghỉ cả sprint; không được giao đơn.` |
| `RULE-DEV-UNAVAILABLE` | WARN | A `Chỉ định` or `Ưu tiên` rule in force names a dev who is not in the pool: `Nhận việc` = `N` or on leave for the whole sprint (D35). `where` = `Luật dòng <n>`. | `Luật dòng <n> (<Loại> <Mã>) không áp dụng: <Mã> không nhận việc hoặc nghỉ cả sprint.` |
| `RULE-NO-CANDIDATE` | WARN | The `Không giao` and `Tối đa đơn` rules left no candidate for an order (§7, A31). | `Luật TM loại hết dev khỏi đơn STT <n>; đơn này được giao như khi không có luật Không giao và Tối đa đơn.` |

## 10 · Output workbook

`output/assignment_<sheet slug>_<YYYYMMDD-HHMMSS>.xlsx`, e.g. `assignment_sprint-10_20261006-143000.xlsx`. Written to
`<name>.tmp`, then renamed (A14). A fresh name each run, so a report left open in Excel never blocks the next one.
The backtest writes its own workbook (§13).

Until the tool can write into the internal system (D19, O8), this report **is** the assignment: whoever has access
enters each `PIC` into the system. The column `Nguồn` still says `Tool đề xuất` for the tool's choices.

**Sheet `Phân công`:** one row per order, in source `STT` order. All original columns of the order row in their
original order (including the original `Người làm`), followed by:

| Column | Content |
|---|---|
| `Độ lớn` | `S`/`M`/`L`/`XL`, with ` (mặc định)` appended when it is the fallback (§6.4). |
| `Giờ ước tính` | 4/16/32/64. |
| `Lý do độ lớn` | The AI's reason; empty for a default. |
| `PIC` | Full name of the PIC. For a pre-assigned order: the original `Người làm`. |
| `Mã PIC` | Code(s) of the PIC; for a pre-assigned order, the codes of the pool devs named (empty if none). |
| `Nguồn` | `Đã giao sẵn` or `Tool đề xuất`. |
| `Lý do` | §8. |
| `Dự phòng 1`, `Dự phòng 2` | Codes of the backups (§7); empty for pre-assigned orders. |

**Sheet `Cảnh báo`:** `Mức` · `Mã` · `Vị trí` · `Nội dung`, sorted WARN before INFO, then by code. A run with no
findings writes a single row `Không có cảnh báo`.

**Sheet `Tải dev`:** one row per pool dev, plus devs removed for leave:

| Column | Content |
|---|---|
| `Mã`, `Tên`, `Level` | From `devs.xlsx`. |
| `Việc dở sprint trước` | Carry-over count (§6.2). |
| `Ngày nghỉ` | Leave days on working days. |
| `Đơn giao sẵn`, `Đơn tool đề xuất`, `Tổng đơn` | Counts in the target sprint. |
| `Tổng giờ ước tính` | Load (§1). |
| `Danh sách đơn` | Titles of the dev's orders with their size, one per line. |
| `App đã làm` | Apps from the history where the dev has rank 0 or 1. |

## 11 · Exit codes and terminal output

| Code | When |
|---|---|
| `0` | The report was written, with or without findings, with or without AI sizes. |
| `2` | Input or usage error. No report is written. The message names the file, sheet, row or column. |
| `130` | Interrupted with Ctrl+C. |

The terminal shows: the rules file (`Luật TM: file luat.md (4 luật, 3 có hiệu lực ngày 06/10/2026)`, or `Luật TM:
không có`); where the history came from (`Lịch sử: file Tech_manager_T2-T10_2026.xlsx (172 đơn gốc)`, the
count being the root orders left after the window of §5.1, or `Lịch sử: sheet Sprint 6, Sprint 7, Sprint 8, Sprint 9
trong workbook (không có file lịch sử)`); the target sprint; how sizing went (`Độ lớn: AI (gemini, 6/6 đơn)`, or the fallback and why);
counts (orders, pre-assigned, proposed, findings by level); one line per proposed order
(`STT 10 · Roblox skin 1.0.4 - Fix luồng/Add Ads/Fix UI [M] → MinhNM (dự phòng: LinhNV, TiếnBV)`); each WARN finding
as `WARN <code>: <message>`; and the report path. The full detail is in the workbook.

## 12 · Acceptance on the sample

Inputs: `input/Maintain_update_Sprint_10_va_9.xlsx`; `devs.xlsx` = the 4 rows of §4. Runs A and B: history = the
12 orders of sheet Sprint 9 as a CSV in the Tech manager format of §5, labelled `Sprint 9 (9/21 - 10/2)` (the
acceptance test builds both files from the sample in `tmp_path` at run time; they are never written to disk
elsewhere). Runs C and D: no history file, so the history is sheets Sprint 6–9 (§5). Run E: history =
`input/Tech_manager_T2-T10_2026.xlsx`. Carry-over comes from sheet Sprint 9 in every run. **`--ai off`**, so every
order is `M` (16h). Runs A–D were first computed with the load cap in hours (16h); with equal sizes that is the same
as the cap in orders (D26), so the tables did not change.

**Derived facts** (history = Sprint 9)

| Dev | Level | Carry-over (Sprint 9) | Apps, rank 0 (latest version) | Apps, rank 1 |
|---|---|---|---|---|
| LinhNV | middle+ | 1 (`qa - need fix`) | PS Remote, AR Dog, metal detector, Santa prank, SpeakerCleaner | — |
| MinhNM | middle | 0 (its 9 `pending` rows do not count, D8) | PS Remote, Speak2 | — |
| AnTD | junior+ | 0 | Game Emulator | AR Dog |
| TiếnBV | junior | 2 (`need to be clean`, `internal - cant fix`) | Game mode 2 | — |

The most recent PS Remote order in Sprint 9 is an RnD research order naming nobody from the pool, so the latest
version is `1.1.1` (LinhNV, MinhNM), §6.1.

**Run A: the file as exported.** Five orders are pre-assigned (Phone Cleaner: LinhNV + TiếnBV; PS Remote: MinhNM;
Auto click: AnTD; spin wheel 2: LinhNV; Game Emulator: AnTD), giving loads LinhNV 32h, AnTD 32h, MinhNM 16h,
TiếnBV 16h. One order is empty:

| STT | Order | needs_senior | PIC | Backups | Why |
|---|---|---|---|---|---|
| 10 | Roblox skin 1.0.4 | yes (new app) | **MinhNM** | LinhNV, TiếnBV | Nobody knows the app; LinhNV and MinhNM are ≥ middle; MinhNM has the lower load (16h vs 32h). |

Findings: none. The sheet `Cảnh báo` holds the single row `Không có cảnh báo`.

**Run B: backtest.** The same inputs with `Người làm` cleared on the 6 Sprint 10 orders, compared with what the TM
actually did:

| Step | Order (priority) | Familiarity | Loads before, h (Linh/Minh/An/Tiến) | PIC | TM's choice |
|---|---|---|---|---|---|
| 1 | PS Remote 1.1.2 (urgent) | LinhNV, MinhNM rank 0 | 0/0/0/0 | MinhNM: carry-over 0 vs 1 | MinhNM ✓ |
| 2 | Game Emulator (high) | AnTD rank 0 | 0/16/0/0 | AnTD: familiarity first | AnTD ✓ |
| 3 | Auto click 1.1.1 | new app | 0/16/16/0 | LinhNV: ≥ middle, lower load | AnTD ✗ |
| 4 | Roblox skin 1.0.4 | new app | 16/16/16/0 | MinhNM: carry-over 0 vs 1 | — (empty) |
| 5 | Phone Cleaner 1.0.2 | new app | 16/32/16/0 | LinhNV: MinhNM capped (2 orders > 0 + 1) | LinhNV (+ TiếnBV) ✓ |
| 6 | spin wheel 2 1.0.2 | new app | 32/32/16/0 | TiếnBV: only AnTD and TiếnBV under the cap | LinhNV ✗ |

Final loads 32/32/16/16 h. The rule matches the TM on 3 of the 5 orders the TM assigned. The two misses are apps
absent from Sprint 9; run D shows them becoming rank 0 once Sprint 6–8 are in the history. The test asserts this
table as it is.

**Runs C and D: history = sheets Sprint 6–9.** The sample gained sheets Sprint 6, 7 and 8 on 2026-10-06 (34 history
orders in all). Same `devs.xlsx`, same carry-over, `--ai off`. Familiarity changes for three of the six apps; Phone
Cleaner stays a new app:

| App | History = Sprint 9 | History = Sprint 6–9 |
|---|---|---|
| Auto click | new app | AnTD rank 0 (Sprint 8) |
| Roblox skin | new app | AnTD rank 0 (Sprint 8) |
| spin wheel 2 | new app | LinhNV rank 0 (Sprint 8) |

**Run C: the file as exported.** Loads after the pre-assigned orders as in run A (LinhNV 32h, MinhNM 16h, AnTD 32h,
TiếnBV 16h). Roblox skin → **AnTD** (backups MinhNM, TiếnBV): the only dev on its latest version, and 2 orders are
within the cap (1 + 1). Final loads 32/16/48/16 h. Findings: the single INFO `HISTORY-FROM-WORKBOOK` naming the four sheets.

**Run D: backtest** (`Người làm` cleared, as in run B):

| Step | Order (priority) | Familiarity | Loads before, h (Linh/Minh/An/Tiến) | PIC | TM's choice |
|---|---|---|---|---|---|
| 1 | PS Remote 1.1.2 (urgent) | LinhNV, MinhNM rank 0 | 0/0/0/0 | MinhNM: carry-over 0 vs 1 | MinhNM ✓ |
| 2 | Game Emulator (high) | AnTD rank 0 | 0/16/0/0 | AnTD: familiarity first | AnTD ✓ |
| 3 | Auto click 1.1.1 | AnTD rank 0 | 0/16/16/0 | AnTD: familiarity first (1 order ≤ 0 + 1) | AnTD ✓ |
| 4 | Roblox skin 1.0.4 | AnTD rank 0 | 0/16/32/0 | LinhNV: AnTD capped (2 orders > 0 + 1); carry-over 1 vs 2 | — (empty) |
| 5 | Phone Cleaner 1.0.2 | new app | 16/16/32/0 | MinhNM: ≥ middle, same load, carry-over 0 vs 1 | LinhNV (+ TiếnBV) ✗ |
| 6 | spin wheel 2 1.0.2 | LinhNV rank 0 | 16/32/32/0 | LinhNV: familiarity first (1 order ≤ 0 + 1) | LinhNV ✓ |

Final loads 32/32/32/0 h. The rule matches the TM on 4 of 5 (run B: 3 of 5).

**Run E: history = the Tech manager export, file as exported.** 178 root orders; the window of §5.1 drops the six of
Sprint 10, leaving 172. All six Sprint 10 apps now have history (Phone Cleaner through its MVP order). Roblox skin →
**AnTD** (backups MinhNM, TiếnBV), reason `Làm version gần nhất của Roblox skin (Sprint 8 (9/4 - 9/18): 1.0.1 - Add
ads) · Tải sprint này: 32h (2 đơn) · Việc dở Sprint 9: 0`. Final loads 32/16/48/16 h, as run C. Findings: none.

**Not asserted:** a run with AI sizes. Its sizes vary between runs (§6.4); the opt-in smoke test only checks that a
real call returns a valid size for every order.

**Sensitivity to AI sizes (scratch analysis, 2026-10-06, not asserted).** Every one of the 4^6 = 4,096 size
combinations of the six orders, run through §7:

| Run | Load cap in hours (before D26) | Load cap in orders (D26, today) |
|---|---|---|
| A (Sprint 9), Roblox skin → | MinhNM 68%, LinhNV 15%, TiếnBV 12%, AnTD 5% | MinhNM 81%, LinhNV 19% |
| C (Sprint 6–9), Roblox skin → | MinhNM 42%, AnTD 30%, TiếnBV 28% | AnTD 100% |
| B (Sprint 9), matches with the TM | 4/5: 16%, 3/5: 65%, 2/5: 19% | 3/5: 62%, 2/5: 38% |
| D (Sprint 6–9), matches with the TM | 5/5: 10%, 4/5: 41%, 3/5: 38%, 2/5: 11% | 4/5: 100% |

More history improves the matches, but with the cap in hours the proposal still depended on the sizes: a dev whose
pre-assigned orders the AI sized L + XL was capped out of an app they built. This table is why the cap now counts
orders (D26); with every order `M` the two caps agree, so runs A–D did not change.

**First real run with Gemini (2026-10-06, for the record, not asserted).** Sizes: Phone Cleaner M, PS Remote XL,
Roblox skin XL, Auto click M, spin wheel 2 L, Game Emulator XL. Loads after the pre-assigned orders: LinhNV 48h,
MinhNM 64h, AnTD 80h, TiếnBV 16h. The 16h cap left only TiếnBV, so Roblox skin went to TiếnBV (junior) although
the app is new; LinhNV and MinhNM appear in the reason as "là middle trở lên nhưng đang có …h (cân tải)" (§8 part 7).
Whether the cap should yield to seniority on large new-app orders was `confirm.md` O5, closed by D26: with the cap
in orders, two pre-assigned orders each for LinhNV and AnTD and one each for MinhNM and TiếnBV leave MinhNM eligible. A second run on the same
input sized Phone Cleaner `XL` instead of `M`, and Roblox skin went to MinhNM: sizes, and so proposals, vary between
runs (`confirm.md` O6).

**Real runs with Gemini on history Sprint 6–9 (2026-10-06, for the record, not asserted).** Four runs of the
default command. Three sized almost every order L or XL (the history examples now include 40–97h orders), giving
loads after the pre-assigned orders of 128/64/96/64, 96/64/96/64 and 128/64/96/64 h (Linh/Minh/An/Tiến); each time
AnTD, the only dev on Roblox skin's latest version, was capped (96 > 64 + 16) and Roblox skin went to MinhNM, with
AnTD as first backup. One run hit the 180s timeout, so every order was `M` and Roblox skin went to AnTD as in run C. More
history did not make the AI-sized proposal stable; the cap in hours was why (`confirm.md` O7, now D26).

**Real run with Gemini after D26 (2026-10-07, history = the Tech manager export, for the record, not asserted).**
Sizes: Phone Cleaner XL, PS Remote XL, Roblox skin L, Auto click M, spin wheel 2 L, Game Emulator XL (no calibration
examples: the export has no hours, D25). Loads after the pre-assigned orders: LinhNV 96h (2 orders), MinhNM 64h (1),
AnTD 80h (2), TiếnBV 64h (1). Roblox skin → AnTD, as with `--ai off` (run E): 2 orders are within the cap of 1 + 1
whatever the sizes.

## 13 · Backtest

`assigntool --backtest` (D22, A29) answers "would the tool have assigned what the TM assigned?" on every Maintain
sprint of the history export. It needs the history export (§5) and `devs.xlsx` only.

**Replay.** For each Maintain sprint (§5.2), oldest first:

1. The sprint's root orders that name at least one active pool dev are taken. Those also listed in an earlier
   Maintain sprint are **carried**: kept with the TM's `Người làm`, like pre-assigned orders (D10), and not compared.
   The others are **compared**: their `Người làm` is cleared and the tool assigns them. Orders naming nobody from the
   pool (outside people, or empty) are left out: there is no TM choice to compare with.
2. Compared orders are replayed **by filing day** (D2: the tool runs whenever BA files orders): those filed before the
   sprint starts are assigned together on its first day, and each later filing day is one more run that sees the
   earlier choices as pre-assigned.
3. Each run is the rule of §7 with: the history window of §5.1 on that day; the TM rules in force on that day
   (§14.3, D34); every order `M` (the export has no `Mô tả`, so the AI has nothing to read); carry-over 0 (the
   export's statuses are today's, not those at the start of a past sprint); leave from `devs.xlsx`; the pool minus
   devs on leave for the whole sprint. Carried orders are pre-assigned, so rules never move them.
4. An order **matches** when the tool's PIC is one of the pool devs the TM named (in the sample, the TM named 2 pool
   devs on 13 of the 92 compared orders; 10 of those match).

A miss is not necessarily wrong: the rule balances load on purpose, and the backtest knows neither sizes nor
carry-over.
No threshold is set (D22).

**Output.** `output/backtest_<YYYYMMDD-HHMMSS>.xlsx`, written through `.tmp`:

| Sheet | Columns |
|---|---|
| `Theo sprint` | `Sprint` · `Bắt đầu` · `Kết thúc` · `Đơn so sánh` · `Khớp` · `Tỉ lệ khớp` · `Đơn mang sang` · `Đơn theo luật TM`; a last row `Tổng`. |
| `Theo đơn` | `Sprint` · `Ngày lên đơn` · `App` · `Đơn` · `Ưu tiên` · `TM giao` · `Tool giao` · `Khớp` (`✓`/`✗`) · `Dự phòng 1` · `Dự phòng 2` · `Lý do của tool` · `Luật TM`; by sprint, then filing day. |

`Luật TM` lists the lines of the rules that shaped the tool's choice (`dòng 3, 5`): the pin or preference of §8 part
0, and the rules of parts 8 and 9. `Đơn theo luật TM` counts the compared orders with a non-empty `Luật TM`. A rule
derived from the same history raises the match rate by construction: with rules, the rate measures the TM's rules
and the tool's rule together.

The terminal prints the rules line of §11 (`Luật TM: file luat.md (4 luật, áp theo ngày giao lại)`), one line per sprint (`Sprint 9 (9/21 - 10/2): khớp 8/11 đơn (73%)`), the total and the report
path. Rates are rounded half up. A history file with no Maintain sprint is an input error (exit 2).

**Run F: the sample** (`input/Tech_manager_T2-T10_2026.xlsx`, the 4 devs of §4 with no leave):

| Sprint | Compared | Matched | Carried |
|---|---|---|---|
| Sprint 14 (1/26 - 2/12) | 1 | 0 | 0 |
| Sprint 15 (2/24 - 3/13) | 5 | 2 | 0 |
| Sprint 16 (3/16 - 3/31) | 4 | 1 | 2 |
| Sprint 17 (4/2 - 4/14) | 3 | 0 | 3 |
| Sprint 18 (4/17 - 4/29) | 3 | 0 | 3 |
| Sprint 19 (5/6 - 5/20) | 3 | 0 | 3 |
| Sprint 1 (5/22 - 6/5) | 7 | 3 | 0 |
| Sprint 2 (6/5 - 6/19) | 8 | 5 | 0 |
| Sprint 3 (6/22 - 7/3) | 6 | 2 | 0 |
| Sprint 4 (7/7 - 7/17) | 11 | 7 | 0 |
| Sprint 5 (7/28 - 8/10) | 6 | 4 | 0 |
| Sprint 6 (8/10 - 8/14) | 3 | 2 | 0 |
| Sprint 7 (8/17 - 8/28) | 7 | 3 | 0 |
| Sprint 8 (9/4 - 9/18) | 9 | 2 | 0 |
| Sprint 9 (9/21 - 10/2) | 11 | 8 | 0 |
| Sprint 10 (10/6 - 10/17) | 5 | 4 | 0 |
| **Total** | **92** | **43 (47%)** | 11 |

Run F has no rules file; `Đơn theo luật TM` is 0 on every row.

Reading it:

- **History length matters most.** Sprints 14–19 (January–May, little history) match 3 of 19 orders; Sprints 1–10
  match 40 of 73 (55%), and Sprint 9 matches 8/11.
- **Sprint 10:** the one miss is PS Remote (urgent): LinhNV and MinhNM both built version 1.1.1, and with carry-over 0
  the level decides for LinhNV. In a normal run (run B) MinhNM wins on carry-over (LinhNV has a `qa - need fix` row in
  Sprint 9), which is what the TM did.
- **Sprint 8 (2/9):** the TM gave LinhNV 6 of the 9 orders. The cap (at most one order more than the least-loaded dev)
  does not allow that, so 5 of the 7 misses are orders the TM gave LinhNV; the tool's reasons say
  `LinhNV quen app hơn nhưng đang có 3 đơn (cân tải)`. Whether the TM's concentration or the cap is right is the
  TM's call (D22).

## 14 · Input: TM rules

The TM steers the choice without editing code: a rules file pins a dev to an app, keeps a dev off an app or off every
order, caps a dev's orders, or prefers a dev for an app (D28, D30). The rules are a fixed table read without AI, so
every choice stays repeatable, explainable in `Lý do` (§8) and measurable by the backtest (§13). The AI never sees
the rules (LLM.md §12).

### 14.1 File

A Markdown file (`.md`), UTF-8 with or without BOM, found as the only `*.md` in `--input` or given with `--rules`
(D29); several `.md` files are an input error, none means no rules. Text outside the tables is the TM's free notes
and is ignored. Example:

```markdown
# Luật giao việc

| Loại       | Dev    | App       | Số đơn | Từ ngày    | Đến ngày   | Ghi chú                 |
|------------|--------|-----------|--------|------------|------------|-------------------------|
| Chỉ định   | LinhNV | AR Dog    |        |            |            | Linh giữ AR Dog         |
| Không giao | MinhNM |           |        | 06/10/2026 | 17/10/2026 | Minh làm MVP sprint này |
| Tối đa đơn | AnTD   |           | 1      | 06/10/2026 | 17/10/2026 |                         |
| Ưu tiên    | TiếnBV | PS Remote |        |            |            | Cho Tiến học PS Remote  |
```

**Reading rules**

1. A table is a run of consecutive lines starting with `|`, whose second line is a delimiter row (`|---|:--:|`). A
   rules table is one whose header has `Loại` and `Dev`; every rules table in the file is read (A33), other tables are
   ignored. Lines inside a fenced code block (```` ``` ```` or `~~~`) are text, not a table, as Markdown renders
   them. A file with no rules table is an input error.
2. Columns are found by header name (§3 rule 2), never by position; unknown columns are ignored. Cells are split on
   `|` (an escaped `\|` stays in the cell), NFC-normalised and trimmed; surrounding `` ` `` and `*` are removed, so
   `` `AR Dog` `` and `**LinhNV**` read as `AR Dog` and `LinhNV`. A row whose cells are all empty is skipped.
3. A rule is identified by its **line number** in the file, quoted in messages and reasons.

| Header | Use |
|---|---|
| `Loại` | `Chỉ định`, `Không giao`, `Tối đa đơn` or `Ưu tiên` (NFC, case-insensitive). |
| `Dev` | A `Mã` of `devs.xlsx` (§4), compared like names (A10). One dev per row. |
| `App` | One app, matched like `App Name` (A10). Required for `Chỉ định` and `Ưu tiên`; empty on `Không giao` means every app; not used by `Tối đa đơn`. |
| `Số đơn` | A whole number ≥ 1. Required for `Tối đa đơn`; not used by the others. |
| `Từ ngày`, `Đến ngày` | `DD/MM/YYYY` or `YYYY-MM-DD`; empty means no limit on that side (D33). |
| `Ghi chú` | Free text, quoted in the reason (§8 part 0). |

### 14.2 Input errors (D35, A33)

A broken rule stops the run with exit 2 and a message naming the file, the line and, when known, the column. The tool
never guesses which of two rules the TM meant.

| Case | Message (Vietnamese) |
|---|---|
| No rules table | `File '<file>' không có bảng luật (bảng có cột Loại và Dev).` |
| Unknown `Loại` | `File '<file>', dòng <n>, cột 'Loại': '<giá trị>' không hợp lệ; dùng Chỉ định, Không giao, Tối đa đơn hoặc Ưu tiên.` |
| Empty `Dev` | `File '<file>', dòng <n>: thiếu Dev.` |
| A required cell empty | `File '<file>', dòng <n>: luật <Loại> cần cột <cột>.` |
| A cell the kind does not use | `File '<file>', dòng <n>: luật <Loại> không dùng cột <cột>.` |
| `Số đơn` not a whole number ≥ 1 | `File '<file>', dòng <n>, cột 'Số đơn' phải là số nguyên từ 1 trở lên.` |
| Unreadable date | `File '<file>', dòng <n>, cột '<cột>': không đọc được ngày '<giá trị>'` |
| `Từ ngày` after `Đến ngày` | `File '<file>', dòng <n>: Từ ngày sau Đến ngày.` |
| `Dev` not a `Mã` of `devs.xlsx` | `File '<file>', dòng <n>: không có dev mã '<Dev>' trong file dev.` |
| Two `Chỉ định` for one app, different devs | `File '<file>', dòng <a> và <b>: hai luật Chỉ định khác dev cho app '<App>'.` |
| `Chỉ định` or `Ưu tiên`, and `Không giao` (same app or every app), same dev | `File '<file>', dòng <a> và <b>: luật <Loại> và Không giao mâu thuẫn cho <Mã>.` |
| Two `Tối đa đơn` for one dev, different numbers | `File '<file>', dòng <a> và <b>: hai luật Tối đa đơn khác số cho <Mã>.` |

Two rules conflict only when their date ranges overlap. Conflicts and unknown devs are checked over the whole file,
not only the rules in force, so a normal run and the backtest accept or reject the same file.

A valid rule that cannot act is not an error: a `Chỉ định` or `Ưu tiên` for a dev outside the pool is a
`RULE-DEV-UNAVAILABLE` finding (§9); a rule whose app has no order in the sprint is not reported (D35).

### 14.3 Rules in force

A rule is in force on a day when `Từ ngày` ≤ day ≤ `Đến ngày`. The day is:

- **normal run:** today, but not earlier than the target sprint's first day when the sheet has dates (A34): a TM who
  runs the tool on the Friday before Sprint 10 gets the rules dated for Sprint 10;
- **backtest:** the day each batch is replayed (§13 step 2), so a rule dated for one sprint does not touch another
  (D34).

How each kind acts is in §7; what it writes in `Lý do` is in §8. Rules never touch pre-assigned orders (D10), never
add a dev outside the pool (D7), and leave the cap's "+ 1 order" (D26) as it is.
