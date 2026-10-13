# Bot spec: `scrumbot`

What the scrum-master bot adds on top of the assignment core of [`assignment-spec.md`](assignment-spec.md): reading
the internal system's API, the risk register, the change log and memory between runs. [`LLM.md`](../LLM.md) says where each part lives in code;
[`confirm.md`](../confirm.md) holds the decisions cited here (`Dn` user-locked, `An` defaults, `On` open).

**Status:** written 2026-10-13 for stage 1 (D57); scope cut the same day (D59). User-facing text is Vietnamese (D12) and quoted exactly as the
bot writes it. `<n>` is an order's STT, `<Mã>` a dev code, dates are `DD/MM/YYYY`, hours are whole numbers.

| § | Contents |
|---|---|
| 1 | Commands |
| 2 | Source: the internal system API |
| 3 | Run day, base day, remaining days |
| 4 | Risk register |
| 5 | Change log and memory between runs |
| 6 | Report |

---

## 1 · Command

One program, `scrumbot`, with one sub-command, `run` (D59). Without a sub-command it runs `run`. A run reads the system
(§2), assigns (assignment spec §7), builds the risk register (§4), compares with the memory (§5) and writes the report
to `--out` (§6).

| Option | Default | Meaning |
|---|---|---|
| `--sprint-id ID` | the running sprint (§2.3) | The sprint to assign. |
| `--input DIR` | `input/` | Where `devs.xlsx` and the TM rules file are found (assignment spec §2). |
| `--devs FILE` | `input/devs.xlsx` | Dev workbook (assignment spec §4). |
| `--rules FILE` | the only `*.md` in `--input` | TM rules (assignment spec §14). |
| `--today DATE` | the clock | Run day (A35). A run with `--today` neither reads nor writes the memory of §5.2 (A66). |
| `--state DIR` | `state/` | Memory and list cache. |
| `--out DIR` | `output/` | Where the report goes. |
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
| description | none: the API has none (D50) |

Status kinds for names found only in the history (renamed statuses) come from every status table read in the run
(A74); an unknown name has no kind.

**History** (familiarity, assignment spec §6.1) is every root task of list Tech manager and of every Maintain sprint,
once per `id`. Its sprints are the Maintain sprints whose `don` lists it, quoted by their label (A25); its filing day is
`ngay_tao`; its hours are `uoc_luong_gio` (AI examples, A19). The window of assignment spec §5.1 applies unchanged.

**Empty orders outside sprints** (A65): roots of list Tech manager with no `nguoi_lam_ids`, a status kind other than
`done`/`closed`, in no Maintain sprint. Counted in `Tóm tắt`, nothing else.

**Freshness:** the newest `ngay_cap_nhat` among the items read, shown as `Dữ liệu mới nhất` (D49).

**Description note** (D50): when the AI sizes at least one order without a description, the run logs and writes in
`Tóm tắt`: `Hệ thống chưa trả mô tả: <k> đơn được ước lượng chỉ theo tiêu đề.` (`k` = orders with an AI size, from the
AI call or the cache, that have no description).

### 2.6 AI with memory (A67, A79)

The prompt of assignment spec §6.4 also asks, per order, for `type` (one of `ads`, `iap`, `flow_ui`, `policy`, `crash`,
`sdk`, `feature`, `other`), `items` (at most 5 short strings) and `tech_risks` (at most 2 short Vietnamese strings, e.g.
a new SDK or a store deadline). A wrong or missing extra key leaves the size untouched. In the report the type reads
`Ads`, `IAP`, `Luồng/UI`, `Policy`, `Crash`, `SDK`, `Tính năng`, `Khác`.

A valid AI answer is remembered by order `id` + title (casefolded); the AI is called only for orders without one.
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
| PIC | The pool devs on the order: the TM's for a pre-assigned order, the bot's for a proposal (kept or new). |
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
| 9 | `ORDER-CHANGED` | Thay đổi | Thấp (+1) | Priority, due date or title differs from the stored state (§5.1) |
| 10 | `STATUS-STUCK` | Tiến độ | Trung bình (+1) | The order or a subtask stays in a status longer than its A49 threshold |
| 11 | `QA-RETURNS` | Chất lượng | Trung bình (+1) | A not-done order went back to `qa - need fix` ≥ 2 times, has ≥ 5 bugs, or has open bugs with `k` ≤ 3 |

Risks 1 and 12 are postponed (D53). Columns of each row: `Vấn đề` (problem), `Ảnh hưởng` (impact), `Đề xuất` (action),
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

**`ORDER-CHANGED`** — where `Đơn STT <n>`; owner `TM`. API runs with a stored state only.
- Problem: `Đơn STT <n> đổi ` + the changes joined with `; `: `ưu tiên <old> → <new>`, `hạn <old> → <new>`,
  `tên "<old>" → "<new>"` (an empty value reads `trống`).
- Impact: `Độ lớn, PIC hoặc kế hoạch có thể cần xem lại.`
- Action: `Báo <PIC>; xem lại độ lớn và hạn.`; no PIC: `Xem lại độ lớn và hạn.`

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

## 5 · Change log and memory between runs

The memory is one SQLite file, `state/scrumbot.sqlite` (A51), used only by API runs on live data of today (A66).

### 5.1 Stored state and `ORDER-CHANGED` (A62)

At the end of each such run the bot stores, per order of the sprint, its title, priority, due date and pool codes,
dated today. Risk 9 and the `Thay đổi` sheet compare with the **latest state stored before today**.

### 5.2 Kept proposals (A66)

A proposal is remembered (order `id` → dev code, reason, backups, time) until the order has a `Người làm` in the system.
The next run keeps it as long as that dev is still in the pool (not off every remaining day, `Nhận việc` = `Y`): the
order counts as proposed for that dev before §7 runs, and its reason starts with `Giữ đề xuất từ <dd/mm/yyyy HH:MM> · `
followed by the stored reason. A kept proposal whose dev left the pool is dropped and §7 runs again.

When an order with a remembered proposal gets a `Người làm`, the bot records an outcome: the proposed code, the pool
codes now, and whether they match.

### 5.3 Sheet `Thay đổi`

Columns `Loại` · `Đơn` · `Trước` · `Sau`. `Đơn` is `STT <n> · <title>`. The first row is `So với dữ liệu lưu lúc
<dd/mm/yyyy HH:MM>`, or `Chưa có lần chạy trước để so` when nothing of this sprint was stored before today, or
`Không so khi chạy với --today.` for a run that does not use the memory; when nothing changed, a
second row `Không có thay đổi`.

| `Loại` | When | `Trước` → `Sau` |
|---|---|---|
| `Đơn mới` | Order not in the stored state | — → `<title> [<size>]` |
| `Đơn bị bỏ` | Stored order no longer in the sprint | `<title>` → — |
| `Đổi ưu tiên` | Priority differs | old → new (`trống` when empty) |
| `Đổi hạn` | Due date differs | old → new |
| `Đổi tên` | Title differs | old → new |
| `TM đã giao` | An outcome recorded today (§5.2) | proposed code → `<codes now> (khớp)` or `(khác đề xuất)` |
| `Đổi người làm` | Pool codes on the order differ from the stored state, not already a `TM đã giao` row | old codes → new codes |

Codes only, never names; a change between people outside the pool is not shown (D14).

## 6 · Report

`assignment_<sprint slug>_<YYYYMMDD-HHMMSS>.xlsx` (assignment spec §10), with six sheets in this order (A76):

1. **`Tóm tắt`**: columns `Mục` · `Nội dung`; rows `Sprint` (`<label> (<start> – <end>)`), `Ngày chạy`
   (`<dd/mm/yyyy HH:MM>`, plus ` (--today)` when given), `Nguồn` (`API <host>`),
   `Dữ liệu mới nhất` (API), `Độ lớn`, `Mô tả đơn` (the D50 note, when it applies), `Đơn` (`<n> đơn · giao sẵn <a> ·
   bot đề xuất <b> (mới <c>, giữ từ lần trước <d>)`), `Rủi ro` (`<x> cao · <y> trung bình · <z> thấp`), `Cảnh báo dữ
   liệu` (`<w> WARN · <i> INFO`), `Thay đổi` (`<k> dòng`, or the first-row text of §5.3), `Đơn trống chưa vào sprint`
   (API: `<m> đơn ở list Tech manager, <r> đơn tạo trong 30 ngày gần đây`, A65), then one `Rủi ro cao` row per `Cao`
   risk: `<code> · <where>: <problem>`.
2. **`Phân công`**: as assignment spec §10. The input columns are `STT` · `ID` · `Task` · `App Name` · `Trạng
   thái` · `Người làm` · `Ưu tiên` · `Hạn` · `Ngày tạo` · `Bug mở` · `Bug tổng`. The bot's columns are `Độ lớn` · `Giờ
   ước tính` · `Lý do độ lớn` · `Loại đơn (AI)` · `Hạng mục (AI)` · `Rủi ro kỹ thuật (AI)` · `PIC` · `Mã PIC` ·
   `Nguồn` · `Lý do` · `Dự phòng 1` · `Dự phòng 2` · `Rủi ro` (the codes of the order's risks).
3. **`Rủi ro`**: `Mức` · `Mã` · `Nhóm` · `Vị trí` · `Vấn đề` · `Ảnh hưởng` · `Đề xuất` · `Ai xử lý` · `Hạn xử lý`; an
   empty register writes one row `Không có rủi ro`.
4. **`Thay đổi`**: §5.3.
5. **`Cảnh báo`**: as assignment spec §10.
6. **`Tải dev`**: as assignment spec §10, plus `Sức chứa còn lại (h)` and `Giờ việc còn lại (h)` (empty when the sprint
   has no dates).

**Terminal** (assignment spec §11) also prints `Nguồn: …` (with `dữ liệu mới nhất <date time>` for the API), the D50
note, `Rủi ro: <x> cao · <y> trung bình · <z> thấp`, one line `CAO <code> <where>: <problem>` per `Cao` risk, and
`Thay đổi: <k> dòng`.
