# scrumbot

Bot scrum master cho team Android. **BA/MO chạy bot khi lên đơn** (D61): bot đọc đơn trong file `.md`, đọc sprint đang
chạy của board Maintain từ API chỉ-đọc của hệ thống nội bộ (server **dev**), rồi làm **ba việc**:

1. **Review đơn**: thiếu App, đơn gấp chưa có hạn hoặc mô tả quá ngắn thì bot dừng, chỉ ghi những gì cần bổ sung.
2. **Đề xuất PIC** (dev chịu trách nhiệm chính) khi đơn đạt, kèm lý do và 2 người dự phòng.
3. **Báo rủi ro** của đơn, của PIC và của cả sprint: quá tải, trễ hạn, kẹt trạng thái, QA trả về nhiều, PIC vắng.

Một lệnh duy nhất: **`scrumbot assign <file đơn>`**, kết quả là **`output/output.md`**. Bot không chạy theo lịch.
Đơn đạt thì **người lên đơn** nhập PIC vào hệ thống, vì bot chưa ghi được gì vào hệ thống.

> **Đơn** = task gốc trên board Maintain, ứng với một version của một app. **Pool** = 4 dev Android có
> `Nhận việc` = `Y` trong `input/devs.xlsx`. QA, RnD và TM không bao giờ được đề xuất.

## 1. Mục tiêu và phạm vi

| | Nội dung |
|---|---|
| **Làm** | Review một đơn BA/MO viết trong file `.md` · đề xuất PIC · sổ rủi ro 9 mã · `output/output.md` (D60, D62) |
| **Không làm** | Ghi vào hệ thống · giao bug hoặc subtask · đổi đơn đã có người làm · báo gì về người ngoài pool · đọc server production |
| **Đã bỏ** | 13/10/2026 (D59): chạy theo lịch 30 phút, báo cáo cuối sprint, clone + replay sprint cũ, chạy bằng file export Excel, bộ đánh giá `eval/` (git `7b2fa0d`). 14/10/2026 (D62): lệnh `run`, báo cáo Excel 6 sheet, bộ nhớ đề xuất giữa các lần chạy, rủi ro `ORDER-CHANGED` (git `754b165`). |

**Lộ trình:**

| Giai đoạn | Trạng thái | Nội dung |
|---|---|---|
| GĐ 1 | **Xong** (14/10/2026) | Đọc API dev, review đơn, giao PIC, sổ rủi ro 9 mã. Đo lần cuối (replay 29 sprint, 13/10): khớp TM 64% số đơn; sổ rủi ro báo trước 82% đơn có kết cục xấu. |
| GĐ 2 | Chờ hệ thống | Ghi PIC vào hệ thống khi có API ghi (O8). Rủi ro 1 và 12 cho cả sprint khi API trả mô tả đơn (D53). Đơn RnD mặc định về DuyLT khi hệ thống có tag loại đơn (D58). |

## 2. Cách bot làm việc

```
INPUT                               XỬ LÝ                                    OUTPUT
file đơn .md của BA/MO       ─┐     1. Đặt đơn vào sprint đang chạy
API dev /api/doc/ (chỉ GET)  ─┤     2. Review: thiếu gì thì dừng ở đây ──►  output/output.md
  sprints · don · lich-su     │     3. AI ước lượng độ lớn S/M/L/XL          (review, PIC, rủi ro)
input/devs.xlsx              ─┼──►  4. Giao PIC theo luật cố định      ──►   Tóm tắt trên terminal
input/<luật TM>.md (tuỳ ý)   ─┘     5. Sổ rủi ro (9 mã)
```

**AI chỉ ước lượng độ lớn đơn và đặt câu hỏi cho người lên đơn.** Review, ai làm đơn nào và rủi ro mức nào đều do
luật cố định quyết định, nên lần nào chạy cũng ra cùng kết quả và giải thích được bằng một câu. AI lỗi hoặc tắt thì
mọi đơn tính là `M` (16 giờ) và lần chạy vẫn tiếp tục.

### 2.1 Review đơn

| Mã | Bot dừng khi |
|---|---|
| `REVIEW-APP` | Đơn không có App |
| `REVIEW-DUE` | Đơn urgent/high không có Hạn |
| `REVIEW-DESC` | Mô tả dưới 30 ký tự (không tính link) |

Đơn chưa đạt thì `output.md` chỉ ghi những gì cần sửa; sửa file đơn rồi chạy lại. Đơn đạt thì AI có thể hỏi tối đa 2
câu về chỗ mô tả còn thiếu: chỉ để nhắc, không chặn. Đơn đã có người làm trên hệ thống thì không review.
Chi tiết: [`docs/bot-spec.md`](docs/bot-spec.md) §7.3.

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
scrumbot assign input/don/<file đơn>.md                  # dùng gemini (mặc định)
scrumbot assign input/don/<file đơn>.md --ai off         # không gọi AI; mọi đơn tính là M, không có câu hỏi AI
scrumbot assign input/don/<file đơn>.md --ai agy --ai-timeout 400
scrumbot assign --help                                   # mọi tuỳ chọn
```

Trong repo thì thêm `uv run` phía trước. Lần đầu trong ngày AI phải ước lượng mọi đơn của sprint (với `agy` khoảng
5–6 phút cho 7 đơn); các lần sau chỉ còn đơn trong file. Đơn chưa đạt review thì bot không gọi AI nên xong ngay.
Lỗi API hoặc lỗi input dừng lần chạy với mã thoát `2` và một câu tiếng Việt nói rõ lỗi.

## 4. Input

**File đơn** (đặt trong `input/don/`, đọc **không dùng AI**):

```markdown
# Game Emulator - Chỉnh sửa và bổ sung luồng auto scan game

| Trường | Giá trị |
|---|---|
| ID | |
| App | Game Emulator |
| Ưu tiên | high |
| Hạn | 16/10/2026 |

Mô tả tự do: nội dung đơn, các hạng mục cần làm, link SRS, link Figma, …
```

Có `ID` thì bot lấy đơn đó trên hệ thống và chỉ thêm mô tả; không có `ID` mà tên trùng một đơn trong sprint thì nối
vào đơn đó; không trùng thì coi là **đơn mới** chưa lên hệ thống. Trước khi gửi cho AI, bot thay link bằng loại link
(`[link Figma]`, `[link Google Docs]`, …) và thay tên người bằng `[người]`.

**`input/devs.xlsx`** (sửa tay khi có người vào/ra team hoặc nghỉ phép):

| Cột | Giá trị |
|---|---|
| `Tên` | Họ tên đúng như hệ thống ghi trong `Người làm` |
| `Mã` | Mã ngắn hiện trong báo cáo, ví dụ `LinhNV` |
| `Level` | `junior`, `junior+`, `middle`, `middle+`, `senior` |
| `Nhận việc` | `Y` hoặc `N` (`N` tạm đưa dev ra khỏi pool) |
| `Ngày nghỉ` | Các ngày nghỉ, cách nhau bằng dấu phẩy: `YYYY-MM-DD` hoặc `DD/MM/YYYY` |

**Luật TM** (không bắt buộc): một file `.md` duy nhất ngay trong `input/`, chứa một bảng có cột cố định, đọc **không
dùng AI**. Luật sai hoặc mâu thuẫn thì bot dừng và chỉ đúng dòng.

| Loại | Tác dụng | Ví dụ |
|---|---|---|
| `Chỉ định` | Đơn của app này giao thẳng cho dev này | LinhNV giữ AR Dog |
| `Không giao` | Dev không nhận đơn của app này (để trống App = mọi app) | MinhNM làm MVP sprint này |
| `Tối đa đơn` | Dev nhận tối đa N đơn | AnTD tối đa 1 đơn |
| `Ưu tiên` | Ưu tiên dev này cho app này, vẫn qua giới hạn tải | Cho TiếnBV học PS Remote |

Mỗi luật có thể kèm `Từ ngày` / `Đến ngày`. Cú pháp đầy đủ: [`docs/assignment-spec.md`](docs/assignment-spec.md) §14.

## 5. Output: `output/output.md`

Đơn **chưa đạt** review: tiêu đề, sprint, mục `Review: chưa đạt` liệt kê từng mục cần sửa. Không có PIC.

Đơn **đạt**: câu hỏi của AI cho người lên đơn · kết luận (PIC đề xuất, lý do, dự phòng, độ lớn) · thông tin đơn và
mô tả AI đã đọc · bảng so sánh 4 dev (quen app, số đơn, giờ việc còn lại / sức chứa, việc dở, ngày nghỉ, vai trò) ·
rủi ro của đơn, của PIC và của sprint, mỗi rủi ro có **Phòng ngừa** và **Nếu xảy ra** · rủi ro kỹ thuật AI nhận xét ·
cảnh báo dữ liệu. Chi tiết: [`docs/bot-spec.md`](docs/bot-spec.md) §7.4.

Lần chạy sau ghi đè file này. `state/` chứa câu trả lời AI (`scrumbot.sqlite`) và cache các sprint cũ; không commit
vì có tên người.

## 6. Nguyên tắc cố định

| Nguyên tắc | Lý do |
|---|---|
| AI chỉ ước lượng độ lớn và đặt câu hỏi; luật quyết định review, PIC và mức rủi ro | Kết quả lặp lại được và giải thích được |
| Đơn đã giao sẵn không bao giờ bị đổi | Người giao là người quyết cuối |
| Không dùng ước lượng giờ do người nhập; subtask không được giao, không dùng để đo độ lớn | PIC tự chia subtask |
| Chỉ đọc server dev, chỉ GET; token chỉ nằm trong header | An toàn với hệ thống thật |

## 7. Tài liệu

| File | Đọc khi |
|---|---|
| [`HOW_TO_USE.md`](HOW_TO_USE.md) | Dùng tool từng bước: cài đặt, file đơn, output, luật TM |
| [`docs/bot-spec.md`](docs/bot-spec.md) | Nguồn API, review, sổ rủi ro, `output.md` |
| [`docs/assignment-spec.md`](docs/assignment-spec.md) | Luật giao PIC, lý do, cảnh báo dữ liệu, luật TM |
| [`docs/api-doc-he-thong.md`](docs/api-doc-he-thong.md) | Tham chiếu API `/api/doc/` |
| [`docs/python-best-practices.md`](docs/python-best-practices.md) | Viết code cho repo này |
| [`confirm.md`](confirm.md) | Mọi quyết định: `D` user chốt, `A` mặc định của Claude, `O` còn mở |

Kiểm tra sau mỗi thay đổi code: `uv run ruff check . && uv run ruff format --check . && uv run pytest`.
Đóng gói: `uv build --wheel` → `dist/scrumbot-<version>-py3-none-any.whl`.
