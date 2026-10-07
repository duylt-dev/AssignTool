# Assignment spec: `assigntool`

What the tool reads, how it sizes orders, how it picks a PIC for each order, and what it writes.
[`LLM.md`](../LLM.md) says where each part lives in code; [`confirm.md`](../confirm.md) holds the decisions cited
here as `Dn` (user-locked), `An` (defaults) and `On` (open).

**Status:** approved 2026-10-06 and implemented. Every number in §12 was computed by hand from the sample workbook
and is asserted by `tests/test_real_input.py` and `tests/test_pipeline.py`.

User-facing text (column headers, finding messages, reasons, terminal lines) is Vietnamese (D12). It is quoted here
exactly as the tool must print it.

| § | Contents |
|---|---|
| 1 | Terms |
| 2 | Command line |
| 3 | Input: sprint workbook |
| 4 | Input: dev workbook |
| 5 | Input: history CSV |
| 6 | Derived facts: familiarity, carry-over, leave, size |
| 7 | Choosing the PIC |
| 8 | Reason text |
| 9 | Findings |
| 10 | Output workbook |
| 11 | Exit codes and terminal output |
| 12 | Acceptance on the sample |

---

## 1 · Terms

| Term | Meaning |
|---|---|
| Order (*đơn*) | A row whose `Loại` is `Task`: one version of one app, e.g. `1.0.2 - Add ads/Add SDK` for Phone Cleaner. The unit of assignment (D5). |
| PIC | The one dev who owns an order and later splits it into subtasks (D5). |
| Pool | Devs in `devs.xlsx` with `Nhận việc` = `Y`, minus those on leave for the whole sprint (A12). Today: LinhNV, MinhNM, AnTD, TiếnBV (D7). Everyone else is ignored everywhere, silently (D14). |
| Target sprint | The sheet the tool assigns: the highest `Sprint N` (A3). |
| Previous sprint | Sheet `Sprint N-1` of the same workbook. Source of carry-over only (A9). |
| Size | The AI's class for an order, `S`/`M`/`L`/`XL`, worth 4/16/32/64 hours (§6.4, A7). |
| Load | Sum of the sizes, in hours, of the orders a pool dev holds in the target sprint, pre-assigned or proposed. |
| Carry-over | Number of rows in the previous sprint assigned to the dev whose status is busy (D8). |
| Familiarity | How well a dev knows the order's app, from the history CSV (§6.1). |

## 2 · Command line

```
assigntool [--input DIR] [--sprint FILE] [--devs FILE] [--history FILE] [--sheet NAME] [--out DIR]
           [--ai gemini|agy|off] [--ai-model NAME] [--ai-timeout SECONDS] [-v]
```

| Option | Default | Meaning |
|---|---|---|
| `--input DIR` | `input/` | Where inputs are discovered. |
| `--sprint FILE` | the only `*.xlsx` in `--input` other than `devs.xlsx` | Sprint workbook (§3). |
| `--devs FILE` | `<input>/devs.xlsx` | Dev workbook (§4). |
| `--history FILE` | the only `*.csv` in `--input`; none → the workbook's older sprint sheets (§5) | History CSV (§5). |
| `--sheet NAME` | highest `Sprint N` | Target sprint sheet. The previous sprint is then `Sprint N-1`. |
| `--out DIR` | `output/` | Where the report is written. Created if missing. |
| `--ai` | `gemini` | AI tool used for sizing (§6.4, D16, A17). `agy` is for the dev machine; `off` sizes every order `M`. |
| `--ai-model` | the AI tool's own default | Model name passed through to the AI tool. |
| `--ai-timeout` | `180` | Seconds before the AI call is killed and sizes fall back to `M`. |
| `-v` | off | Show tracebacks for input errors and the AI tool's raw output. |

Discovery never guesses (A2): zero or several candidates for a file is an input error that names the candidates and
the flag to use. Files whose names start with `~$` (Excel lock files) and `.` are ignored.

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
| `Trạng thái` | ✓ | Previous sprint only: busy statuses (D8). |
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

## 5 · Input: history CSV

Exported by the user from the internal system (D6). It uses **the sprint export's own column names plus a `Sprint`
column** (A20), one row per task. Only rows with `Loại` = `Task` are used, so a full dump including subtasks works.

```csv
Sprint,STT,Task,Loại,App Name,Người làm,Ước lượng (h),Ngày tạo,Mô tả
Sprint 9,1,1.1.1 - Fix ads/FIx luồng/ fix policy,Task,PS Remote,"Ngọc Văn Linh, Nguyễn Nhật Minh",68,2026-09-21,
Sprint 9,165,1.0.3. Fix crash,Task,Game Emulator,Trần Đức An,17,2026-09-22,
```

| Header | Required | Use |
|---|---|---|
| `Sprint` | ✓ | Quoted in the reason text. |
| `Loại` | ✓ | Only `Task` rows are used. |
| `App Name` | ✓ | App (A10 matching). Rows with an empty app are skipped. |
| `Người làm` | ✓ | Comma-separated full names; names outside the pool are ignored (D14). |
| `Ngày tạo` | ✓ | Recency: decides the "latest version" of an app. |
| `Task` | — | Quoted in the reason text; sent to the AI as an example (§6.4). |
| `Ước lượng (h)` | — | Hours recorded for the order; sent to the AI as an example (A19). |
| `Mô tả` | — | Not used today. |

Encoding UTF-8 with or without BOM; delimiter `,` or `;`, detected from the header line; dates `YYYY-MM-DD` or
`DD/MM/YYYY` (A15). Header names are matched like §3 rule 2. A missing required header or an unreadable date is an
input error naming the line. Extra columns are ignored.

**No CSV (A8).** When `--history` is not given and `--input` holds no `*.csv`, the history is every sprint sheet of
the workbook numbered below the target (the sample: `Sprint 6` to `Sprint 9`, 34 orders), read with the same rules: `Task` rows with an app,
a name and a `Ngày tạo`, `Ước lượng (h)` as hours. Required headers on those sheets: `Loại`, `App Name.`,
`Người làm`, `Ngày tạo`. The run then reports `HISTORY-FROM-WORKBOOK`, or `HISTORY-MISSING` when there is no older
sheet either. A CSV, when present, is the only history: the two are never combined, so nothing is counted twice.

## 6 · Derived facts

§6.1–§6.3, §7 and the prompt and parsing of §6.4 are pure computation over values from §3–§5 (LLM.md §2). Only the
call to the AI tool itself is I/O.

### 6.1 Familiarity of a dev with an app

For each app, consider the history orders of that app that name **at least one pool dev**. The most recent of them
by `Ngày tạo` is the app's **latest version**. Orders naming only people outside the pool are ignored here: an RnD
research order is not a version a pool dev worked on.

| Rank | Meaning | Reason text |
|---|---|---|
| 0 | The dev is named on the app's latest version. | `Làm version gần nhất của <app> (<Sprint>: <Task>)` |
| 1 | The dev is named on an older version only. | `Từng làm <app> (<k> version)` |
| 2 | Never named on this app. | `Chưa làm <app>` |

An app with no history order naming a pool dev is a **new app**: every dev has rank 2.

### 6.2 Carry-over

For each pool dev: the number of previous-sprint rows (orders **and** subtasks) that name the dev in `Người làm` and
whose `Trạng thái` is one of the busy statuses of D8. Statuses are compared after NFC, trimming and casefolding.

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
   date, `STT`.
3. For each order:
   - `needs_senior` is true when the priority is `urgent` or `high`, or the app is new (§6.1).
   - **Load cap:** only devs whose load ≤ (lowest load in the pool) + 16h can be chosen. This keeps a dev who knows
     many apps from taking every order.
   - Among them, the PIC is the dev with the **smallest key**, compared left to right:

     | # | Key part | Smaller is better |
     |---|---|---|
     | 1 | familiarity rank (§6.1) | 0 = latest version |
     | 2 | seniority gap | 0 when `needs_senior` is false or level ≥ `middle`; else 1 |
     | 3 | load (hours) | less work in this sprint |
     | 4 | carry-over (§6.2) | fewer busy rows left from the previous sprint |
     | 5 | leave days (§6.3) | fewer days off |
     | 6 | level, descending | higher level first |
     | 7 | `Mã` | alphabetical, so the result is deterministic |

   - **Backups:** the next two devs by the same key over the **whole** pool, ignoring the load cap. A backup
     excluded by the cap is still useful to the TM, who may prefer familiarity over balance.
   - The PIC's load is increased by the order's size before the next order.

**Why a key and not a weighted score.** Every part of the key can be stated as a sentence in the reason (§8), and the
TM can check it by eye. Weights would need tuning against data we do not have, and a score of 0.73 explains nothing.

**Why familiarity comes before seniority, even on urgent orders.** The person who built the last version is the
fastest on the next one. The sample agrees: the TM gave a `high` Game Emulator order to AnTD (junior+), the only dev
who had worked on that app.

**Why the AI sizes but does not choose.** The choice must be explainable and repeatable; a size is one input among
seven, and a wrong size moves load by a few hours, not the whole decision.

## 8 · Reason text

The `Lý do` cell joins these parts with ` · `, in this order, leaving out parts that do not apply:

1. Familiarity text of §6.1.
2. `Đơn <priority> → ưu tiên middle trở lên` when `needs_senior` is caused by priority; `App chưa ai trong team làm →
   ưu tiên middle trở lên` when it is caused by a new app. Only when the PIC is middle or above.
3. `Tải sprint này: <h>h (<n> đơn)` (load before this order).
4. `Việc dở <previous sprint>: <n>`.
5. `Nghỉ <n> ngày` when n > 0.
6. For each dev with a better familiarity rank who was excluded by the load cap:
   `<Mã> quen app hơn nhưng đang có <h>h (cân tải)`.
7. For each dev with the same rank but a better seniority gap (middle or above when `needs_senior`) who was excluded
   by the load cap: `<Mã> là middle trở lên nhưng đang có <h>h (cân tải)`. Without it, a junior chosen for a new-app
   order looks like a mistake (first real run, §12 note).

Example: `Làm version gần nhất của PS Remote (Sprint 9: 1.1.1 - Fix ads/FIx luồng/ fix policy) · Đơn urgent → ưu tiên
middle trở lên · Tải sprint này: 0h (0 đơn) · Việc dở Sprint 9: 0`.

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
| `HISTORY-MISSING` | WARN | No CSV and no sprint sheet older than the target (§5). | `Không có file .csv lịch sử và workbook không có sheet sprint cũ; coi như chưa ai làm app nào.` |
| `HISTORY-FROM-WORKBOOK` | INFO | No CSV; the older sheets were used (§5). `where` = the sheet names. | `Không có file .csv lịch sử; dùng sheet <các sheet> trong workbook làm lịch sử.` |
| `DEV-ON-LEAVE` | INFO | A pool dev is off for every working day. | `<Mã> nghỉ cả sprint; không được giao đơn.` |

## 10 · Output workbook

`output/assignment_<sheet slug>_<YYYYMMDD-HHMMSS>.xlsx`, e.g. `assignment_sprint-10_20261006-143000.xlsx`. Written to
`<name>.tmp`, then renamed (A14). A fresh name each run, so a report left open in Excel never blocks the next one.

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

The terminal shows: where the history came from (`Lịch sử: file history.csv`, or `Lịch sử: sheet Sprint 6, Sprint 7, Sprint 8,
Sprint 9 trong workbook (không có file .csv)`); the target sprint; how sizing went (`Độ lớn: AI (gemini, 6/6 đơn)`, or the fallback and why);
counts (orders, pre-assigned, proposed, findings by level); one line per proposed order
(`STT 10 · Roblox skin 1.0.4 - Fix luồng/Add Ads/Fix UI [M] → MinhNM (dự phòng: LinhNV, TiếnBV)`); each WARN finding
as `WARN <code>: <message>`; and the report path. The full detail is in the workbook.

## 12 · Acceptance on the sample

Inputs: `input/Maintain_update_Sprint_10_va_9.xlsx`; `devs.xlsx` = the 4 rows of §4. Runs A and B: history CSV = the
12 orders of sheet Sprint 9 in the §5 format (the acceptance test builds both files from the sample in `tmp_path` at run time; they
are never written to disk elsewhere). Runs C and D: no CSV, so the history is sheets Sprint 6–9 (§5). Carry-over comes from sheet
Sprint 9 in every run. **`--ai off`**, so every order is `M` (16h); with equal sizes
the load cap of 16h equals "one order".

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
| 5 | Phone Cleaner 1.0.2 | new app | 16/32/16/0 | LinhNV: MinhNM capped (32 > 0 + 16) | LinhNV (+ TiếnBV) ✓ |
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
TiếnBV 16h). Roblox skin → **AnTD** (backups MinhNM, TiếnBV): the only dev on its latest version, and 32h is within
the cap (16 + 16). Final loads 32/16/48/16 h. Findings: the single INFO `HISTORY-FROM-WORKBOOK` naming the four sheets.

**Run D: backtest** (`Người làm` cleared, as in run B):

| Step | Order (priority) | Familiarity | Loads before, h (Linh/Minh/An/Tiến) | PIC | TM's choice |
|---|---|---|---|---|---|
| 1 | PS Remote 1.1.2 (urgent) | LinhNV, MinhNM rank 0 | 0/0/0/0 | MinhNM: carry-over 0 vs 1 | MinhNM ✓ |
| 2 | Game Emulator (high) | AnTD rank 0 | 0/16/0/0 | AnTD: familiarity first | AnTD ✓ |
| 3 | Auto click 1.1.1 | AnTD rank 0 | 0/16/16/0 | AnTD: familiarity first (16 ≤ 0 + 16) | AnTD ✓ |
| 4 | Roblox skin 1.0.4 | AnTD rank 0 | 0/16/32/0 | LinhNV: AnTD capped (32 > 0 + 16); carry-over 1 vs 2 | — (empty) |
| 5 | Phone Cleaner 1.0.2 | new app | 16/16/32/0 | MinhNM: ≥ middle, same load, carry-over 0 vs 1 | LinhNV (+ TiếnBV) ✗ |
| 6 | spin wheel 2 1.0.2 | LinhNV rank 0 | 16/32/32/0 | LinhNV: familiarity first (16 ≤ 0 + 16) | LinhNV ✓ |

Final loads 32/32/32/0 h. The rule matches the TM on 4 of 5 (run B: 3 of 5).

**Not asserted:** a run with AI sizes. Its sizes vary between runs (§6.4); the opt-in smoke test only checks that a
real call returns a valid size for every order.

**Sensitivity to AI sizes (scratch analysis, 2026-10-06, not asserted).** Every one of the 4^6 = 4,096 size
combinations of the six orders, run through §7:

| Run | Load cap in hours (today) | Load cap in orders (`confirm.md` O7) |
|---|---|---|
| A (Sprint 9), Roblox skin → | MinhNM 68%, LinhNV 15%, TiếnBV 12%, AnTD 5% | MinhNM 81%, LinhNV 19% |
| C (Sprint 6–9), Roblox skin → | MinhNM 42%, AnTD 30%, TiếnBV 28% | AnTD 100% |
| B (Sprint 9), matches with the TM | 4/5: 16%, 3/5: 65%, 2/5: 19% | 3/5: 62%, 2/5: 38% |
| D (Sprint 6–9), matches with the TM | 5/5: 10%, 4/5: 41%, 3/5: 38%, 2/5: 11% | 4/5: 100% |

More history improves the matches, but with the cap in hours the proposal still depends on the sizes: a dev whose
pre-assigned orders the AI sizes L + XL is capped out of an app they built. Counted in orders (load ≤ lowest + one
order) the cap gives the same result as today when every order is `M`, so runs A–D are unchanged.

**First real run with Gemini (2026-10-06, for the record, not asserted).** Sizes: Phone Cleaner M, PS Remote XL,
Roblox skin XL, Auto click M, spin wheel 2 L, Game Emulator XL. Loads after the pre-assigned orders: LinhNV 48h,
MinhNM 64h, AnTD 80h, TiếnBV 16h. The 16h cap left only TiếnBV, so Roblox skin went to TiếnBV (junior) although
the app is new; LinhNV and MinhNM appear in the reason as "là middle trở lên nhưng đang có …h (cân tải)" (§8 part 7).
Whether the cap should yield to seniority on large new-app orders is `confirm.md` O5. A second run on the same
input sized Phone Cleaner `XL` instead of `M`, and Roblox skin went to MinhNM: sizes, and so proposals, vary between
runs (`confirm.md` O6).

**Real runs with Gemini on history Sprint 6–9 (2026-10-06, for the record, not asserted).** Four runs of the
default command. Three sized almost every order L or XL (the history examples now include 40–97h orders), giving
loads after the pre-assigned orders of 128/64/96/64, 96/64/96/64 and 128/64/96/64 h (Linh/Minh/An/Tiến); each time
AnTD, the only dev on Roblox skin's latest version, was capped (96 > 64 + 16) and Roblox skin went to MinhNM, with
AnTD as first backup. One run hit the 180s timeout, so every order was `M` and Roblox skin went to AnTD as in run C. More
history did not make the AI-sized proposal stable; the cap in hours is why (`confirm.md` O7).
