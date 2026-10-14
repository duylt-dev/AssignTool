# Bot spec: `scrumbot`

What the scrum-master bot adds on top of the assignment core of [`assignment-spec.md`](assignment-spec.md): reading
the internal system's API, the review of an order file, the risk register and the AI memory. [`LLM.md`](../LLM.md) says where each part lives in code;
[`confirm.md`](../confirm.md) holds the decisions cited here (`Dn` user-locked, `An` defaults, `On` open).

**Status:** written 2026-10-13 for stage 1 (D57); scope cut the same day (D59); `assign` added the same day (D60); `run`, the Excel report and the memory between runs removed and the review added on 2026-10-14 (D62). User-facing text is Vietnamese (D12) and quoted exactly as the
bot writes it. `<n>` is an order's STT, `<Mã>` a dev code, dates are `DD/MM/YYYY`, hours are whole numbers.

| § | Contents |
|---|---|
| 1 | Commands |
| 2 | Source: the internal system API |
| 3 | Run day, base day, remaining days |
| 4 | Risk register |
| 5 | Memory: AI answers only |
| 6 | Report (removed) |
| 7 | `assign`: one order file, a review, one Markdown report |

---

## 1 · Commands

One program, `scrumbot`, with one sub-command, **`assign <file>`** (D60, D62). BA/MO run it when they file an order
(D61). It reads the system (§2), places the order file in the running sprint, reviews it (§7.3) and, when the review
passes, assigns (assignment spec §7), builds the risk register (§4) and writes `<--out>/output.md` (§7.4). `scrumbot`
without a sub-command prints the usage and exits `2` (A91). `run`, its Excel report and the memory between runs were
removed on 2026-10-14 (D62); they are in git history at `754b165`.

| Option | Default | Meaning |
|---|---|---|
| `--sprint-id ID` | the running sprint (§2.3) | The sprint to assign. |
| `--input DIR` | `input/` | Where `devs.xlsx` and the TM rules file are found (assignment spec §2). |
| `--devs FILE` | `input/devs.xlsx` | Dev workbook (assignment spec §4). |
| `--rules FILE` | the only `*.md` in `--input` | TM rules (assignment spec §14). |
| `--today DATE` | the clock | Run day (A35). |
| `--state DIR` | `state/` | AI answers and list cache (§5). |
| `--out DIR` | `output/` | Where `output.md` goes. |
| `--ai gemini\|agy\|off`, `--ai-model`, `--ai-timeout` | `gemini`, none, 180 s | The AI tool (assignment spec §6.4). |
| `-v` | off | Traceback and the AI exchange on errors. |

Exit codes are those of assignment spec §11. An API error (§2.2) is exit `2`.

## 2 · Source: the internal system API

### 2.1 Configuration (A54, D49, A64)

The bot reads `SCRUMBOT_API_TOKEN` and `SCRUMBOT_API_BASE` from the environment, else from `.env` in the working
directory (`KEY=value` lines; spaces around `=` and surrounding quotes are allowed; `#` lines are comments). The
environment wins over the file.

| Case | Message (exit 2) |
|---|---|
| Token missing | `Thiếu SCRUMBOT_API_TOKEN (trong .env hoặc biến môi trường).` |
| Base missing | `Thiếu SCRUMBOT_API_BASE (trong .env hoặc biến môi trường), ví dụ https://devclickup.datlt.site.` |
| Base is production | `SCRUMBOT_API_BASE trỏ tới production (circle.datlt.site); bot chỉ đọc server dev (confirm.md D49).` |

### 2.2 Calls (A55)

`GET <base>/api/doc/<path>?<params>` with `Authorization: Bearer <token>` and `User-Agent: scrumbot/<version>`,
timeout 60 s. `429` waits 30 s and retries, three times at most. Every other failure stops the run (exit 2):

| Case | Message |
|---|---|
| `401` | `API từ chối token (401). Kiểm tra SCRUMBOT_API_TOKEN, hoặc xin TM token mới.` |
| `404` | `API trả 404 cho <path>: API đang tắt trên server hoặc id không còn trong phạm vi.` |
| `429` after 3 retries | `API vẫn giới hạn tải (429) sau 3 lần thử; chạy lại sau ít phút.` |
| `5xx` | `API lỗi phía server (<code>) ở <path>; thử lại sau.` |
| other HTTP code | `API trả mã <code> ở <path>.` |
| network error, timeout | `Không gọi được API <host>: <reason>.` |
| reply not JSON, or `ok` false | `API trả dữ liệu không đọc được ở <path>.` |

The token never appears in a message, a log line, a report or a stored file.

Three endpoints (`docs/api-doc-he-thong.md`): `sprints?folder_id=90169740714` (folder Maintain), `don?list_id=…&trang=…`
(every page, until `trang × goc_moi_trang ≥ tong_goc`) and `lich-su?task_id=…` (batches of 50 ids).

### 2.3 What a run reads (A56, A58, A59)

**Maintain sprints** are lists with `kieu` = `sprint`, a name starting with `Sprint ` and `tong` > 0 (A56). The sprint
label is the list name, e.g. `Sprint 10 (10/6 - 10/17)`; its number is the integer after `Sprint`.

**Running sprint:** the Maintain sprints, not archived, whose `bat_dau` ≤ run day ≤ `ket_thuc`. Several: those with
orders win; still several, or none, is an input error:

- none: `Không có sprint Maintain nào đang chạy ngày <dd/mm/yyyy>. Chọn sprint bằng --sprint-id.`
- several: `Có nhiều sprint đang chạy ngày <dd/mm/yyyy>: <tên> (<id>), …. Chọn một bằng --sprint-id.`
- unknown `--sprint-id`: `Không có sprint id '<id>' trong folder Maintain.`

**Previous sprint:** the Maintain sprint (archived or not) whose `ket_thuc` is the latest before the running sprint's
`bat_dau`. Source of carry-over (assignment spec §6.2 on its rows, by status name, A60).

**A run reads:** the sprint list; `don` of every Maintain sprint and of list Tech manager (`901609972453`); `lich-su`
of every item of the running sprint. Archived lists are cached in `state/cache/` for good; lists whose `ket_thuc` is
before today are cached for the day; the running sprint, list Tech manager and the history are always read fresh.

### 2.5 From API items to orders

An item is a **root** when `cha_id` is null; roots with `loai` = `task` are the orders (D5); bugs are never orders.
Every non-root task is a subtask of its nearest root; bugs belong to the tree of their root.

| Order field | From |
|---|---|
| STT | 1, 2, … over the roots sorted by `ngay_tao`, then `id` (A76) |
| title, app, priority, due, hours | `ten`, `app`, `uu_tien`, `han`, `uoc_luong_gio` |
| status, status kind | the name and `kieu` of `trang_thai_id` |
| `Người làm` | the names of `nguoi_lam_ids`; matched with `devs.xlsx` by name (A10) |
| created, updated, closed | `ngay_tao`, `ngay_cap_nhat`, `ngay_dong` |
| description | none: the API has none (D50); the order file of `assign` gives one (§7.2) |

Status kinds for names found only in the history (renamed statuses) come from every status table read in the run
(A74); an unknown name has no kind.

**History** (familiarity, assignment spec §6.1) is every root task of list Tech manager and of every Maintain sprint,
once per `id`. Its sprints are the Maintain sprints whose `don` lists it, quoted by their label (A25); its filing day is
`ngay_tao`; its hours are `uoc_luong_gio` (AI examples, A19). The window of assignment spec §5.1 applies unchanged.

**Freshness:** the newest `ngay_cap_nhat` among the items read, shown as `dữ liệu API mới nhất` in `output.md` and
on the terminal (D49).

### 2.6 AI with memory (A67, A79)

The prompt of assignment spec §6.4 also asks, per order, for `type` (one of `ads`, `iap`, `flow_ui`, `policy`, `crash`,
`sdk`, `feature`, `other`), `items` (at most 5 short strings), `tech_risks` (at most 2 short Vietnamese strings, e.g.
a new SDK or a store deadline) and `questions` (at most 2 short Vietnamese questions to the person who filed the
order, about what its description leaves unclear for doing the work; an empty list when the order has no description
or nothing is unclear; A90). A wrong or missing extra key leaves the size untouched. In the report the type reads
`Ads`, `IAP`, `Luồng/UI`, `Policy`, `Crash`, `SDK`, `Tính năng`, `Khác`.

A valid AI answer is remembered by order `id` + title (casefolded); the AI is called only for orders without one.
The order of an `assign` file is the exception: always sized, never remembered (§7.2).
`Độ lớn` then reads, e.g., `AI (agy, 6/6 đơn; 5 từ bộ nhớ)`. Defaults (`M`) and `questions` are never remembered.

## 3 · Run day, base day, remaining days

- **Run day:** today, or `--today` (A35).
- **Base day:** the run day, but not before the sprint's first day (A34, A73).
- **Remaining days:** working days (Monday–Friday) from the base day to the sprint's last day, inclusive.
- **Leave (A75, R8):** a pool dev off every working day of the sprint is out of the pool (`DEV-ON-LEAVE`); a dev off
  every remaining day is out too, with the INFO finding `DEV-ON-LEAVE-REST`:
  `<Mã> nghỉ hết các ngày còn lại của sprint (từ <base day>); không được giao đơn mới.` (`where` = `<Mã>`). Key part 5
  of assignment spec §7 counts leave days among the remaining days. On the sprint's first day this is exactly the
  earlier behaviour.
- **`DUE-MISSING`** (WARN, D53): `Đơn STT <n> là đơn <urgent|high> nhưng chưa có Hạn.` (`where` = `Đơn STT <n>`).

## 4 · Risk register

Risks advise; the rule of assignment spec §7 still decides. No risk changes a PIC, a pre-assigned order (D10), the
cap (D26) or the exit code (LLM.md §12).

### 4.1 Common terms (A73)

| Term | Meaning |
|---|---|
| Open order | A root order whose status is busy (D8) or empty: work is left for its dev. |
| Not started | Status `ready to progress`, `pending`, `all issue` or empty. |
| Done | Status kind `done`/`closed`; when the kind is unknown, status `done`, `ready to release`, `close`, `complete` or `đã ro`. |
| PIC | The pool devs on the order: the TM's for a pre-assigned order, the bot's for its proposal. |
| Deadline | `Hạn`, else the sprint's last day. Written `hạn <date>` or `cuối sprint (<date>)`. |
| Days left `k` | Working days from the base day to the deadline, inclusive (0 when the deadline is past). |
| Capacity of a dev | 6 × (remaining days − leave days among them) hours (R6). |
| Hours left on an order | Its size hours × the share of its subtasks whose status is busy (D8) or empty, rounded half up; an order without subtasks counts whole (A73). Measured 13/10: counting whole orders mid-sprint put all four devs and the sprint at `Cao`. |
| Load left of a dev | Sum of the hours left on the open orders whose PIC includes the dev. |
| Sprint load, sprint capacity | Sum of the hours left on the open orders with a PIC, each order once; sum of the pool's capacities. |
| Reverse order | The opposite of the processing order of A5: lowest priority, latest or no due date, newest, highest STT first. |
| Defer list | Not-started open orders of a set, in reverse order, taken until their hours cover the excess. |
| Suggestion | The PIC that §7 picks for the order when it is emptied, every other order keeps its PIC, and the order's current devs are left out of the pool. Its reason is the §8 text. |

**Levels:** `Cao`, `Trung bình`, `Thấp`, fixed per code; order risks go one step up for an urgent or high order (T4),
never above `Cao`. **Due to act (`Hạn xử lý`):** `Cao` the base day, `Trung bình` one working day later, `Thấp` two.
**Order of rows:** level, then code, then where.

### 4.2 Codes

| D45 # | Code | Group | Level | Fires when |
|---|---|---|---|---|
| 2 | `CAPACITY-DEV` | Năng lực | Trung bình; Cao above 1.5 × capacity | A pool dev's load left > capacity |
| 3 | `CAPACITY-SPRINT` | Năng lực | Cao | Sprint load > sprint capacity, unless `SCOPE-ADDED` fires |
| 4 | `SCOPE-ADDED` | Năng lực | Cao | Sprint load > capacity, and without the open orders filed after the sprint's first day it would fit |
| 5 | `PIC-UNFAMILIAR` | Phân công | Thấp (+1) | An open urgent/high order with an app whose every PIC dev has familiarity rank 2 |
| 6 | `PIC-ABSENT` | Phân công | Cao | An open order whose pool devs are all off every remaining day |
| 7 | `DUE-AT-RISK` | Tiến độ | see below (+1) | Overdue, not started near the deadline, or many open subtasks near the deadline |
| 8 | `CARRY-OVER` | Năng lực | Thấp; Trung bình from 3 | A pool dev has carry-over ≥ 1 and at least one open order |
| 10 | `STATUS-STUCK` | Tiến độ | Trung bình (+1) | The order or a subtask stays in a status longer than its A49 threshold |
| 11 | `QA-RETURNS` | Chất lượng | Trung bình (+1) | A not-done order went back to `qa - need fix` ≥ 2 times, has ≥ 5 bugs, or has open bugs with `k` ≤ 3 |

Risks 1 and 12 are postponed (D53); the review of §7.3 covers part of risk 1 for the order file. Risk 9
(`ORDER-CHANGED`) was removed with the memory (D62). Columns of each row: `Vấn đề` (problem), `Ảnh hưởng` (impact), `Đề xuất` (action),
`Ai xử lý` (owner).

**`CAPACITY-DEV`** — where `<Mã>`; owner `TM`.
- Problem: `<Mã> còn <h>h việc (<n> đơn), sức chứa còn <c>h (<d> ngày × 6h)`
- Impact: `Có thể không xong hết đơn trước <sprint end>.`
- Action: `Cân nhắc chuyển STT <x> cho <Mã2> (còn trống <f>h)`, where `<x>` is the dev's first open order in reverse
  order (not-started ones first) and `<Mã2>` the other pool dev with the most free hours (ties by code); when nobody
  has free hours: `Không dev nào còn trống; xem rủi ro của sprint.`

**`CAPACITY-SPRINT`** — where the sprint label; owner `TM`.
- Problem: `Sprint còn <h>h việc, sức chứa của team còn <c>h`
- Impact: `Khoảng <h − c>h việc có thể trễ sang sprint sau.`
- Action: `Đề xuất đẩy sang sprint sau: STT <a>, <b> (<k>h), hoặc thêm người ngoài team` (defer list of every open
  order); empty list: `Không còn đơn chưa bắt đầu để đẩy; cân nhắc thêm người ngoài team.`

**`SCOPE-ADDED`** — where the sprint label; owner `TM`.
- Problem: `<m> đơn lên sau ngày đầu sprint (STT <a>, <b>: <ha>h) làm tải vượt sức chứa (<h>h > <c>h)`
- Impact: as `CAPACITY-SPRINT`.
- Action: `Đề xuất đẩy sang sprint sau: STT <a> (<k>h)` (defer list of the late orders); empty list:
  `Các đơn lên giữa sprint đã bắt đầu; cân nhắc thêm người ngoài team.`

**`PIC-UNFAMILIAR`** — where `Đơn STT <n>`; owner `TM`.
- Problem: `Đơn STT <n> (<priority>) giao cho <Mã> nhưng <Mã> chưa làm <app>`
- Impact: `PIC mất thêm thời gian tìm hiểu app trên một đơn gấp.`
- Action: `Nhờ <Mã2> (<familiarity text>) hỗ trợ khởi động`, `<Mã2>` being the pool dev off the order with the best
  rank (0, then 1; then higher level, then code) and the text that of assignment spec §6.1; new app:
  `App mới với team: tính thêm thời gian tìm hiểu.`

**`PIC-ABSENT`** — where `Đơn STT <n>`; owner `TM`. Only orders that name a pool dev and no pool dev who still works.
- Problem: `Đơn STT <n> giao cho <Mã> nhưng <Mã> nghỉ các ngày còn lại của sprint (từ <base day>)`
- Impact: `Đơn không có ai làm tới hết sprint.`
- Action: `Chuyển cho <Mã2>: <reason>` (the suggestion); none: `Không còn dev trong team; cân nhắc người ngoài team hoặc
  đẩy sang sprint sau.`

**`DUE-AT-RISK`** — where `Đơn STT <n>`; owner the PIC codes (`TM` for a proposal). Open or not-started orders with a
PIC; the first branch that applies:
1. `Hạn` < base day: `Đơn STT <n> quá hạn <Hạn> (trạng thái "<status>")`; impact `Đơn đã trễ hạn.`; `Cao`.
2. Not started and `k` ≤ 3: `Đơn STT <n> còn <k> ngày làm việc tới <deadline> nhưng vẫn "<status>"` (empty status:
   `nhưng vẫn chưa bắt đầu`); impact `Đơn có thể trễ hạn.`; `Trung bình`, `Cao` when `k` ≤ 1.
3. Started, `k` ≤ 3, and at least 2 and at least half of its subtasks not done:
   `Đơn STT <n> còn <k> ngày làm việc tới <deadline> mà còn <m>/<t> subtask chưa xong`; impact as 2; level as 2.
- Action: `Hỏi <PIC> lý do; nếu kẹt: chuyển cho <Mã2> hoặc lùi hạn` (`<Mã2>` the suggestion); no suggestion:
  `Hỏi <PIC> lý do; nếu kẹt: lùi hạn hoặc đẩy sang sprint sau.`; on an order that only has the bot's proposal:
  `Giao ngay cho <Mã>; nếu không kịp: lùi hạn hoặc đẩy sang sprint sau.`

**`CARRY-OVER`** — where `<Mã>`; owner `TM`.
- Problem: `<Mã> còn <k> việc dở ở <previous sprint>`
- Impact: `Sức chứa thật của <Mã> ở sprint này thấp hơn tính toán.`
- Action: `Hỏi <Mã> khi nào xong việc dở; tính tới khi giao thêm đơn.`

**`STATUS-STUCK`** — where `Đơn STT <n>`. Thresholds of A49, in working days: root `in progress` 4, `ready to
progress` 2, `ready to qa-testing` 2, `ready to internal testing` 2, `ready to release` 6; subtask `in progress` 2,
`ready to progress` 3, `ready to qa-testing` 2, `ready to internal testing` 2. Time in status = working time (Saturday
and Sunday removed) from the last history event into the current status to the run time, one decimal; without such an
event, from the last event; without history, from `ngay_cap_nhat`; without that, not checked. The time is compared
after rounding to one decimal, as shown (`4,0 ngày (ngưỡng 4)` never appears). Subtasks are checked only under a root
that is not done. An order that only has the bot's proposal is not checked: nobody holds it yet, and the proposal is
the action.
- Problem: the root stuck: `Đơn STT <n> ở "<status>" <x> ngày làm việc (ngưỡng <t>)`; subtasks stuck:
  `<s> subtask kẹt, lâu nhất "<subtask>" ở "<status>" <x> ngày (ngưỡng <t>)`, prefixed by `Đơn STT <n> có ` when
  the root is not stuck and joined with `; ` when it is.
- Impact: `Đơn chậm lại; có thể trễ hạn.`
- Action, by the status of the root when it is stuck, else of the longest-stuck subtask: `in progress`, `ready to
  progress` → `Hỏi <PIC> đang vướng gì.` (owner the PIC codes; without PIC `Hỏi người làm đang vướng gì.`, owner `TM`); `ready to qa-testing`, `ready to
  internal testing` → `Nhắc khâu test nhận đơn.` (owner `TM`, D40); `ready to release` → `Nhắc khâu phát hành.`
  (owner `TM`).

**`QA-RETURNS`** — where `Đơn STT <n>`; owner the PIC codes, else `TM`. Bugs are the bug items in the order's tree.
- Problem: `Đơn STT <n> ` + what applies, joined with `; `: `về "qa - need fix" <r> lần`, `có <b> bug (<o> chưa
  xong)`, `còn <o> bug mở khi còn <k> ngày làm việc tới <deadline>`.
- Impact: `Bản build còn nhiều lỗi; vòng test có thể kéo dài.`
- Action: `Hỏi <PIC> nguyên nhân; cân nhắc review code trước khi gửi test.`; no PIC: `Tìm nguyên nhân trước khi gửi
  test lại.`

## 5 · Memory: AI answers only (D62)

`state/scrumbot.sqlite` (A51) holds only the AI answers of §2.6 (A67); `state/cache/` holds the list cache (§2.3, A58).
Kept proposals, the stored state of orders, outcomes and the `Thay đổi` sheet were removed with `run` (D62). A file
written before may still hold their tables; the bot ignores them.

## 6 · Report (removed 2026-10-14, D62)

The six-sheet Excel report belonged to `run`. The only report is `output.md` (§7.4).

## 7 · `assign`: one order file, a review, one Markdown report (D60, D62)

`scrumbot assign <file> [options]`, e.g. `scrumbot assign input/don/req.md --ai agy`. BA/MO run it when they file an
order (D61). It answers two questions for that order: is it ready to be assigned (§7.3), and if so who takes it, why,
who backs up, and what may go wrong. Everything is decided on the whole running sprint, so the load and the risks are
those of the real sprint plus this order.

### 7.1 The order file (A82)

A `.md` file, usually in `input/don/` (an order file at the top of `--input` is never taken for the TM rules file).
Read by `sources/order_reader.py`, without AI.

```markdown
# Game Emulator - Chỉnh sửa và bổ sung luồng auto scan game

| Trường | Giá trị |
|---|---|
| ID | |
| App | Game Emulator |
| Ưu tiên | high |
| Hạn | 16/10/2026 |

Free text: the description, links, anything.
```

- **Title:** the first `# ` line; without one, the file name without `.md`.
- **Fields:** the first table whose header starts with `Trường`; keys `ID` (or `ID trên hệ thống`), `App` (or `App
  Name`), `Ưu tiên`, `Hạn` (`YYYY-MM-DD` or `DD/MM/YYYY`), case-insensitive; an empty cell is an empty field. Every
  field is optional.
- **Description:** every other line, as written.

| Input error (exit 2) | Message |
|---|---|
| The file is missing | `Không có file đơn '<file>'.` |
| Unreadable | `Không đọc được file đơn '<file>': <reason>` |
| Unknown key | `File đơn '<file>' dòng <n>: trường '<key>' không hợp lệ; dùng ID, App, Ưu tiên hoặc Hạn.` |
| `Hạn` not a date | `File đơn '<file>': Hạn '<value>' không đọc được; dùng YYYY-MM-DD hoặc DD/MM/YYYY.` |

### 7.2 The order in the sprint (A82, A83)

1. `ID` given: the root order with that `id` in the running sprint; none is the input error
   `Không có đơn gốc ID '<id>' trong <sprint>.`
2. No `ID`: the root order of the running sprint whose title equals the file's title (`text_key`); two or more is the
   input error `Có <k> đơn tên '<title>' trong <sprint>; ghi ID của đơn vào file đơn.`
3. Neither: a **new order**, not yet on the system: an empty root (no `Người làm`, no status) with the file's title,
   App, priority and `Hạn`, filed on the run day, numbered after the roots (subtasks and bugs move one STT down). Filed
   after the sprint's first day, it counts toward `SCOPE-ADDED` (§4.2) like any order added mid-sprint.

An order found on the system keeps its title, App, priority and `Hạn` from the API; the file only adds the
description. A pre-assigned order stays as it is (D10): the report says who holds it.

**What the AI reads** (A83): the description with every link replaced by `[link <kind>]` (`Figma`, `Google Docs`,
`Google Sheets`, `Google Slides`, `Google Drive`, else `[link]`; a Markdown link keeps its label unless the label is a
link), every known name replaced by `[người]` (the names and codes of `devs.xlsx` and every `Người làm` read from the
API), every word shaped like a person's code (a capitalised word ending in one to three capitals: `TestBA`, `TiếnBV`;
`GameUI` too) replaced by `[người]`, whitespace collapsed. The order of the file is **always sized by this call** and
its answer is never remembered (§2.6): the same `id` and title may carry another description next time.

**Memory** (A84, D62): `assign` reads the AI answers of §5 and writes those of the other orders of the sprint.

### 7.3 Review before the PIC (D62, A86–A89)

Right after the order is placed (§7.2) and before any AI call, the bot checks the order as placed: an order found on
the system has its App, priority and `Hạn` from the API (A82). An order that already has a `Người làm` is not
reviewed (A87). Checks, in this order (a "file order" is a new order, §7.2 case 3; an "order on the system" is cases 1
and 2):

| Code | Blocks when | Message for a file order | Message for an order on the system |
|---|---|---|---|
| `REVIEW-APP` | App is empty | `Thiếu App: ghi tên app vào dòng App của file đơn.` | `Thiếu App: điền App cho đơn trên hệ thống.` |
| `REVIEW-DUE` | Priority `urgent` or `high` and no `Hạn` | `Đơn <urgent\|high> chưa có Hạn: ghi dòng Hạn của file đơn (YYYY-MM-DD hoặc DD/MM/YYYY).` | `Đơn <urgent\|high> chưa có Hạn: điền Hạn cho đơn trên hệ thống.` |
| `REVIEW-DESC` | The description the AI reads (§7.2), without its `[link …]` and with whitespace collapsed, has fewer than 30 characters (A88) | `Mô tả quá ngắn (<k> ký tự, cần từ 30, không tính link): ghi rõ các hạng mục cần làm.` | the same |

**Not ready** (any check fires): no AI call, no assignment, no risk register (A86); exit `0` (A89). `output.md` is:

```markdown
# Giao đơn: <title>

<sprint> (<start> – <end>) · chạy <dd/mm/yyyy HH:MM> · dữ liệu API mới nhất <dd/mm/yyyy HH:MM>

## Review: chưa đạt

Bot chưa đề xuất PIC. Sửa các mục dưới đây rồi chạy lại `scrumbot assign <file>`:

- `REVIEW-APP`: <message>
```

**Ready:** the bot sizes, assigns and builds the register as before, and `output.md` (§7.4) carries the AI's questions
(A90) in its `## Review: đạt` section. They never block.

### 7.4 The report when the order is ready: `<--out>/output.md` (A85)

Written to `output.md.tmp` and renamed; each run replaces the previous file. Sections, in this order:

1. `# Giao đơn: <title>`, then `<sprint> (<start> – <end>) · chạy <dd/mm/yyyy HH:MM> · dữ liệu API mới nhất <…>`.
   **`## Review: đạt`** follows (not for a pre-assigned order, A87): `Câu hỏi của AI cho người lên đơn (không chặn;
   trả lời trong file đơn nếu cần):` and one `- <question>` per question; `AI không có câu hỏi.` when the AI answered
   for the order with none; `Không có câu hỏi của AI (AI tắt hoặc lỗi).` when the order's size is the default.
2. **`## Kết luận`**: `PIC đề xuất: <Mã>`, `Lý do: <assignment spec §8>`, `Dự phòng: <Mã>, <Mã>` (or, for a
   pre-assigned order, `Đã có người làm trên hệ thống: <codes or người ngoài team>. Bot giữ nguyên, không đề xuất PIC
   khác.`), `Độ lớn (AI): <size> (<h>h)[ (mặc định)]: <AI reason>`, `Rủi ro liên quan: <x> cao · <y> trung bình · <z>
   thấp`, and for a proposal `Bot chưa ghi được vào hệ thống: người lên đơn nhập PIC vào hệ thống.` (D61)
3. **`## Thông tin đơn`**: `Đơn` (`Đơn mới, chưa có trên hệ thống (tính là STT <n> của <sprint>)` or `Đơn trên hệ
   thống, ID <id>, STT <n> (nối theo ID|theo tên đơn)`), `File đơn`, `App`, `Ưu tiên`, `Hạn` (`trống` when empty),
   `Loại đơn (AI)`, `Hạng mục (AI)`, `Mô tả AI đọc` (§7.2).
4. **`## So sánh dev`**: one row per active dev: `Dev` · `Level` · `Quen <app>` (`Làm version gần nhất`, `Từng làm
   (<k> version)`, `Chưa làm`; `—` without App) · `Đơn trong sprint` · `Giờ việc còn lại / sức chứa` (§4.1) · `Việc
   dở <previous sprint>` · `Ngày nghỉ còn lại` · `Vai trò` (`PIC`, `Người làm`, `Dự phòng 1`, `Dự phòng 2`, `Nghỉ cả
   sprint`, `Nghỉ hết các ngày còn lại`). Counts and hours include this order for its PIC.
5. **`## Rủi ro và phương án dự phòng`**: the risks of this order, of its PIC (where = a PIC code) and of the sprint
   (where = the sprint label): `Mức` · `Mã` · `Vấn đề` · `Ảnh hưởng` · `Phòng ngừa` (the `Đề xuất` of §4.2) · `Nếu
   xảy ra` · `Ai xử lý` · `Hạn xử lý`; none: `Không có rủi ro liên quan tới đơn này, PIC hoặc sprint.` Then ``Sổ rủi ro
   cả sprint: <x> cao · <y> trung bình · <z> thấp.``
6. **`## Rủi ro kỹ thuật (AI nhận xét, chỉ để tham khảo)`**: the AI's `tech_risks` (A79), or `Không có.`
7. **`## Cảnh báo dữ liệu`**: every finding except those about another order, as ``- <WARN|INFO> `<code>`:
   <message>``, or `Không có cảnh báo.`

**`Nếu xảy ra`** (A85), one fixed sentence per code:

| Code | Sentence |
|---|---|
| `CAPACITY-DEV` | `Chuyển đơn chưa bắt đầu sang dev còn trống giờ; không còn ai trống thì lùi hạn đơn ưu tiên thấp.` |
| `CAPACITY-SPRINT` | `Chốt với BA/MO các đơn đẩy sang sprint sau; giữ lại đơn urgent/high.` |
| `SCOPE-ADDED` | `Báo BA/MO dời hạn đơn mới hoặc tách bớt hạng mục sang sprint sau.` |
| `CARRY-OVER` | `Làm xong việc dở trước; đơn mới chưa bắt đầu thì chuyển cho người dự phòng.` |
| `PIC-UNFAMILIAR` | `Chuyển cho người dự phòng đã làm app, hoặc ghép người đó review code.` |
| `PIC-ABSENT` | `Chuyển đơn cho người dự phòng ngay; không còn ai thì đẩy sang sprint sau.` |
| `DUE-AT-RISK` | `Báo BA/MO lùi hạn hoặc cắt bớt hạng mục; cần thì thêm người hỗ trợ.` |
| `STATUS-STUCK` | `Gặp người làm để gỡ vướng; vướng ở khâu test hoặc phát hành thì báo người phụ trách khâu đó.` |
| `QA-RETURNS` | `Dừng gửi test; review code và tự test lại trước khi gửi QA lần nữa.` |

**Terminal:** `Ngày chạy: <dd/mm/yyyy> (--today)` when given, `Nguồn: API <host> (dữ liệu mới nhất <…>)`, `Luật
TM: …`, `Lịch sử: API (<n> đơn gốc)`, then `Đơn: <title> (đơn mới|đơn trên hệ thống <id>, STT <n> của <sprint>)`.
Not ready: `Review: chưa đạt (<k> mục)`, one line `- <code>: <message>` per check, `Báo cáo: <path>`. Ready, or a
pre-assigned order: `Đang ước lượng độ lớn bằng <tool>… (<n> đơn)` when the AI is called, `Review: đạt (<q> câu hỏi
của AI)` (left out for a pre-assigned order), `Độ lớn: <size>[ (mặc định)] · <sizing note>`, `PIC đề xuất: <Mã> (dự
phòng: …)` or `Đã có người làm: … (giữ nguyên)`, `Rủi ro liên quan: …`, each WARN finding of the report, and `Báo cáo:
<path>`.
