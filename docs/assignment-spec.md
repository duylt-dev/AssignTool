# Assignment spec: the assignment core of `scrumbot`

How the bot sizes orders, picks a PIC for each empty order, and what it writes. Reading the internal system's API,
the review of an order file, the risk register, the AI memory and `output.md` are in [`bot-spec.md`](bot-spec.md); this
file is the reference for the rule itself (§6–§8), the findings (§9), the exit codes (§11) and the TM rules (§14).
[`LLM.md`](../LLM.md) says where each part lives in code; [`confirm.md`](../confirm.md) holds the decisions cited
here as `Dn` (user-locked), `An` (defaults) and `On` (open).

**Status:** approved 2026-10-06 and implemented; the load cap in orders (D26) and the TM rules file (D28–D35, §14)
added 2026-10-07; renamed `scrumbot` on 2026-10-13 (D46, D57). The same day the export-file source, the acceptance
run on the sample and the backtest were removed (D59): the orders come from the API (bot spec §2.5), and §3, §5, §12
and §13 keep their numbers so that citations stay valid. On 2026-10-14 `run` and its workbook were removed (D62);
§10 keeps its number.

User-facing text (column headers, finding messages, reasons, terminal lines) is Vietnamese (D12). It is quoted here
exactly as the tool must print it.

| § | Contents |
|---|---|
| 1 | Terms |
| 2 | Command line and input files |
| 3 | Input: the target sprint |
| 4 | Input: dev workbook |
| 5 | History |
| 6 | Derived facts: familiarity, carry-over, leave, size |
| 7 | Choosing the PIC |
| 8 | Reason text |
| 9 | Findings |
| 10 | Output workbook (removed) |
| 11 | Exit codes and terminal output |
| 12 | Acceptance on the sample (removed) |
| 13 | Backtest (removed) |
| 14 | Input: TM rules |

---

## 1 · Terms

| Term | Meaning |
|---|---|
| Order (*đơn*) | A root item of the target sprint whose `Loại` is `Task`: one version of one app, e.g. `1.0.2 - Add ads/Add SDK` for Phone Cleaner. The unit of assignment (D5). |
| PIC | The one dev who owns an order and later splits it into subtasks (D5). |
| Pool | Devs in `devs.xlsx` with `Nhận việc` = `Y`, minus those on leave for the whole sprint (A12). Today: LinhNV, MinhNM, AnTD, TiếnBV (D7). Everyone else is ignored everywhere, silently (D14). |
| Target sprint | The running sprint of board Maintain (bot spec §2.3, A59), or the one given with `--sprint-id`. BA/MO run the tool when they file an order (D61): orders already assigned are kept, empty ones are assigned. |
| Previous sprint | The Maintain sprint that ended last before the target's first day (A59). Source of carry-over only (A60). |
| Size | The AI's class for an order, `S`/`M`/`L`/`XL`, worth 4/16/32/64 hours (§6.4, A7). |
| Load | The orders a pool dev holds in the target sprint, pre-assigned or proposed: counted in orders for the load cap (§7, D26) and summed in hours (their sizes) for key part 3. |
| Carry-over | Number of rows (orders and subtasks) of the previous sprint assigned to the dev whose status is busy (D8, A60). |
| Familiarity | How well a dev knows the order's app, from the history (§5, §6.1). |
| TM rule | One row of the TM's rules file (§14): pin a dev to an app, keep a dev off an app or off everything, cap a dev's orders, or prefer a dev for an app. Read without AI (D28). |
| Board | List "Tech manager" holds every order: Maintain orders (in a two-week Maintain sprint, A56) and MVP / research or unscheduled ones. Only Maintain orders are assigned (D5); the rest are history only (D23). |

## 2 · Command line and input files

```
scrumbot assign <order file> [--input DIR] [--devs FILE] [--rules FILE] [--sprint-id ID] [--today DATE]
                [--state DIR] [--out DIR] [--ai gemini|agy|off] [--ai-model NAME] [--ai-timeout SECONDS] [-v]
```

Every option is in bot spec §1. `--today DATE` (`YYYY-MM-DD` or `DD/MM/YYYY`, A35) is the run day of the history
window (§5.1) and of the rules day (§14.3); unreadable is an input error.
`--ai off` sizes every order `M` (§6.4).

**Input files** (A2, D29): in `--input`, `devs.xlsx` is the dev workbook (§4) and the only `*.md` is the TM rules file
(§14); no `.md` means no rules. The order file given to `assign` (bot spec §7) is never taken for the rules file. Discovery never guesses: no `devs.xlsx`, or several `.md` files, is an input error that
names the candidates and the flag to use (`--devs`, `--rules`). Files whose names start with `~$` (Excel lock files)
and `.` are ignored.

## 3 · Input: the target sprint

The orders come from the API (bot spec §2.5): the target sprint becomes rows with the columns `STT` · `ID` · `Task` ·
`App Name` · `Trạng thái` · `Người làm` · `Ưu tiên` · `Hạn` · `Ngày tạo` · `Bug mở` · `Bug tổng` (A76), and the
sprint's first and last days come from the sprint list. An order with a `Người làm` is **pre-assigned**: kept as it
is (D10), its size added to its devs' load. An empty one is assigned by §7. Subtasks are never assigned and never
measure size (D5, D9). The export workbook this section once described was removed on 2026-10-13 (D59).

## 4 · Input: dev workbook

`devs.xlsx`, maintained by hand (D11). First sheet, header on row 1, one dev per row, empty rows ignored. Headers
are matched by name, never by position, after NFC, trimming, removing a trailing `.` and casefolding.

| Header | Required | Values |
|---|---|---|
| `Tên` | ✓ | Full name exactly as the internal tool writes it in `Người làm`, e.g. `Ngọc Văn Linh`. Unique. |
| `Mã` | ✓ | Short code shown in the output, e.g. `LinhNV`. Unique. |
| `Level` | ✓ | `junior`, `junior+`, `middle`, `middle+`, `senior`, case-insensitive (A13). |
| `Nhận việc` | ✓ | `Y` or `N`. `N` takes a dev out of the pool without deleting the row. |
| `Ngày nghỉ` | — | Leave days inside the sprint, separated by `,`: `YYYY-MM-DD` or `DD/MM/YYYY`, or real date cells. |

Example (the pool of D7; the full names are the ones the system uses):

| Tên | Mã | Level | Nhận việc | Ngày nghỉ |
|---|---|---|---|---|
| Ngọc Văn Linh | LinhNV | middle+ | Y | |
| Nguyễn Nhật Minh | MinhNM | middle | Y | |
| Trần Đức An | AnTD | junior+ | Y | |
| Bùi Văn Tiến | TiếnBV | junior | Y | |

Input errors: a missing required header, an invalid level, `Nhận việc` not `Y`/`N`, a duplicate `Tên` or `Mã`, an
unreadable date, and an empty pool after leave exclusion.

**Known cost of D14:** a pool dev's name spelled differently in the system (missing diacritic, extra word) is treated
as a stranger, so that dev's load is silently too low. NFC and whitespace normalisation (A10) remove the common
cases; the remaining ones are not reported.

## 5 · History

The history is every root order the API returns for the Maintain sprints and list "Tech manager" (bot spec §2.3,
A56), MVP / research orders and orders with no sprint included (A23, D23). Familiarity counts the root order's
`Người làm` only (A26); an order with no app never makes anyone familiar. The hours of an old order
(`uoc_luong_gio`) are only sent to the AI as examples (§6.4, A19). The reason text quotes the order's sprint name
(A25).

### 5.1 History window (A22)

A run uses the history orders that existed **before it**:

1. not an order of the target sprint: an order never serves as its own history;
2. created on or before the run day;
3. its earliest sprint, if it has one, started on or before the run day.

The run day is today, or the day given with `--today` (A35), so a run on a past day never sees a later assignment.

## 6 · Derived facts

§6.1–§6.3, §7 and the prompt and parsing of §6.4 are pure computation over values from §3–§5 (LLM.md §2). Only the
call to the AI tool itself is I/O.

### 6.1 Familiarity of a dev with an app

For each app, consider the history orders of that app that name **at least one pool dev**. The most recent of them
by `Ngày tạo` is the app's **latest version**. Orders naming only people outside the pool are ignored here: an RnD
research order is not a version a pool dev worked on.

| Rank | Meaning | Reason text |
|---|---|---|
| 0 | The dev is named on the app's latest version. | `Làm version gần nhất của <app> (<Sprint>: <Task>)`; `<Sprint>` is the history order's `Sprint` cell as written, `Tháng <m>/<yyyy>` of the creation date when it is empty (A25) |
| 1 | The dev is named on an older version only. | `Từng làm <app> (<k> version)` |
| 2 | Never named on this app. | `Chưa làm <app>` |

An app with no history order naming a pool dev is a **new app**: every dev has rank 2.

### 6.2 Carry-over

For each pool dev: the number of previous-sprint rows (orders **and** subtasks) that name the dev in `Người làm` and
whose `Trạng thái` is busy (D8, compared by name, A60): `qa - need fix`, `all issue`, `in progress`, `ready to progress`, `need to be clean`,
`internal - cant fix`, `internal - need fix`, `đã ro`. Every other status (`pending`, `qa - cant fix`, waiting for test,
done) is not busy. Statuses are compared after NFC, trimming and casefolding. `đã ro` is busy by the user's choice
(D8), although the system counts it as done.

### 6.3 Leave

Working days of the sprint are Monday to Friday between its first and last days, inclusive. A dev whose leave days
cover every working day is removed from the pool (`DEV-ON-LEAVE`); since 2026-10-13 a dev off every **remaining**
working day is removed too (`DEV-ON-LEAVE-REST`, bot spec §3, A75), and key part 5 counts the remaining days only. A pre-assigned order held by such a dev and by no other pool dev is kept (D10) and reported (`PRE-ASSIGNED-ON-LEAVE`, A43): nobody in the pool works on it. Otherwise the number of leave days on working days
is a tie-breaker only (A12). Leave days outside the sprint are ignored.

### 6.4 Size (AI)

Every order of the target sprint gets a size, **pre-assigned ones included**, because their size counts toward
load (D13). The AI only sizes; it never sees people and never picks a PIC.

**Classes** (A7):

| Class | Hours | Meaning given to the AI |
|---|---|---|
| `S` | 4 | One small item only: a single crash, a single policy or store change, a text or config change. |
| `M` | 16 | Two to three days: one feature-sized item, or two or three small items. |
| `L` | 32 | About a week: several items, e.g. ads or IAP changes together with flow (`luồng`) or UI changes. |
| `XL` | 64 | More than a week: a new feature, a new SDK, a new app, or many items at once. |

The prompt also tells the AI that an order is one release of one app whose PIC does every item listed, and that items
written as "Fix" (`Fix ads`, `Fix luồng`, `Fix UI`) rework existing screens and each takes days (A44). Without that,
the AI read "Fix ads/Fix luồng/fix policy" as a policy fix (`S`) when it took 68h (measured 2026-10-08).

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
2. Up to 30 **examples**: history orders with hours > 0 (A19), the target sprint's apps first, then most recent
   first. Each line: app · title · hours. No names.
3. The **orders**: each line `STT` · app · priority · title · description. The API returns no description today
   (D50); only the order file of `assign` gives one, with links and names already replaced (bot spec §7.2). Every
   URL left is replaced by `[link]` and the text is cut to 600 characters.
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

A finding is a line of `## Cảnh báo dữ liệu` in `output.md` (bot spec §7.4), not an exception: the run goes on and
the report is written. The review checks of bot spec §7.3 (`REVIEW-…`) are not findings: they stop the assignment. Codes are
never renamed once released. Nothing is ever reported about people outside the pool (D14).

| Code | Level | When | Message (Vietnamese, exact) |
|---|---|---|---|
| `SIZE-AI-FAILED` | WARN | The AI call failed (§6.4). | `Không ước lượng được độ lớn bằng AI (<lý do ngắn>); mọi đơn tính là M (16h).` |
| `SIZE-AI-INVALID` | WARN | The call worked but some orders have no valid element. One finding listing them. | `AI không trả độ lớn hợp lệ cho đơn STT <danh sách>; các đơn này tính là M (16h).` |
| `APP-MISSING` | WARN | An order has an empty `App Name`. | `Đơn STT <n> không có App Name; coi như app chưa ai làm.` |
| `PRIORITY-UNKNOWN` | WARN | `Ưu tiên` is not urgent/high/normal/low/empty. | `Đơn STT <n> có Ưu tiên "<giá trị>" không hợp lệ; coi như normal.` |
| `DUE-BEFORE-CREATED` | WARN | `Hạn` is before `Ngày tạo`. | `Đơn STT <n> có Hạn <hạn> trước Ngày tạo <ngày tạo>.` |
| `TYPE-UNKNOWN` | WARN | `Loại` is neither `Task` nor `Subtask`. | `Dòng STT <n> có Loại "<giá trị>" không hợp lệ; bỏ qua dòng này.` |
| `PREV-SPRINT-MISSING` | WARN | No previous Maintain sprint (A59). | `Không có sheet <tên>; coi như không dev nào còn việc dở.` |
| `DEV-ON-LEAVE` | INFO | A pool dev is off for every working day. | `<Mã> nghỉ cả sprint; không được giao đơn.` |
| `PRE-ASSIGNED-ON-LEAVE` | WARN | A pre-assigned order names a dev who is off for every working day (`DEV-ON-LEAVE`) and no other pool dev, so nobody in the pool works on it (A43). The order is still kept (D10). `where` = `Đơn STT <n>`. | `Đơn STT <n> giao sẵn cho <Mã> nhưng <Mã> nghỉ cả sprint; đơn chưa có ai làm, cân nhắc giao lại.` |
| `RULE-DEV-UNAVAILABLE` | WARN | A `Chỉ định` or `Ưu tiên` rule in force names a dev who is not in the pool: `Nhận việc` = `N` or on leave for the whole sprint (D35). `where` = `Luật dòng <n>`. | `Luật dòng <n> (<Loại> <Mã>) không áp dụng: <Mã> không nhận việc hoặc nghỉ cả sprint.` |
| `RULE-NO-CANDIDATE` | WARN | The `Không giao` and `Tối đa đơn` rules left no candidate for an order (§7, A31). | `Luật TM loại hết dev khỏi đơn STT <n>; đơn này được giao như khi không có luật Không giao và Tối đa đơn.` |
| `DUE-MISSING` | WARN | An `urgent` or `high` order has no `Hạn` (D53, bot spec §3). | `Đơn STT <n> là đơn <urgent\|high> nhưng chưa có Hạn.` |
| `DEV-ON-LEAVE-REST` | INFO | A pool dev is off every remaining working day, not every day of the sprint (A75, bot spec §3). | `<Mã> nghỉ hết các ngày còn lại của sprint (từ <ngày gốc>); không được giao đơn mới.` |

## 10 · Output workbook (removed 2026-10-14)

The workbook belonged to `run` (D62); it is in git history at `754b165`. What it showed for one order and for each
dev is in `output.md` (bot spec §7.4). Until the tool can write into the internal system (D19, O8), `output.md` is the
assignment: the person who filed the order enters the PIC into the system (D61).

## 11 · Exit codes and terminal output

| Code | When |
|---|---|
| `0` | `output.md` was written: the order ready or not (bot spec §7.3), with or without findings, with or without AI sizes. |
| `2` | Input or usage error. No report is written. The message names the file, sheet, row or column. |
| `130` | Interrupted with Ctrl+C. |

The terminal lines are listed in bot spec §7.4.

## 12 · Acceptance on the sample (removed 2026-10-13)

The acceptance runs on the export sample in `input/` were removed with the sample (D59). The command line and a run
are covered end to end against a local fake API: `tests/test_cli.py` and `tests/test_assign_order.py`.

## 13 · Backtest (removed 2026-10-13)

The backtest, and the replay on a copy of the API data that replaced it, were removed (D59). Their last numbers: the
backtest matched the TM on 43 of 92 orders (47%); the replay of 2026-10-13 (29 sprints) on 111 of 174 (64%).

## 14 · Input: TM rules

The TM steers the choice without editing code: a rules file pins a dev to an app, keeps a dev off an app or off every
order, caps a dev's orders, or prefers a dev for an app (D28, D30). The rules are a fixed table read without AI, so
every choice stays repeatable and explainable in `Lý do` (§8). The AI never sees
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
2. Columns are found by header name (as §4), never by position; unknown columns are ignored. Cells are split on
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
not only the rules in force, so a run on any day accepts or rejects the same file.

A valid rule that cannot act is not an error: a `Chỉ định` or `Ưu tiên` for a dev outside the pool is a
`RULE-DEV-UNAVAILABLE` finding (§9); a rule whose app has no order in the sprint is not reported (D35).

### 14.3 Rules in force

A rule is in force on a day when `Từ ngày` ≤ day ≤ `Đến ngày`. The day is today (or `--today`, A35), but not earlier
than the target sprint's first day (A34): a TM who runs the tool on the Friday before Sprint 10 gets the rules dated
for Sprint 10.

How each kind acts is in §7; what it writes in `Lý do` is in §8. Rules never touch pre-assigned orders (D10), never
add a dev outside the pool (D7), and leave the cap's "+ 1 order" (D26) as it is.
