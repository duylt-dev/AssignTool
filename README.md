# scrumbot

Bot scrum master cho team Android. **BA/MO chạy bot khi lên đơn** (D61): bot đọc đơn trong file `.md`, đọc sprint đang
chạy của board Maintain từ API chỉ-đọc của hệ thống nội bộ (server **dev**), rồi làm **ba việc**:

1. **Review đơn** (`scrumbot review <file đơn>`) theo quy trình Sprint Tech (D65): thiếu trường bắt buộc (App,
   version trong tiêu đề, Hạn, người chịu trách nhiệm, bằng chứng của đơn khẩn cấp, mục "Nghiệm thu khi") hoặc mô tả
   quá ngắn thì bot dừng, chỉ ghi những gì cần bổ sung; đủ thì AI chấm mô tả theo mẫu của loại đơn (thiếu ý cũng dừng)
   và hỏi tối đa 2 câu.
2. **Đề xuất PIC** (`scrumbot assign <file đơn>`, chỉ cho đơn đã review đạt và chưa sửa sau đó) kèm lý do và 2 người
   dự phòng.
3. **Báo rủi ro** (cũng trong `assign`) của đơn, của PIC và của cả sprint: quá tải, trễ hạn, kẹt trạng thái, QA trả
   về nhiều, PIC vắng.

Hai lệnh chạy lần lượt trên cùng một file đơn, cả hai ghi **`output/output.md`** (lệnh sau ghi đè). Bot không chạy
theo lịch. Đơn có PIC đề xuất thì **người lên đơn** nhập PIC vào hệ thống, vì bot chưa ghi được gì vào hệ thống.

> **Đơn** = task gốc trên board Maintain, ứng với một version của một app. **Pool** = 4 dev Android có
> `Nhận việc` = `Y` trong `input/devs.xlsx`. QA, RnD và TM không bao giờ được đề xuất.

## 1. Mục tiêu và phạm vi

| | Nội dung |
|---|---|
| **Làm** | Review một đơn BA/MO viết trong file `.md` theo quy trình Sprint Tech (`review`) · đề xuất PIC và sổ rủi ro 9 mã (`assign`) · `output/output.md` (D60, D62, D64, D65) |
| **Không làm** | Ghi vào hệ thống · giao bug hoặc subtask · đổi đơn đã có người làm · báo gì về người ngoài pool · đọc server production |
| **Đã bỏ** | 13/10/2026 (D59): chạy theo lịch 30 phút, báo cáo cuối sprint, clone + replay sprint cũ, chạy bằng file export Excel, bộ đánh giá `eval/` (git `7b2fa0d`). 14/10/2026 (D62): lệnh `run`, báo cáo Excel 6 sheet, bộ nhớ đề xuất giữa các lần chạy, rủi ro `ORDER-CHANGED` (git `754b165`). |

**Lộ trình:**

| Giai đoạn | Trạng thái | Nội dung |
|---|---|---|
| GĐ 1 | **Xong** (14/10/2026) | Đọc API dev, review đơn, giao PIC, sổ rủi ro 9 mã. Đo lần cuối (replay 29 sprint, 13/10): khớp TM 64% số đơn; sổ rủi ro báo trước 82% đơn có kết cục xấu. |
| Bàn giao core | **Xong** (14/10/2026, 0.3.0) | Tách bot thành Input → Process → Output, cộng module AI, nối bằng 2 định dạng chuẩn (`scrumbot-input/1`, `scrumbot-outcome/1`) để TM tích hợp core vào website (D63, mục 4 và 6 dưới đây). Lệnh `assign` không đổi: `output.md` giống từng byte. |
| Tách review | **Xong** (21/10/2026, 0.4.0) | Review là lệnh và module riêng (`core.review`), `assign` chỉ chạy cho đơn đã review đạt; câu hỏi của AI chuyển sang review; định dạng `scrumbot-outcome/2` (D64). |
| Review theo quy trình | **Xong** (21/10/2026, 0.5.0) | Review theo quy trình Sprint Tech (`rule.html`, 19/10/2026): thêm 4 mục chặn cố định, AI chấm mô tả theo 8 mẫu loại đơn và chặn khi thiếu ý; file đơn có thêm `Loại đơn`, `Người chịu trách nhiệm`, `Bằng chứng`; định dạng `scrumbot-input/2`, `scrumbot-outcome/3` (D65). Phần còn lại của quy trình (buffer 5%, đơn khẩn cấp ≤ 8 giờ, ai phân công) chưa đưa vào `assign` (O16). |
| GĐ 2 | Chờ hệ thống | Ghi PIC vào hệ thống khi có API ghi (O8). Rủi ro 1 và 12 cho cả sprint khi API trả mô tả đơn (D53). Đơn RnD mặc định về DuyLT khi hệ thống có tag loại đơn (D58). |

## 2. Cách bot làm việc

```
INPUT                               XỬ LÝ                                       OUTPUT
file đơn .md của BA/MO       ─┐     Cả hai lệnh: đặt đơn vào sprint đang chạy
API dev /api/doc/ (chỉ GET)  ─┤     scrumbot review                      ──►   output/output.md
  sprints · don · lich-su     │       1. Check cố định: thiếu gì thì dừng      (review, hoặc PIC và rủi ro)
input/devs.xlsx              ─┼──►    2. AI chấm mẫu loại đơn, hỏi 2 câu   ──►  Tóm tắt trên terminal
                              │          (thiếu ý thì dừng); đạt thì ghi nhớ
input/<luật TM>.md (tuỳ ý)   ─┘     scrumbot assign (đơn đã review đạt)
                                      3. AI ước lượng độ lớn S/M/L/XL
                                      4. Giao PIC theo luật cố định
                                      5. Sổ rủi ro (9 mã)
```

**AI chấm mô tả theo mẫu loại đơn, đặt câu hỏi cho người lên đơn và ước lượng độ lớn đơn.** Các mục chặn cố định của
review, ai làm đơn nào và rủi ro mức nào đều do luật cố định quyết định, nên lần nào chạy cũng ra cùng kết quả và giải
thích được bằng một câu. Riêng phần chấm mẫu là AI quyết (D65), nên cùng một file có thể lúc đạt lúc không. AI lỗi
hoặc tắt thì review không chấm mẫu, mọi đơn tính là `M` (16 giờ) và lần chạy vẫn tiếp tục.

### 2.1 Review đơn

| Mã | Bot dừng khi |
|---|---|
| `REVIEW-APP` | Đơn không có App |
| `REVIEW-TITLE` | Tiêu đề không có version (`1.0.3`, `v1.0.3`) |
| `REVIEW-DUE` | Đơn không có Hạn |
| `REVIEW-OWNER` | File đơn không có dòng Người chịu trách nhiệm |
| `REVIEW-EVIDENCE` | Đơn urgent/high (Khẩn cấp) không có Bằng chứng |
| `REVIEW-DESC` | Mô tả dưới 30 ký tự (không tính link) |
| `REVIEW-ACCEPT` | Mô tả không có mục "Nghiệm thu khi" |
| `REVIEW-TEMPLATE` | AI thấy mô tả thiếu ý của mẫu loại đơn (8 loại của quy trình, trừ ý "Tài liệu") |

`scrumbot review` chạy 7 check cố định trước. Còn thiếu thì `output.md` chỉ ghi những gì cần sửa, bot không gọi AI;
sửa file đơn rồi review lại. Đủ thì AI xếp loại đơn (hoặc lấy dòng `Loại đơn` của file), chấm mô tả theo mẫu của loại
đó và hỏi tối đa 2 câu (câu hỏi chỉ để nhắc). Thiếu ý của mẫu là chưa đạt; đạt thì bot ghi nhớ đơn đã đạt.
`scrumbot assign` chỉ chạy khi đơn, đúng như lúc đó, đã review đạt: sửa file đơn (hoặc App, Hạn trên hệ thống đổi) thì
phải review lại. Đơn đã có người làm trên hệ thống thì không review, `assign` vẫn báo người làm và rủi ro.
Chi tiết: [`docs/bot-spec.md`](docs/bot-spec.md) §7.3, §7.4.

### 2.2 Giao PIC

1. Đơn đã có người làm thì **giữ nguyên**; độ lớn của nó chỉ cộng vào tải của dev đó.
2. Đơn trống được xét lần lượt: ưu tiên → hạn → ngày tạo.
3. Ứng viên là pool, trừ dev bị luật TM loại. Chỉ xét dev đang giữ không quá **số đơn của người ít đơn nhất + 1**,
   để không ai ôm hết.
4. Chọn dev tốt nhất theo thứ tự: luật `Ưu tiên` của TM → **quen app** (làm version gần nhất > từng làm > chưa làm) →
   đơn gấp hoặc app mới thì cần middle trở lên → ít giờ tải hơn → ít việc dở hơn → ít ngày nghỉ hơn → level cao hơn.
5. Mỗi đề xuất có **lý do** một câu và **2 người dự phòng**. Bot không nhớ đề xuất: người lên đơn nên nhập PIC vào
   hệ thống ngay, để lần chạy sau tính đúng tải.

Chi tiết: [`docs/assignment-spec.md`](docs/assignment-spec.md) §7.

### 2.3 Sổ rủi ro

Rủi ro **chỉ khuyên**: không đổi PIC, không đụng đơn đã giao, không đổi mã thoát. Mỗi dòng ghi vấn đề, ảnh hưởng,
cách phòng ngừa, việc cần làm nếu xảy ra, ai xử lý, hạn xử lý.

| Nhóm | Mã | Bật khi |
|---|---|---|
| Năng lực | `CAPACITY-DEV` | Giờ việc còn lại của một dev vượt sức chứa (6h × ngày làm việc còn lại, trừ ngày nghỉ) |
| | `CAPACITY-SPRINT` | Tải cả sprint vượt sức chứa cả team; bot đề xuất đơn nên đẩy sang sprint sau |
| | `SCOPE-ADDED` | Quá tải, nhưng bỏ các đơn thêm vào giữa sprint thì vừa |
| | `CARRY-OVER` | Dev còn việc dở từ sprint trước và đang có đơn mở |
| Phân công | `PIC-UNFAMILIAR` | Đơn urgent/high giao cho người chưa làm app đó |
| | `PIC-ABSENT` | Mọi dev của đơn nghỉ hết các ngày còn lại |
| Tiến độ | `DUE-AT-RISK` | Quá hạn, hoặc còn ≤ 3 ngày mà chưa bắt đầu / còn nhiều subtask |
| | `STATUS-STUCK` | Đơn hoặc subtask nằm một trạng thái quá ngưỡng |
| Chất lượng | `QA-RETURNS` | Bị QA trả về từ 2 lần, có từ 5 bug, hoặc còn bug mở sát hạn |

Ngưỡng và mức: [`docs/bot-spec.md`](docs/bot-spec.md) §4.

## 3. Cài đặt và chạy

Cách cài cho BA/MO (file `.whl`, thư mục làm việc, token, AI): [`HOW_TO_USE.md`](HOW_TO_USE.md) mục 1.

```bash
scrumbot review input/don/<file đơn>.md                  # bước 1, dùng gemini (mặc định) để chấm mẫu và hỏi
scrumbot assign input/don/<file đơn>.md                  # bước 2, sau khi review đạt
scrumbot review input/don/<file đơn>.md --ai off         # không gọi AI: không chấm mẫu, không có câu hỏi
scrumbot assign input/don/<file đơn>.md --ai off         # không gọi AI: mọi đơn tính là M
scrumbot assign input/don/<file đơn>.md --ai agy --ai-timeout 400
scrumbot assign --help                                   # mọi tuỳ chọn (giống nhau cho hai lệnh)
```

Trong repo thì thêm `uv run` phía trước. Lần chạy đầu trên một máy, AI phải ước lượng mọi đơn của sprint (với `agy`
khoảng 5–6 phút cho 7 đơn); bot nhớ câu trả lời theo ID và tên đơn (A67), nên các lần sau chỉ còn đơn trong file và
các đơn mới hoặc đổi tên. Đơn chưa đạt review thì bot không gọi AI nên xong ngay; đơn đạt thì `review` gọi AI một
lần cho riêng đơn đó. Lỗi API, lỗi input, hoặc `assign` khi đơn chưa review đạt dừng lần chạy với mã thoát `2` và một
câu tiếng Việt nói rõ lỗi.

## 4. Flow 3 module: Input → AI → Output

Bot gồm 3 module nối quanh một **core** giữ toàn bộ luật. Core không đọc file, không gọi mạng, không gọi AI trực tiếp:
nó nhận một object chuẩn, gọi AI qua một hàm được đưa vào, và trả một object chuẩn. Nhờ vậy thay được từng module mà
không đụng tới luật.

```
INPUT   scrumbot.input   file đơn .md · devs.xlsx · luật TM .md · API dev
  │
  ▼ core.Inputs (JSON scrumbot-input/2)
CORE    scrumbot.core    place:  chọn sprint, đặt đơn (cả hai bước dùng chung)
  │                      review: check cố định (chưa đạt: dừng, không gọi AI) ─► AI chấm mẫu, hỏi
  │                      assign: chỉ đơn đã review đạt ─► độ lớn ─► giao PIC ─► sổ rủi ro
  │                                  │  ▲
  │    đơn + lịch sử, không tên/link ▼  │ loại đơn, ý thiếu, câu hỏi (asker); S/M/L/XL, hạng mục, rủi ro kỹ thuật (sizer)
  │                      AI  scrumbot.ai: gemini · agy · AI khác · tắt = không chấm mẫu, không câu hỏi, mọi đơn M
  ▼ core.Outcome (JSON scrumbot-outcome/3)
OUTPUT  scrumbot.output  output/output.md · terminal · JSON, trang web, … (adapter tự viết)
```

| Module | Nhận | Trả | Thay được bằng |
|---|---|---|---|
| **Input** (`scrumbot.input`) | File đơn, `devs.xlsx`, luật TM, API dev | `core.Inputs` | API production, JSON, database, form trên website, … |
| **AI** (`scrumbot.ai`) | Đơn đã che tên và link, các mẫu loại đơn, đơn lịch sử làm ví dụ | Kết quả chấm mẫu và câu hỏi cho đơn của file (`core.AiReview`), độ lớn từng đơn (`core.Sizing`) | AI CLI khác, API của nhà cung cấp khác, hoặc tắt (không chấm mẫu, không câu hỏi, mọi đơn `M`) |
| **Output** (`scrumbot.output`) | `core.Outcome` | `output/output.md`, các dòng terminal | JSON, trang web, tin nhắn, … |
| Core (`scrumbot.core`) | `Inputs` và AI | `Outcome` | Không thay: review, PIC và rủi ro đều nằm ở đây |

Ba module chỉ import `scrumbot.core`, không import lẫn nhau; core chỉ dùng thư viện chuẩn Python, và hai module con
`core.review`, `core.assign` không import nhau ([`tests/test_boundaries.py`](tests/test_boundaries.py) kiểm tra). Đơn
chưa đạt check cố định thì core không gọi AI; `core.assign` từ chối đơn chưa review đạt.

### 4.1 Input

**Là gì.** Mọi thứ core cần, gói trong một object `core.Inputs` (dạng JSON `scrumbot-input/2`):

| Phần | Nội dung | Bắt buộc | `scrumbot assign` lấy từ |
|---|---|---|---|
| `order` | Đơn đang lên: tên, ID, App, ưu tiên, hạn, mô tả, loại đơn, người chịu trách nhiệm, bằng chứng | ✓ | File đơn `.md` |
| `devs` | Tên, mã, level, nhận việc, ngày nghỉ của từng dev | ✓ | `input/devs.xlsx` |
| `rules`, `rules_source` | Luật TM và nơi lấy luật | | File luật `.md` trong `input/` |
| `sprints` | Các list của board Maintain: tên, ngày đầu, ngày cuối, đã lưu trữ chưa | ✓ | API dev `sprints` |
| `lists`, `history_lists` | Đơn, subtask, bug của từng list; list nào ngoài sprint vẫn tính là lịch sử | ✓ | API dev `don` (cả list Tech manager) |
| `status_changes` | Lịch sử đổi trạng thái | | API dev `lich-su` |
| `source`, `fetched_at` | Nhãn nguồn dữ liệu, lúc đọc | ✓ | `API <host>` |

**File đơn** (đặt trong `input/don/`, đọc **không dùng AI**):

```markdown
# Game Emulator v1.2.0 - Chỉnh sửa và bổ sung luồng auto scan game

| Trường | Giá trị |
|---|---|
| ID | |
| App | Game Emulator |
| Ưu tiên | normal |
| Hạn | 30/10/2026 |
| Loại đơn | Tính năng |
| Người chịu trách nhiệm | TaiDT – BA |

Mô tả theo mẫu của loại đơn: mục tiêu, hiện trạng, mong muốn, …, Nghiệm thu khi: …, link SRS, link Figma, …
```

Có `ID` thì bot lấy đơn đó trên hệ thống và chỉ thêm mô tả, loại đơn, người chịu trách nhiệm và bằng chứng; không có `ID` mà tên trùng một đơn trong sprint thì nối
vào đơn đó; không trùng thì coi là **đơn mới** chưa lên hệ thống.

**`input/devs.xlsx`** (sửa tay khi có người vào/ra team hoặc nghỉ phép):

| Cột | Giá trị |
|---|---|
| `Tên` | Họ tên đúng như hệ thống ghi trong `Người làm` |
| `Mã` | Mã ngắn hiện trong báo cáo, ví dụ `LinhNV` |
| `Level` | `junior`, `junior+`, `middle`, `middle+`, `senior` |
| `Nhận việc` | `Y` hoặc `N` (`N` tạm đưa dev ra khỏi pool) |
| `Ngày nghỉ` | Các ngày nghỉ, cách nhau bằng dấu phẩy: `YYYY-MM-DD` hoặc `DD/MM/YYYY` |

**Rule cấu hình ở đâu:**

| Muốn chỉnh | Ở đâu | Sửa code? |
|---|---|---|
| Luật giao của TM: `Chỉ định`, `Không giao`, `Tối đa đơn`, `Ưu tiên` | Một file `.md` ngay trong `input/`, hoặc `--rules <file>` (bảng dưới) | Không |
| Dev vào/ra pool, level, ngày nghỉ | `input/devs.xlsx`, hoặc `--devs <file>` | Không |
| Server API và token | `.env`: `SCRUMBOT_API_BASE`, `SCRUMBOT_API_TOKEN` (biến môi trường thắng file) | Không |
| AI, sprint, ngày chạy, thư mục `input/` `output/` `state/` | Tuỳ chọn dòng lệnh, `scrumbot review --help` | Không |
| Ngưỡng review (30 ký tự), ngưỡng rủi ro, 6 giờ làm/ngày, số giờ của S/M/L/XL, thứ tự tiêu chí chọn PIC | Hằng số trong [`src/scrumbot/core/review/`](src/scrumbot/core/review/) và [`src/scrumbot/core/assign/`](src/scrumbot/core/assign/) | Có: sửa spec trước ([`docs/bot-spec.md`](docs/bot-spec.md) §4, §7.3; [`docs/assignment-spec.md`](docs/assignment-spec.md) §7) rồi mới sửa code |

**Luật TM** (không bắt buộc): một file `.md` duy nhất ngay trong `input/`, chứa một bảng có cột cố định, đọc **không
dùng AI** và không bao giờ gửi cho AI. Luật sai hoặc mâu thuẫn thì bot dừng và chỉ đúng dòng.

| Loại | Tác dụng | Ví dụ |
|---|---|---|
| `Chỉ định` | Đơn của app này giao thẳng cho dev này | LinhNV giữ AR Dog |
| `Không giao` | Dev không nhận đơn của app này (để trống App = mọi app) | MinhNM làm MVP sprint này |
| `Tối đa đơn` | Dev nhận tối đa N đơn | AnTD tối đa 1 đơn |
| `Ưu tiên` | Ưu tiên dev này cho app này, vẫn qua giới hạn tải | Cho TiếnBV học PS Remote |

Mỗi luật có thể kèm `Từ ngày` / `Đến ngày`. Cú pháp đầy đủ: [`HOW_TO_USE.md`](HOW_TO_USE.md) mục 4,
[`docs/assignment-spec.md`](docs/assignment-spec.md) §14.

**Đổi sang nguồn khác.** API production, file JSON, database, form trên website hay file Excel đều được: viết một
adapter dựng ra `Inputs`, bằng Python hoặc bằng JSON `scrumbot-input/2` rồi `core.Inputs.from_dict(data)`. Core
không đổi. Adapter phải giữ:

- Đủ trường bắt buộc; ngày viết `YYYY-MM-DD`, thời điểm `YYYY-MM-DDTHH:MM:SS` (giờ hệ thống, không múi giờ). Sai dạng
  thì core dừng với `Dữ liệu đầu vào không đúng dạng: <vị trí>: <vấn đề>.`, ví dụ `devs[2].level`.
- `assignees` của mỗi task là **họ tên đúng như `devs[].name`**, để bot nối người làm với dev; `rules[].dev` là một
  `devs[].code`. Không có dev, trùng tên hoặc mã, luật sai: core tự kiểm tra và dừng.
- `lists` có đủ mọi cấp (đơn gốc, subtask, bug) của mọi sprint Maintain. Subtask và bug không bao giờ thành đơn (D5).
- Thiếu `status_changes` thì `STATUS-STUCK` dựa vào `updated` và `QA-RETURNS` không thấy lần QA trả về.
- `hours` (giờ người nhập) chỉ làm ví dụ cho AI ở đơn lịch sử, không bao giờ là độ lớn (D3).
- Chỉ đọc: không ghi vào hệ thống (O8); token chỉ nằm trong header, không vào `source`, log hay thông báo. Adapter
  `dev_api` có sẵn chỉ đọc server dev và từ chối production (D49); đọc production là một adapter khác.

Bảng trường đầy đủ và các thông báo lỗi: [`docs/bot-spec.md`](docs/bot-spec.md) §8.3. Ví dụ dựng `Inputs` bằng
Python, không HTTP, không file: [`tests/test_engine.py`](tests/test_engine.py).

### 4.2 AI

**Làm gì.** Hai lần gọi, mỗi bước một lần. `review` (đơn đã qua check cố định) đưa cho AI riêng đơn của file cùng các
mẫu loại đơn; AI trả loại đơn, số thứ tự các ý của mẫu mà mô tả còn thiếu, và tối đa 2 câu hỏi cho người lên đơn. `assign` đưa cho AI các đơn của sprint và các đơn lịch sử (kèm số giờ thực tế để AI
so); với mỗi đơn AI trả độ lớn `S` (4h), `M` (16h), `L` (32h) hoặc `XL` (64h) kèm lý do, loại đơn, tối đa 5 hạng mục
và tối đa 2 rủi ro kỹ thuật. Ở `review`, ý thiếu theo mẫu làm review chưa đạt (D65); ngoài phần đó AI **không**
quyết định review đạt hay không, không chọn PIC, không chấm mức rủi ro. AI không nhận
tên người, mã dev hay link: tên thành `[người]`, link thành `[link Figma]`, `[link Google Docs]`, …; AI chạy chỉ đọc
trong một thư mục tạm rỗng. AI lỗi, hết giờ hoặc trả sai thì đơn đó tính là `M` (cảnh báo `SIZE-AI-FAILED` hoặc
`SIZE-AI-INVALID`) và lần chạy vẫn xong; ở `review` thì không chấm mẫu, không có câu hỏi, và review vẫn đạt nếu các
check cố định đạt.

**Cấu hình (không sửa code):**

| Muốn | Cách |
|---|---|
| Chọn AI | `--ai gemini` (mặc định, cần lệnh `gemini` và `GEMINI_API_KEY`), `--ai agy` (`~/.gemini/bin/agy`), `--ai off` (không gọi AI: không có câu hỏi, mọi đơn `M`) |
| Chọn model | `--ai-model <tên>`, truyền thẳng cho công cụ AI |
| Cho AI chờ lâu hơn | `--ai-timeout <giây>` (mặc định 180; `agy` nên để 400) |
| Xem prompt và câu trả lời của AI | `-v` |
| Bắt AI ước lượng lại mọi đơn | Xoá `state/scrumbot.sqlite`: bot nhớ câu trả lời theo ID + tên đơn |

**Custom prompt.** Chưa có file cấu hình prompt: prompt nằm trong code, biến `_PROMPT` (độ lớn) và `_REVIEW_PROMPT`
(review: chấm mẫu và câu hỏi) ở [`src/scrumbot/ai/prompt.py`](src/scrumbot/ai/prompt.py); các mẫu loại đơn ở
[`src/scrumbot/core/review/templates.py`](src/scrumbot/core/review/templates.py). Prompt là một phần của spec
([`docs/assignment-spec.md`](docs/assignment-spec.md) §6.4, [`docs/bot-spec.md`](docs/bot-spec.md) §2.6, §7.3): sửa spec
trước rồi mới sửa code, và giữ:

- **Dạng trả lời**: độ lớn là một mảng JSON, mỗi đơn một phần tử `{"stt", "size", "reason", "type", "items",
  "tech_risks"}`, đọc bằng `parse_reply`; review là một object `{"type", "missing", "questions"}`, đọc bằng
  `parse_review`.
  Thêm hoặc đổi khoá thì sửa cả hàm đọc trong cùng file.
- **Không đưa tên người, mã dev hay link vào prompt.** `build_prompt` và `build_review_prompt` đã lo việc này.
- **Giới hạn độ dài**: prompt tối đa 30.000 ký tự (mô tả bị cắt dần 600 → 200 → 0 ký tự), tối đa 30 đơn lịch sử làm
  ví dụ, ưu tiên đơn cùng app.
- Sửa xong thì xoá `state/scrumbot.sqlite` (câu trả lời cũ được nhớ theo đơn, không theo prompt) và chạy thử với AI
  thật: `ASSIGNTOOL_TEST_AI=agy uv run pytest -m ai`.

**Dùng AI provider khác.** Được, theo 3 mức; mức sau thay nhiều hơn mức trước:

| Mức | Thay phần nào | Giữ nguyên | Làm ở đâu |
|---|---|---|---|
| 1. AI CLI khác cho `scrumbot assign` | Cách chạy lệnh và đọc kết quả | Prompt, cách đọc trả lời, bộ nhớ | Thêm tên vào `AI_TOOLS` ở [`src/scrumbot/cli.py`](src/scrumbot/cli.py), cách gọi và đọc kết quả ở [`src/scrumbot/ai/tools.py`](src/scrumbot/ai/tools.py), dòng mới trong bảng công cụ ở assignment spec §6.4 |
| 2. Hàm `ask` gọi API của nhà cung cấp khác (Claude, OpenAI, Gemini API, …) | Một lần gọi AI | Prompt, cách đọc trả lời, bộ nhớ | Code của website. Đưa vào package này thì cần quyết định trước: hiện chỉ `input/dev_api/client.py` được gọi HTTP |
| 3. Asker / sizer riêng (AI khác hẳn, mô hình riêng, luật riêng) | Toàn bộ module AI | Không gì | Bất kỳ đâu, miễn đúng giao diện `core.Asker` và `core.Sizer` |

Mức 2: `ask` nhận prompt, trả `AiReply`; **không được raise**, lỗi thì trả lý do ngắn bằng tiếng Việt.

```python
from scrumbot import core
from scrumbot.ai.asker import AiAsker
from scrumbot.ai.prompt import AiReply
from scrumbot.ai.sizer import AiSizer

def ask(prompt: str) -> AiReply:
    try:
        text = goi_api_ai(prompt)                      # API của nhà cung cấp, trả về chữ
    except Exception as error:
        return AiReply("ten-ai", None, f"lỗi: {error}")  # đơn tính là M, có cảnh báo SIZE-AI-FAILED
    return AiReply("ten-ai", text, None)

review = core.review(core.place(inputs, now=now), AiAsker(ask, tool="ten-ai"))
sizer = AiSizer(ask, tool="ten-ai", now=now, memory=None)  # memory=None: không nhớ câu trả lời
outcome = core.assign(core.place(inputs, now=now), reviewed={review.order.fingerprint}, sizer=sizer)
```

Mức 3: `asker(row, kind)` trả `core.AiReview` (loại đơn, có chấm mẫu không, số thứ tự các ý thiếu, tối đa 2 câu hỏi, AI
có trả lời không, một dòng ghi chú); `kind` là `Loại đơn` của file hoặc `None`. Không raise khi AI lỗi. Core tự đổi số
thứ tự thành chữ của mẫu, nên asker không đưa được chữ của mình vào câu chặn.
`sizer(orders, examples, fresh)` trả `core.Sizing` (một `SizeEstimate` cho mỗi STT, các cảnh báo, một dòng
ghi chú). Không raise khi AI lỗi: tính `M` và ghi lý do vào ghi chú. Đơn bị bỏ sót thì core tự tính `M`. STT trong
`fresh` (đơn của file đơn) phải được ước lượng ngay, không lấy từ bộ nhớ.

Ở mức nào cũng giữ 3 điều: AI không nhận tên hay link, không chọn PIC, và AI lỗi thì đơn là `M` chứ không làm hỏng lần
chạy. Chi tiết: [`docs/bot-spec.md`](docs/bot-spec.md) §8.5.

### 4.3 Output

**Là gì.** Core trả một object `core.Outcome` (dạng JSON `scrumbot-outcome/3`, lấy bằng `outcome.to_dict()`). Mọi
output đều dựng từ `Outcome`, nên cùng nội dung và cùng câu chữ. `status` là một trong các kết cục:

| `status` | Bước | Khi | Có gì |
|---|---|---|---|
| `not_ready` | `review` | Check cố định chưa đạt, hoặc AI thấy thiếu ý của mẫu | Sprint, đơn, danh sách mục cần sửa (và kết quả của AI khi AI đã chấm) |
| `ready` | `review` | Đạt | Sprint, đơn (kèm `fingerprint` để `assign` nhận ra), kết quả chấm mẫu và câu hỏi của AI |
| `pre_assigned` | `review` | Đơn đã có người làm | Sprint, đơn; không review |
| `proposed` | `assign` | Đơn chưa có người làm | Đủ mọi phần bên dưới, PIC là đề xuất của bot |
| `pre_assigned` | `assign` | Đơn đã có người làm trên hệ thống | Như `proposed`, nhưng giữ nguyên người làm, không có dự phòng |

Kết quả của `review` không có `assignment`, `size`, rủi ro, bảng dev hay cảnh báo; kết quả của `assign` không có
`ai`.

| Phần | Nội dung |
|---|---|
| `run_at`, `source`, `freshness`, `sprint` | Lúc chạy, nguồn, dữ liệu mới nhất lúc nào, sprint đang chạy và sprint trước |
| `order` | Đơn như bot hiểu: STT, ID, nối theo ID / theo tên / đơn mới, App, ưu tiên, hạn, mô tả AI đã đọc, loại đơn, người chịu trách nhiệm, bằng chứng, `fingerprint` |
| `review` | Từng mục cần sửa: mã `REVIEW-…` và câu tiếng Việt |
| `ai` | Loại đơn review đã dùng, có chấm mẫu không, số thứ tự các ý thiếu, câu hỏi của AI cho người lên đơn, AI có trả lời không, ghi chú |
| `assignment` | PIC, lý do một câu, 2 người dự phòng, các dòng luật TM đã áp dụng |
| `size` | Độ lớn, số giờ, có phải mặc định không, lý do, loại đơn, hạng mục, rủi ro kỹ thuật |
| `risks`, `sprint_risks` | Rủi ro của đơn, PIC và sprint: mức, mã, vấn đề, ảnh hưởng, phòng ngừa, nếu xảy ra, ai xử lý, hạn xử lý; số rủi ro theo mức của cả sổ |
| `devs` | Bảng so sánh dev: quen app, số đơn, giờ việc còn lại / sức chứa, việc dở, ngày nghỉ, vai trò |
| `findings` | Cảnh báo dữ liệu `WARN` / `INFO` |

**Có sẵn 2 output:**

- **`output/output.md`** (đổi thư mục bằng `--out`), lệnh sau ghi đè lệnh trước. Của `review` (`# Review đơn: …`):
  mục `Review: chưa đạt` liệt kê từng mục cần sửa, hoặc `Review: đạt` với câu hỏi của AI và lời nhắc chạy `assign`,
  cuối là bảng thông tin đơn. Của `assign` (`# Giao đơn: …`): kết luận (PIC đề xuất, lý do, dự phòng, độ lớn) ·
  thông tin đơn và mô tả AI đã đọc · bảng so sánh 4 dev · rủi ro của đơn, của PIC và của sprint, mỗi rủi ro có
  **Phòng ngừa** và **Nếu xảy ra** · rủi ro kỹ thuật AI nhận xét · cảnh báo dữ liệu.
  Chi tiết: [`docs/bot-spec.md`](docs/bot-spec.md) §7.3, §7.4.
- **Terminal**: nguồn dữ liệu, luật TM đang có hiệu lực, đơn được đặt vào đâu, kết quả review, độ lớn, PIC, số rủi ro,
  các cảnh báo `WARN`, đường dẫn báo cáo. Mã thoát: `0` đã ghi báo cáo (review đạt hay chưa đạt), `2` lỗi input
  hoặc API, hoặc `assign` khi chưa review đạt (kèm một câu tiếng Việt), `130` bấm Ctrl+C.

`state/` chứa câu trả lời AI và các lần review đạt (`scrumbot.sqlite`) và cache các sprint cũ; không commit vì có tên
người.

**Đổi sang output khác.** JSON cho website (`outcome.to_dict()`), trang web, tin nhắn Slack/Telegram/email, file
Excel: viết một adapter đọc `Outcome`. Core không đổi. Adapter phải giữ:

- Chỉ đọc `Outcome`, không tự tính lại PIC, độ lớn hay rủi ro.
- Mã `REVIEW-…`, mã rủi ro và mã cảnh báo không bao giờ đổi khi đã phát hành, nên output khác có thể dùng chữ riêng
  cho từng mã. Câu tiếng Việt chuẩn (kể cả `Nếu xảy ra`) có sẵn trong `Outcome`.
- PIC là **gợi ý**: để người lên đơn xác nhận. Chỉ ghi vào hệ thống khi có API ghi và được duyệt (O8).
- Rủi ro chỉ khuyên. Không hiện token.
- Không báo gì về người ngoài pool (D14): hiện người làm bằng `assignment.pic_codes`, không dùng `pic_names`
  (với đơn `pre_assigned` đó là `Người làm` gốc, có thể có người ngoài pool); `pic_codes` rỗng thì ghi
  `người ngoài team`, như `output.md`.
- Output ghi file thì ghi ra `.tmp` rồi đổi tên; không ghi vào `input/`.

Bảng trường đầy đủ: [`docs/bot-spec.md`](docs/bot-spec.md) §8.4.

## 5. Nguyên tắc cố định

| Nguyên tắc | Lý do |
|---|---|
| AI chỉ ước lượng độ lớn và đặt câu hỏi; luật quyết định review, PIC và mức rủi ro | Kết quả lặp lại được và giải thích được |
| Đơn đã giao sẵn không bao giờ bị đổi | Người giao là người quyết cuối |
| Không dùng ước lượng giờ do người nhập; subtask không được giao, không dùng để đo độ lớn | PIC tự chia subtask |
| Chỉ đọc server dev, chỉ GET; token chỉ nằm trong header | An toàn với hệ thống thật |

## 6. Tích hợp core (cho TM)

TM chỉ cần **`scrumbot.core`** (chỉ dùng thư viện chuẩn Python, không đọc file, không gọi mạng); input, AI và output
do website tự chọn theo mục 4.

```python
from datetime import datetime
from scrumbot import core

inputs = core.Inputs.from_dict(data)      # data: JSON theo scrumbot-input/2 (mục 4.1)

# Bước 1, khi người lên đơn bấm "Review": asker là AI theo mục 4.2; None = không chấm mẫu, không có câu hỏi
outcome = core.review(core.place(inputs, now=datetime.now()), asker=None)
if outcome.status is core.Status.READY:
    luu_review_dat(outcome.order.fingerprint)  # website tự lưu, vd trong database

# Bước 2, khi bấm "Giao": reviewed là mọi fingerprint đã lưu; sizer None = mọi đơn M
outcome = core.assign(core.place(inputs, now=datetime.now()), reviewed=cac_review_dat(), sizer=None)
result = outcome.to_dict()                # JSON theo scrumbot-outcome/3 (mục 4.3)
```

- `core.assign` ném `core.InputError` khi đơn chưa review đạt, hoặc đã đổi (tiêu đề, ID, App, ưu tiên, Hạn, mô tả,
  loại đơn, người chịu trách nhiệm, bằng chứng) sau lần review đạt. `reviewed` là bất kỳ thứ gì hỗ trợ `in` (set, hoặc object tự viết đọc database).
- `core.place(...)` là một bước riêng để in trạng thái trước khi chờ AI, như terminal
  ([`docs/bot-spec.md`](docs/bot-spec.md) §8.2).
- Adapter mẫu: `scrumbot.input.dev_api` (API dev), `scrumbot.input.files` (`devs.xlsx`, luật TM, file đơn),
  `scrumbot.ai.asker.AiAsker` và `scrumbot.ai.sizer.AiSizer` (AI qua `gemini`/`agy`), `scrumbot.output.markdown`
  (`output.md`).
- Đề xuất PIC là **gợi ý**: khớp lựa chọn của TM ở 64% số đơn (mục 1). Website nên để người lên đơn xác nhận.

## 7. Tài liệu

| File | Đọc khi |
|---|---|
| [`HOW_TO_USE.md`](HOW_TO_USE.md) | Dùng tool từng bước: cài đặt, file đơn, output, luật TM |
| [`docs/bot-spec.md`](docs/bot-spec.md) | Nguồn API, review, sổ rủi ro, `output.md`, 3 bước và 2 định dạng chuẩn (§8) |
| [`docs/assignment-spec.md`](docs/assignment-spec.md) | Luật giao PIC, lý do, cảnh báo dữ liệu, luật TM |
| [`docs/api-doc-he-thong.md`](docs/api-doc-he-thong.md) | Tham chiếu API `/api/doc/` |
| [`docs/python-best-practices.md`](docs/python-best-practices.md) | Viết code cho repo này |
| [`confirm.md`](confirm.md) | Mọi quyết định: `D` user chốt, `A` mặc định của Claude, `O` còn mở |

Kiểm tra sau mỗi thay đổi code: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
Đóng gói: `uv build --wheel` → `dist/scrumbot-<version>-py3-none-any.whl`.
