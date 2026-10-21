# Bot spec: `scrumbot`

What the scrum-master bot adds on top of the assignment core of [`assignment-spec.md`](assignment-spec.md): reading
the internal system's API, the review of an order file, the risk register and the AI memory. [`LLM.md`](../LLM.md) says where each part lives in code;
[`confirm.md`](../confirm.md) holds the decisions cited here (`Dn` user-locked, `An` defaults, `On` open).

**Status:** written 2026-10-13 for stage 1 (D57); scope cut the same day (D59); `assign` added the same day (D60); `run`, the Excel report and the memory between runs removed and the review added on 2026-10-14 (D62); split into Input, Process and Output with two standard formats on 2026-10-14 (D63, §8); `review` split from `assign` into its own command and core module on 2026-10-21 (D64). User-facing text is Vietnamese (D12) and quoted exactly as the
bot writes it. `<n>` is an order's STT, `<Mã>` a dev code, dates are `DD/MM/YYYY`, hours are whole numbers.

| § | Contents |
|---|---|
| 1 | Commands |
| 2 | Source: the internal system API |
| 3 | Run day, base day, remaining days |
| 4 | Risk register |
| 5 | Memory: AI answers and passed reviews |
| 6 | Report (removed) |
| 7 | `review` and `assign`: one order file, two commands, one Markdown report |
| 8 | Three steps and two standard formats: Input, Process, Output, AI |

---

## 1 · Commands

One program, `scrumbot`, with two sub-commands run on the same order file (D60, D62, D64). BA/MO run them when they
file an order (D61):

1. **`review <file>`** reads the system (§2), places the order file in the running sprint and reviews it (§7.3): the
   fixed checks, then, when they pass, the AI's questions. It writes `<--out>/output.md` and, when the order is ready,
   remembers that this order passed (§5).
2. **`assign <file>`** reads the system again, places the order, and assigns it (assignment spec §7) only when that
   order, unchanged, passed `review` before (§7.4, A101); it builds the risk register (§4) and writes
   `<--out>/output.md` (§7.4), replacing the review's.

`scrumbot` without a sub-command prints the usage and exits `2` (A91). `run`, its Excel report and the memory between
runs were removed on 2026-10-14 (D62); they are in git history at `754b165`. Both commands take the same options:

| Option | Default | Meaning |
|---|---|---|
| `--sprint-id ID` | the running sprint (§2.3) | The sprint the order is placed in. |
| `--input DIR` | `input/` | Where `devs.xlsx` and the TM rules file are found (assignment spec §2). |
| `--devs FILE` | `input/devs.xlsx` | Dev workbook (assignment spec §4). |
| `--rules FILE` | the only `*.md` in `--input` | TM rules (assignment spec §14). |
| `--today DATE` | the clock | Run day (A35). |
| `--state DIR` | `state/` | AI answers, passed reviews and list cache (§5). |
| `--out DIR` | `output/` | Where `output.md` goes. |
| `--ai gemini\|agy\|off`, `--ai-model`, `--ai-timeout` | `gemini`, none, 180 s | The AI tool: the questions of `review` (§7.3), the sizes of `assign` (assignment spec §6.4). |
| `-v` | off | Traceback and the AI exchange on errors. |

Exit codes are those of assignment spec §11. An API error (§2.2) is exit `2`; so is `assign` on an order without a
passed review (§7.4).

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

**History** (familiarity, assignment spec §6.1) is every root task of list Tech manager and of every Maintain sprint,
once per `id`. Its sprints are the Maintain sprints whose `don` lists it, quoted by their label (A25); its filing day is
`ngay_tao`; its hours are `uoc_luong_gio` (AI examples, A19). The window of assignment spec §5.1 applies unchanged.

**Freshness:** the newest `ngay_cap_nhat` among the items read, shown as `dữ liệu API mới nhất` in `output.md` and
on the terminal (D49).

### 2.6 AI with memory (A67, A79)

The prompt of assignment spec §6.4 also asks, per order, for `type` (one of `ads`, `iap`, `flow_ui`, `policy`, `crash`,
`sdk`, `feature`, `other`), `items` (at most 5 short strings), `tech_risks` (at most 2 short Vietnamese strings, e.g.
a new SDK or a store deadline). A wrong or missing extra key leaves the size untouched. The questions to the person
who filed the order are another call, made by `review` (§7.3, A102). In the report the type reads
`Ads`, `IAP`, `Luồng/UI`, `Policy`, `Crash`, `SDK`, `Tính năng`, `Khác`.

A valid AI answer is remembered by order `id` + title (casefolded); the AI is called only for orders without one.
The order of an `assign` file is the exception: always sized, never remembered (§7.2).
`Độ lớn` then reads, e.g., `AI (agy, 6/6 đơn; 5 từ bộ nhớ)`. Defaults (`M`) are never remembered.

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

## 5 · Memory: AI answers and passed reviews (D62, D64)

`state/scrumbot.sqlite` (A51) holds the AI answers of §2.6 (A67) in `ai_answers` and the passed reviews of §7.3
(A101) in `reviews`: one row per fingerprint, with the order file and the time of the review; a row never expires.
`state/cache/` holds the list cache (§2.3, A58). The AI's questions are never remembered (A90). Kept proposals, the
stored state of orders, outcomes and the `Thay đổi` sheet were removed with `run` (D62). A file written before may
still hold their tables; the bot ignores them.

## 6 · Report (removed 2026-10-14, D62)

The six-sheet Excel report belonged to `run`. The only report is `output.md` (§7.4).

## 7 · `review` and `assign`: one order file, two commands, one Markdown report (D60, D62, D64)

`scrumbot review <file> [options]`, then `scrumbot assign <file> [options]`, e.g. `scrumbot review input/don/req.md
--ai agy`. BA/MO run them when they file an order (D61). `review` answers: is the order ready to be assigned, and
what does the AI find unclear in it (§7.3). `assign` answers, for an order that passed `review`: who takes it, why,
who backs up, and what may go wrong (§7.4). Both place the order in the whole running sprint (§7.2), so the load and
the risks are those of the real sprint plus this order. Both write `<--out>/output.md`; the later run replaces it.

### 7.1 The order file (A82)

A `.md` file, usually in `input/don/` (an order file at the top of `--input` is never taken for the TM rules file).
Read by `input/files/order_md.py`, without AI.

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

### 7.3 `review`: the checks, then the AI's questions (D62, D64, A86–A90, A101–A103)

Right after the order is placed (§7.2), the bot checks the order as placed: an order found on the system has its App,
priority and `Hạn` from the API (A82). An order that already has a `Người làm` is not reviewed (A87). Checks, in this
order (a "file order" is a new order, §7.2 case 3; an "order on the system" is cases 1 and 2):

| Code | Blocks when | Message for a file order | Message for an order on the system |
|---|---|---|---|
| `REVIEW-APP` | App is empty | `Thiếu App: ghi tên app vào dòng App của file đơn.` | `Thiếu App: điền App cho đơn trên hệ thống.` |
| `REVIEW-DUE` | Priority `urgent` or `high` and no `Hạn` | `Đơn <urgent\|high> chưa có Hạn: ghi dòng Hạn của file đơn (YYYY-MM-DD hoặc DD/MM/YYYY).` | `Đơn <urgent\|high> chưa có Hạn: điền Hạn cho đơn trên hệ thống.` |
| `REVIEW-DESC` | The description the AI reads (§7.2), without its `[link …]` and with whitespace collapsed, has fewer than 30 characters (A88) | `Mô tả quá ngắn (<k> ký tự, cần từ 30, không tính link): ghi rõ các hạng mục cần làm.` | the same |

Every `output.md` of `review` starts with the same two lines and ends with a short `Thông tin đơn` table:

```markdown
# Review đơn: <title>

<sprint> (<start> – <end>) · chạy <dd/mm/yyyy HH:MM> · dữ liệu API mới nhất <dd/mm/yyyy HH:MM>

## Review: <chưa đạt|đạt|không cần>

…

## Thông tin đơn

| Trường | Giá trị |
|---|---|
| Đơn | <as §7.4 section 3> |
| File đơn | <file> |
| App | <app or trống> |
| Ưu tiên | <priority or trống> |
| Hạn | <dd/mm/yyyy or trống> |
| Mô tả AI đọc | <§7.2, or không có> |
```

**Not ready** (any check fires): no AI call (A86), nothing remembered; exit `0` (A89). The section reads:

```markdown
## Review: chưa đạt

Sửa các mục dưới đây rồi chạy lại `scrumbot review <file>`:

- `REVIEW-APP`: <message>
```

**Ready** (no check fires): one AI call for this order alone (A102): its title, App, priority and the description the
AI reads (§7.2), cut at 2000 characters. The prompt asks for `{"questions": [...]}`: at most 2 short Vietnamese
questions to the person who filed the order, about what the description leaves unclear for doing the work, an empty
list when nothing is unclear. The questions never block and are never remembered (A90). The bot then remembers the
order's **fingerprint** (§5, A101): its title, `ID`, App, priority, `Hạn` and the description the AI reads, as placed.
Exit `0`. The section reads:

```markdown
## Review: đạt

Câu hỏi của AI cho người lên đơn (không chặn; trả lời trong file đơn nếu cần):

- <question>

Chạy `scrumbot assign <file>` để bot đề xuất PIC. Sửa file đơn sau lần review này thì phải review lại.
```

With no question, the first lines are `AI không có câu hỏi.` when the AI answered with none, else `Không có câu hỏi
của AI (AI tắt hoặc lỗi).` (the AI off, failed, or replied without a readable `questions` list).

**Pre-assigned** (the order has a `Người làm`): no check, no AI call, nothing remembered; exit `0`. The section reads
``Đơn đã có người làm trên hệ thống: bot giữ nguyên, không review. Chạy `scrumbot assign <file>` để xem người làm và
rủi ro.``

**Terminal:** `Ngày chạy: <dd/mm/yyyy> (--today)` when given, `Nguồn: API <host> (dữ liệu mới nhất <…>)`, `Luật TM:
…`, `Lịch sử: API (<n> đơn gốc)`, `Đơn: <title> (đơn mới|đơn trên hệ thống <id>, STT <n> của <sprint>)`; then, not
ready: `Review: chưa đạt (<k> mục)` and one line `- <code>: <message>` per check; ready: `Đang hỏi <tool> về mô tả
đơn…` when the AI is called, `Review: đạt (<q> câu hỏi của AI)` or `Review: đạt (không có câu hỏi của AI: <note>)`
(`tắt AI`, or why the call failed), `Tiếp theo: scrumbot assign <file>`; pre-assigned: `Review: không cần (đơn đã có
người làm)`. Last, `Báo cáo: <path>`.

### 7.4 `assign`: the passed review, then the report (A85, A101)

After the order is placed (§7.2), an order with a `Người làm` is reported as it is (D10, A87). Any other order must
have passed `review` with the same fingerprint (§7.3); the core checks it (§8.2). Without one:

| Input error (exit 2) | Message |
|---|---|
| No passed review for the order as placed (never reviewed, not ready, or the file or the system changed since) | `Đơn chưa qua review, hoặc đã đổi sau lần review đạt gần nhất: review lại '<file>' trước khi giao.` |

Nothing is written then. Otherwise the bot sizes (§2.6), assigns (assignment spec §7) and builds the register (§4).

**`<--out>/output.md`** is written to `output.md.tmp` and renamed; each run replaces the previous file. Sections, in
this order:

1. `# Giao đơn: <title>`, then `<sprint> (<start> – <end>) · chạy <dd/mm/yyyy HH:MM> · dữ liệu API mới nhất <…>`.
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

**Terminal:** the five first lines of §7.3, then `Đang ước lượng độ lớn bằng <tool>… (<n> đơn)` when the AI is
called, `Độ lớn: <size>[ (mặc định)] · <sizing note>`, `PIC đề xuất: <Mã> (dự phòng: …)` or `Đã có người làm: …
(giữ nguyên)`, `Rủi ro liên quan: …`, each WARN finding of the report, and `Báo cáo: <path>`.

## 8 · Three steps and two standard formats (D63)

The bot is three steps joined by two standard formats, plus an AI module that the Process step calls. Whoever
integrates the bot elsewhere (the TM, in the internal system's website) replaces an input adapter, an output adapter
or the AI; the core never changes. Built on 2026-10-14 (0.3.0); the core split into `review` and `assign` on
2026-10-21 (0.4.0, D64).

```
INPUT (replaceable)                  PROCESS (core)                                 OUTPUT (replaceable)
dev API · production API · JSON  ─►  Inputs ─► place ─┬─► review ─► Outcome ─┐
· Excel  (one adapter per source)                      │      ▲ Asker         ├─►  output.md · terminal · JSON · …
                                                       └─► assign ─► Outcome ─┘
                                                              ▲ Sizer, passed reviews
                                     (Asker, Sizer: the AI module, replaceable)
```

### 8.1 Packages (A92)

| Package | Step | Holds | Imports from `scrumbot` |
|---|---|---|---|
| `scrumbot.core` | Process | The two formats (§8.3, §8.4) and `place` (§8.2), with what both steps use in `core.sprint` (§2.3, §2.5, §3, §7.2). Two sub-packages that never import each other (A99): `core.review` (§7.3, the `Asker`) and `core.assign` (§2.6 sizing, assignment spec §7, §4, the report facts of §7.4). No file, network, clock, subprocess or printing; the standard library only. | nothing |
| `scrumbot.input` | Input | One adapter per source, each building `Inputs`: `dev_api` (§2, with the list cache and `.env`) and `files` (`devs.xlsx`, the TM rules `.md`, the order `.md`, discovery in `--input`). | `core` |
| `scrumbot.ai` | AI | The two prompts and their parsing (pure; §2.6, §7.3, assignment spec §6.4), the AI CLI tools `gemini` and `agy` (best practices §4), the memory of answers and passed reviews (§5), `AiSizer` and `AiAsker` (§8.5). | `core` |
| `scrumbot.output` | Output | One adapter per format, each reading `Outcome`: `markdown` (`output.md`, §7.3, §7.4) and `terminal` (the lines of §7.3, §7.4). | `core` |
| `scrumbot.app` | — | `scrumbot review`: `input.local` → `core.place` → `core.review` with `ai.AiAsker` → `output`, then the passed review into `ai.memory`. `scrumbot assign`: `input.local` → `core.place` → `core.assign` with the passed reviews and `ai.AiSizer` → `output`. Hands lines to `say`. | every package |
| `scrumbot.cli` | — | Parses the options, calls `app`, prints, sets the exit code. | `app`, `core` |

`input`, `ai` and `output` never import each other; `core.review` and `core.assign` never import each other, and the
rest of `core` imports neither (its `__init__` re-exports them). `tests/test_boundaries.py` checks every import of
every module against this table, that `core` imports only the standard library, that each kind of I/O has its one owner module
(`openpyxl`: `input/files/devs_xlsx.py`; `urllib.request`: `input/dev_api/client.py`; `sqlite3`: `ai/memory.py`;
`subprocess`: `ai/tools.py`), and that only `cli.py` prints.

### 8.2 The core API (A100)

```python
from scrumbot import core

placed = core.place(inputs, now=now, today=None, sprint_id=None)   # §2.3 sprint, §7.2 place
outcome = core.review(placed, asker=None)                          # §7.3: not_ready, ready or pre_assigned
outcome = core.assign(placed, reviewed=passed, sizer=None)         # §7.4: proposed or pre_assigned
```

- `now` is the run time: the core never reads the clock. `today` is the run day (`--today`); `None` is `now.date()`.
  `sprint_id` is `--sprint-id`.
- `place` checks `Inputs` (§8.3), picks the running sprint and places the order. `placed` carries what the terminal
  prints before the AI is called (§7.3): the source and its freshness, the rules in force, the size of the history,
  the placed order.
- `review` runs the checks of §7.3 and, when they pass, asks `asker` (§8.5) for the questions; a blocked or
  pre-assigned order never reaches `asker`. A `ready` outcome carries `order.fingerprint`, which the caller keeps.
- `assign` raises the input error of §7.4 unless the order has a `Người làm` or its fingerprint is in `reviewed`, any
  container of the fingerprints of passed reviews (the CLI gives its memory, §5; a website gives its own store). It
  never runs the checks again: the same fingerprint gives the same review (A101).
- `asker=None` and `sizer=None` are the AI turned off: no questions, every order `M` with the note `tắt AI (mọi đơn
  M)`, as `--ai off`.
- Every error the user can act on is an `InputError` whose message is a Vietnamese text of this spec or of the
  assignment spec. The core returns an outcome or raises; it never prints and never exits.

### 8.3 Standard input: `Inputs` (A94)

A frozen dataclass of `scrumbot.core`. `Inputs.from_dict(data)` reads its JSON form and `inputs.to_dict()` writes it.
Field names are the same in Python and in JSON. In JSON a date is `"YYYY-MM-DD"` and a time `"YYYY-MM-DDTHH:MM:SS"`
(the system's local time, no zone, as the API writes it); an optional field may be absent or `null`; every text is
NFC-normalised when read; unknown keys are ignored.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `format` | text | ✓ (JSON) | `scrumbot-input/1`. |
| `source` | text | ✓ | Label of the data, printed as `Nguồn: <source>`, e.g. `API devclickup.datlt.site`. |
| `fetched_at` | time | ✓ | When the data was read. |
| `sprints` | list of Sprint | ✓ | Every list of board Maintain; §2.3 picks the sprints among them. |
| `lists` | map: list id → list of Task | ✓ | The items of every list read, every level of the tree: at least every Maintain sprint. A task in several lists appears in each. |
| `history_lists` | list of text | — | Ids of `lists` that are not sprints but count as history (§2.5). The dev API adapter gives list Tech manager, `901609972453`. |
| `status_changes` | list of StatusChange | — | Status history, at least of every item of the running sprint. Without it `STATUS-STUCK` falls back to `updated` and `QA-RETURNS` sees no return to `qa - need fix`. |
| `devs` | list of Dev | ✓ | The dev list (assignment spec §4). |
| `rules` | list of TeamRule | — | The TM rules (assignment spec §14). |
| `rules_source` | text | — | Where the rules came from, quoted in rule errors (`File '<rules_source>', dòng …`) and on the terminal; empty without rules. |
| `order` | Order | ✓ | The order being filed (§7.1). |

**Sprint**: one list of board Maintain (`/api/doc/sprints`).

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | text | ✓ | List id. |
| `name` | text | ✓ | E.g. `Sprint 10 (10/6 - 10/17)`; the number after `Sprint` is the sprint number. |
| `kind` | text | ✓ | `sprint` or `list` (A56). |
| `start`, `end` | date | — | First and last day; a sprint without them never runs. |
| `archived` | yes/no | — | Default no. |
| `total` | number | ✓ | Root orders in the list; a list with 0 is not a Maintain sprint (A56). |

**Task**: one item of a list (`/api/doc/don`): a root order, a subtask or a bug.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | text | ✓ | Item id. |
| `title` | text | ✓ | |
| `parent_id` | text | — | The parent item; empty for a root. A root that is not a bug is an order (D5). |
| `is_bug` | yes/no | — | A bug item, never an order. Default no. |
| `status` | text | — | Status name, e.g. `in progress`. |
| `status_kind` | text | — | `open`, `custom`, `done`, `closed`, or empty when unknown. |
| `assignees` | list of text | — | Full names of `Người làm`, matched with `devs[].name` (A10). |
| `priority_raw` | text | — | `urgent`, `high`, `normal`, `low` or empty, as written. |
| `due` | date | — | `Hạn`. |
| `hours` | number | — | The human estimate: only an AI example on history orders, never a size (D3). |
| `app` | text | — | App name. |
| `created` | time | ✓ | Filing time; orders are numbered by it (A76). |
| `updated`, `closed` | time | — | Last update, closing time. |

**StatusChange**: `task_id` (text, ✓), `new` (text, ✓: the status entered), `at` (time, ✓).

**Dev** (assignment spec §4): `name` (text, ✓; as in `assignees`), `code` (text, ✓), `level` (text, ✓: `junior`,
`junior+`, `middle`, `middle+`, `senior`), `active` (yes/no, ✓: `Nhận việc`), `leave_days` (list of dates).

**TeamRule** (assignment spec §14): `kind` (text, ✓: `Chỉ định`, `Không giao`, `Tối đa đơn`, `Ưu tiên`), `dev` (text,
✓: a `code`), `app` (text), `max_orders` (number), `start`, `end` (dates), `note` (text), `line` (number, ✓: names
the rule in messages and reasons; the line in the rules file, or any number unique among the rules).

**Order** (§7.1): `title` (text, ✓), `order_id` (text: the order's id on the system; empty to match by title or file a
new order, §7.2), `app`, `priority_raw` (text), `due` (date), `description` (text as written; the core removes links
and names before the AI reads it, §7.2), `origin` (text: where the order came from, e.g. the file path; shown as
`File đơn` and in the not-ready line of `output.md`).

**Checks.** A JSON form that does not fit is the input error `Dữ liệu đầu vào không đúng dạng: <path>: <problem>.`,
where `<path>` reads like `devs[2].level` or `lists[<list id>][3].created` and `<problem>` is `thiếu`, `không phải
<kind>` (`chữ`, `số nguyên`, `số`, `đúng/sai`, `danh sách`, `bảng`, `ngày YYYY-MM-DD`, `thời điểm YYYY-MM-DDTHH:MM:SS`) or
`'<value>' không hợp lệ` (a level or a rule kind). A top level that is not an object is `Dữ liệu đầu vào không đúng
dạng: không phải bảng.`; a missing `format` is `Dữ liệu đầu vào không đúng dạng: format: thiếu.`; another one is `Dữ
liệu đầu vào không đúng dạng: format '<value>', cần scrumbot-input/1.` On every `Inputs`, whatever adapter built it, `place` checks before anything else, in this order:
no dev (`Dữ liệu đầu vào không có dev nào.`), a dev name or code used twice (`Dữ liệu đầu vào trùng tên dev '<name>'.`,
`Dữ liệu đầu vào trùng mã dev '<code>'.`, compared like names, A10), then the rules against the devs (assignment spec
§14.2, `rules_source` standing for the file name). The file adapter keeps its own messages with row numbers
(assignment spec §4), so these fire only for another adapter; the file adapter also checks the rules against the
devs before any API call, so that a mistake in the files never waits for the API.

### 8.4 Standard outcome: `Outcome` (A95, A104)

A frozen dataclass of `scrumbot.core`; `outcome.to_dict()` gives its JSON form, with the value formats of §8.3. Texts
are the Vietnamese texts of this spec. A code (`REVIEW-…`, a risk code, a finding code) never changes once released,
so another output may show its own words for a code.

| Field | Type | Meaning |
|---|---|---|
| `format` | text | `scrumbot-outcome/2` (JSON only; `/1` before D64). |
| `status` | text | From `review`: `not_ready` (§7.3 blocks), `ready` (nothing blocks) or `pre_assigned`. From `assign`: `proposed` (the bot proposes a PIC) or `pre_assigned`. `pre_assigned`: the order has a `Người làm` and is kept (D10). |
| `run_at` | time | The run time; with `--today`, that day at the time of `now`. |
| `source`, `freshness` | text, time | `Inputs.source`; the newest `updated` read (D49), may be empty. |
| `sprint` | object | `id`, `name`, `start`, `end`, `previous` (the previous sprint's name, §2.3; `sprint trước` without one). |
| `order` | object | `title`, `stt`, `id` (empty for a new order), `placement` (`new`, `id` or `title`, §7.2), `origin`, `app`, `priority_raw`, `due`, `description` (as the AI read it, §7.2), `fingerprint` (§7.3, A101: 16 hex digits). |
| `review` | list of {`code`, `message`} | The blocking items of §7.3; empty unless `not_ready`. |
| `questions` | object or null | `review` only, null otherwise and for `not_ready` and `pre_assigned`: `items` (at most 2 texts), `answered` (the AI answered, even with no question), `note` (`AI (<tool>)`, `tắt AI`, or why the call failed). |
| `assignment` | object or null | Null for a `review` outcome. `pic_codes` (`proposed`: the PIC; `pre_assigned`: the pool devs holding it, may be empty), `pic_names`, `reason` (assignment spec §8), `backups` (at most 2 codes; empty for `pre_assigned`), `rule_lines` (the TM rules that shaped the choice), `rules_relaxed` (A31). |
| `size` | object or null | Null for a `review` outcome. `size` (`S`, `M`, `L`, `XL`), `hours` (4, 16, 32, 64), `is_default` (`M` because the AI was off or failed), `reason`, `kind` and `kind_label` (the AI type and its label, §2.6), `items`, `tech_risks`, `remembered`, `note` (the sizing note of the run, e.g. `AI (agy, 6/6 đơn; 5 từ bộ nhớ)`). |
| `risks` | list of Risk | The risks of this order, of its PIC and of the sprint (§7.4), in register order: `level` (`high`, `medium`, `low`), `level_text` (`Cao`, `Trung bình`, `Thấp`), `code`, `group` (`Năng lực`, `Phân công`, `Tiến độ`, `Chất lượng`), `where`, `problem`, `impact`, `action`, `if_it_happens` (§7.4), `owner`, `due`, `stt`. Empty for a `review` outcome. |
| `sprint_risks` | {`high`, `medium`, `low`} | Counts over the whole register; zeros for a `review` outcome. |
| `devs` | list of DevLine | The dev table of §7.4: `code`, `level`, `familiarity`, `orders`, `open_hours`, `capacity` (null without sprint dates), `carry_over`, `leave_days`, `role`. Empty for a `review` outcome. |
| `findings` | list of {`severity`, `code`, `where`, `message`} | `severity` `WARN` or `INFO`; every finding except those about another order (§7.4). Empty for a `review` outcome. |

`output.md` is built from `Outcome` alone, and the terminal lines from `placed` and `Outcome`. The `Nếu xảy ra`
sentences (§7.4) and the labels of the AI types (§2.6) move from the Markdown writer into the core, so every output
shows the same words.

### 8.5 The AI module (A96, A102)

The core sees the AI as two callables, one per step:

- **`asker(row) -> Questions`** for `review` (§7.3): `row` is the filed order as placed, its description already
  scrubbed (§7.2). `Questions` holds `items` (at most 2), `answered` and `note` (§8.4). An asker never raises for an
  AI failure: it returns no question, `answered` false and why in the note.
- **`sizer(orders, examples, fresh) -> Sizing`** for `assign`: `orders` are the sprint's orders, the filed order's
  description already scrubbed; `examples` are the history orders of the window (assignment spec §5.1); `fresh`
  holds the STTs that must be sized by this call and never remembered (§2.6). `Sizing` holds a `SizeEstimate` per
  STT, the findings of the AI reply and the sizing note. A sizer never raises for an AI failure: it sizes the orders
  `M` and says why in the note. An order the sizer leaves out is sized `M` by the core.

`scrumbot.ai` gives today's two, `AiAsker(ask, tool=…, say=…)` and `AiSizer(ask, tool=…, now=…, memory=…, say=…)`;
`tool` names the AI in the notes and the memory, `now` is the run time stored with an answer:

- `ask(prompt) -> AiReply` is one AI call. `ai.tools.cli_ask(tool, model, timeout)` runs `gemini` or `agy` as now
  (best practices §4). Another AI (an HTTP API, another vendor) is another `ask`; the prompts, their parsing and the
  memory stay as they are.
- `memory` is the SQLite store of §5, or `None` for no memory. The asker has none (A90).
- `say` receives `Đang hỏi <tool> về mô tả đơn…` (asker) or `Đang ước lượng độ lớn bằng <tool>… (<n> đơn)` (sizer)
  before the call.

What reaches the AI does not change: titles, App, priority, the history's titles and hours and the scrubbed
description (A18, A83); never a name, a code or a link.

### 8.6 What does not change

`scrumbot assign` keeps its options, its exit codes, its files on disk and, but for the `## Review: đạt` section and
the `Review: đạt` terminal line that moved to `review` (A103), its terminal lines and `output.md` byte for byte (A97).
The adapter `input.dev_api` still reads only the dev server and refuses production (D49, A64): reading production is
another adapter, written by whoever integrates the bot. A JSON entry point for a website not written in Python is
open (O15).
