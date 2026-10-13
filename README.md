# scrumbot

Bot scrum master cho team Android. Mỗi lần chạy, bot đọc sprint đang chạy của board Maintain từ API chỉ-đọc của hệ
thống nội bộ (server **dev**), rồi làm **hai việc**:

1. **Đề xuất PIC** (dev chịu trách nhiệm chính) cho mỗi đơn gốc còn trống.
2. **Lập sổ rủi ro** của sprint: quá tải, trễ hạn, kẹt trạng thái, QA trả về nhiều, PIC vắng, đơn đổi so với hôm trước.

Kết quả là **một file Excel**. TM đọc file này rồi tự nhập PIC vào hệ thống, vì bot chưa ghi được gì vào hệ thống.

> **Đơn** = task gốc trên board Maintain, ứng với một version của một app. **Pool** = 4 dev Android có
> `Nhận việc` = `Y` trong `input/devs.xlsx`. QA, RnD và TM không bao giờ được đề xuất.

## 1. Mục tiêu và phạm vi

| | Nội dung |
|---|---|
| **Làm** | Giao PIC cho đơn trống · sổ rủi ro 10 mã · nhớ đề xuất và trạng thái đơn giữa các lần chạy để thấy cái gì đã đổi · một báo cáo Excel |
| **Không làm** | Ghi vào hệ thống · giao bug hoặc subtask · đổi đơn đã có người làm · báo gì về người ngoài pool · đọc server production |
| **Đã bỏ** (13/10/2026, `confirm.md` D59) | Chạy theo lịch 30 phút, báo cáo cuối sprint, clone + replay sprint cũ, chạy bằng file export Excel, bộ đánh giá `eval/`. Code vẫn còn trong lịch sử git (commit `7b2fa0d`). |

**Lộ trình:**

| Giai đoạn | Trạng thái | Nội dung |
|---|---|---|
| GĐ 1 | **Xong** (13/10/2026) | Đọc API dev, giao PIC, sổ rủi ro 10 mã, bộ nhớ, báo cáo 6 sheet. Đo lần cuối (replay 29 sprint, trước khi bỏ replay): khớp TM 64% số đơn; sổ rủi ro báo trước 82% đơn có kết cục xấu. |
| GĐ 2 | Chờ hệ thống | Ghi PIC vào hệ thống khi có API ghi (O8). Rủi ro 1 và 12 khi API trả mô tả đơn (D53). Đơn RnD mặc định về DuyLT khi hệ thống có tag loại đơn (D58). |

## 2. Cách bot làm việc

```
INPUT                               XỬ LÝ                                    OUTPUT
API dev /api/doc/ (chỉ GET) ─┐      1. Dựng đơn, độ quen app, việc dở,
  sprints · don · lich-su    │         ngày nghỉ                            output/assignment_<sprint>_<giờ>.xlsx
input/devs.xlsx             ─┼──►   2. AI ước lượng độ lớn S/M/L/XL   ──►   (6 sheet)
input/<luật TM>.md (tuỳ ý)  ─┤      3. Giao PIC theo luật cố định           Tóm tắt trên terminal
state/scrumbot.sqlite       ─┘      4. Sổ rủi ro (10 mã)                     state/scrumbot.sqlite (cập nhật)
  (lần chạy trước)                  5. So với lần chạy trước
```

**AI chỉ ước lượng độ lớn đơn** (từ tiêu đề, vì API chưa trả mô tả). Ai làm đơn nào và rủi ro mức nào đều do luật cố
định quyết định, nên lần nào chạy cũng ra cùng kết quả và giải thích được bằng một câu. AI lỗi hoặc tắt thì mọi đơn tính
là `M` (16 giờ) và lần chạy vẫn tiếp tục.

### 2.1 Giao PIC

1. Đơn đã có người làm thì **giữ nguyên**; độ lớn của nó chỉ cộng vào tải của dev đó.
2. Đơn trống được xét lần lượt: ưu tiên → hạn → ngày tạo.
3. Ứng viên là pool, trừ dev bị luật TM loại. Chỉ xét dev đang giữ không quá **số đơn của người ít đơn nhất + 1**,
   để không ai ôm hết.
4. Chọn dev tốt nhất theo thứ tự: luật `Ưu tiên` của TM → **quen app** (làm version gần nhất > từng làm > chưa làm) →
   đơn gấp hoặc app mới thì cần middle trở lên → ít giờ tải hơn → ít việc dở hơn → ít ngày nghỉ hơn → level cao hơn.
5. Mỗi đề xuất có **lý do** một câu và **2 người dự phòng**. Đề xuất được **giữ** giữa các lần chạy cho tới khi đơn có
   người làm trên hệ thống.

Chi tiết: [`docs/assignment-spec.md`](docs/assignment-spec.md) §7.

### 2.2 Sổ rủi ro

Rủi ro **chỉ khuyên**: không đổi PIC, không đụng đơn đã giao, không đổi mã thoát. Mỗi dòng ghi vấn đề, ảnh hưởng, đề
xuất xử lý, ai xử lý, hạn xử lý.

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
| Thay đổi | `ORDER-CHANGED` | Đơn đổi ưu tiên, hạn hoặc tên so với lần chạy trước |

Ngưỡng và mức: [`docs/bot-spec.md`](docs/bot-spec.md) §4.

## 3. Cài đặt

| Cần | Ghi chú |
|---|---|
| Python ≥ 3.11 và [`uv`](https://docs.astral.sh/uv/) | `uv sync` một lần trong thư mục repo. |
| `.env` | `SCRUMBOT_API_TOKEN=<token TM cấp>` và `SCRUMBOT_API_BASE=https://devclickup.datlt.site` (mẫu: `.env.example`). Không commit. Bot từ chối địa chỉ production. |
| `input/devs.xlsx` | Mục 5. |
| AI (không bắt buộc) | `agy` ở `~/.gemini/bin/agy`, hoặc `gemini` có `GEMINI_API_KEY`. Không có AI thì chạy `--ai off`. |

## 4. Chạy

```bash
uv run scrumbot run --ai agy             # chạy trên API: báo cáo vào output/, cập nhật bộ nhớ
uv run scrumbot run --ai off             # không gọi AI; mọi đơn tính là M
uv run scrumbot run --today 2026-10-15   # như thể hôm nay là 15/10; không đọc, không ghi bộ nhớ
uv run scrumbot run --help               # mọi tuỳ chọn (--sprint-id, --input, --devs, --rules, --out, --state, -v)
```

Lỗi API hoặc lỗi input dừng lần chạy với mã thoát `2` và một câu tiếng Việt nói rõ lỗi.

## 5. Input

**`input/devs.xlsx`** (sửa tay khi có người vào/ra team hoặc nghỉ phép):

| Cột | Giá trị |
|---|---|
| `Tên` | Họ tên đúng như hệ thống ghi trong `Người làm` |
| `Mã` | Mã ngắn hiện trong báo cáo, ví dụ `LinhNV` |
| `Level` | `junior`, `junior+`, `middle`, `middle+`, `senior` |
| `Nhận việc` | `Y` hoặc `N` (`N` tạm đưa dev ra khỏi pool) |
| `Ngày nghỉ` | Các ngày nghỉ, cách nhau bằng dấu phẩy: `YYYY-MM-DD` hoặc `DD/MM/YYYY` |

**Luật TM** (không bắt buộc): một file `.md` duy nhất trong `input/`, chứa một bảng có cột cố định, đọc **không dùng
AI**. Luật sai hoặc mâu thuẫn thì bot dừng và chỉ đúng dòng.

| Loại | Tác dụng | Ví dụ |
|---|---|---|
| `Chỉ định` | Đơn của app này giao thẳng cho dev này | LinhNV giữ AR Dog |
| `Không giao` | Dev không nhận đơn của app này (để trống App = mọi app) | MinhNM làm MVP sprint này |
| `Tối đa đơn` | Dev nhận tối đa N đơn | AnTD tối đa 1 đơn |
| `Ưu tiên` | Ưu tiên dev này cho app này, vẫn qua giới hạn tải | Cho TiếnBV học PS Remote |

Mỗi luật có thể kèm `Từ ngày` / `Đến ngày`. Cú pháp đầy đủ: [`docs/assignment-spec.md`](docs/assignment-spec.md) §14.

## 6. Output: `output/assignment_<sprint>_<YYYYMMDD-HHMMSS>.xlsx`

| Sheet | Nội dung |
|---|---|
| `Tóm tắt` | Sprint, ngày chạy, độ mới của dữ liệu, số đơn (giao sẵn / đề xuất mới / giữ từ lần trước), số rủi ro theo mức, từng rủi ro Cao. **Đọc trước.** |
| `Phân công` | Mỗi đơn một dòng: dữ liệu gốc, độ lớn và lý do, PIC, nguồn, lý do chọn, 2 người dự phòng, mã rủi ro |
| `Rủi ro` | Sổ rủi ro |
| `Thay đổi` | So với lần chạy hôm trước: đơn mới / bị bỏ, đổi ưu tiên / hạn / tên, TM đã giao có khớp đề xuất không |
| `Cảnh báo` | Dữ liệu thiếu hoặc lạ (AI lỗi, đơn thiếu app, đơn gấp chưa có hạn, …) |
| `Tải dev` | Mỗi dev: số đơn, giờ, sức chứa còn lại, việc dở, ngày nghỉ, app đã làm |

`state/` chứa bộ nhớ (`scrumbot.sqlite`) và cache các sprint cũ; không commit vì có tên người.

## 7. Nguyên tắc cố định

| Nguyên tắc | Lý do |
|---|---|
| AI chỉ ước lượng độ lớn; luật quyết định PIC và mức rủi ro | Kết quả lặp lại được và giải thích được |
| Đơn đã giao sẵn không bao giờ bị đổi | TM là người quyết cuối |
| Không dùng ước lượng giờ do người nhập; subtask không được giao, không dùng để đo độ lớn | PIC tự chia subtask |
| Chỉ đọc server dev, chỉ GET; token chỉ nằm trong header | An toàn với hệ thống thật |

## 8. Tài liệu

| File | Đọc khi |
|---|---|
| [`docs/bot-spec.md`](docs/bot-spec.md) | Nguồn API, sổ rủi ro, bộ nhớ, báo cáo |
| [`docs/assignment-spec.md`](docs/assignment-spec.md) | Luật giao PIC, lý do, cảnh báo dữ liệu, luật TM |
| [`docs/api-doc-he-thong.md`](docs/api-doc-he-thong.md) | Tham chiếu API `/api/doc/` |
| [`docs/python-best-practices.md`](docs/python-best-practices.md) | Viết code cho repo này |
| [`confirm.md`](confirm.md) | Mọi quyết định: `D` user chốt, `A` mặc định của Claude, `O` còn mở |

Kiểm tra sau mỗi thay đổi code: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
