# Hướng dẫn sử dụng scrumbot

scrumbot đề xuất **PIC** (dev chịu trách nhiệm chính) cho đơn của board Maintain và lập **sổ rủi ro** của sprint. Bot
**chỉ đọc** hệ thống nội bộ (server dev); TM đọc kết quả rồi tự nhập PIC vào hệ thống.

| Bạn muốn | Lệnh | Kết quả |
|---|---|---|
| Giao **một đơn** BA/MO vừa gửi | `uv run scrumbot assign input/don/<file đơn>.md --ai agy` | `output/output.md` |
| Giao **cả sprint** đang chạy và xem rủi ro | `uv run scrumbot run --ai agy` | `output/assignment_<sprint>_<giờ>.xlsx` |

Muốn biết bot chọn PIC thế nào và vì sao, đọc [`README.md`](README.md) mục 2.

## 1. Cài đặt (làm một lần)

1. Cài Python ≥ 3.11 và [`uv`](https://docs.astral.sh/uv/), rồi trong thư mục repo chạy `uv sync`.
2. Tạo file token: `cp .env.example .env`, rồi điền:
   ```
   SCRUMBOT_API_TOKEN=<token TM cấp>
   SCRUMBOT_API_BASE=https://devclickup.datlt.site
   ```
   Bot từ chối địa chỉ production. **Không commit, không gửi `.env` cho ai.**
3. Kiểm tra `input/devs.xlsx` (mục 3.1).
4. Chọn AI để ước lượng độ lớn đơn (không bắt buộc):

   | `--ai` | Cần gì |
   |---|---|
   | `agy` | `~/.gemini/bin/agy` (máy hiện tại dùng cái này) |
   | `gemini` (mặc định) | lệnh `gemini` và `GEMINI_API_KEY` |
   | `off` | Không cần gì; mọi đơn tính là `M` (16 giờ) |

## 2. Thư mục

```
input/
├── devs.xlsx          danh sách dev                      bắt buộc, sửa tay
├── <tên bất kỳ>.md    luật TM (custom rule, mục 4)       tuỳ chọn, chỉ được 1 file .md ở đây
└── don/
    └── <tên đơn>.md   file đơn của BA/MO (mục 3.2)       cho lệnh assign
output/                kết quả mỗi lần chạy
state/                 bộ nhớ của bot: đề xuất, trạng thái đơn, cache. Đừng xoá.
.env                   token API
```

Sprint, đơn, người làm, lịch sử các sprint trước: bot tự đọc qua API, **không cần export Excel**.

## 3. Input

### 3.1 `input/devs.xlsx`: danh sách dev

Sheet đầu tiên, dòng 1 là tiêu đề, mỗi dòng một dev.

| Cột | Bắt buộc | Giá trị |
|---|---|---|
| `Tên` | ✓ | Họ tên **đúng y như hệ thống ghi** trong `Người làm`, cả dấu, ví dụ `Ngọc Văn Linh` |
| `Mã` | ✓ | Mã ngắn hiện trong kết quả, ví dụ `LinhNV` |
| `Level` | ✓ | `junior`, `junior+`, `middle`, `middle+`, `senior` |
| `Nhận việc` | ✓ | `Y` hoặc `N`. `N` tạm đưa dev ra khỏi danh sách giao việc mà không phải xoá dòng |
| `Ngày nghỉ` | | Các ngày nghỉ trong sprint, cách nhau bằng dấu phẩy: `YYYY-MM-DD` hoặc `DD/MM/YYYY` |

Sửa file này khi có người vào hoặc rời team, có người tạm không nhận việc, hoặc có lịch nghỉ phép.

> `Tên` viết khác hệ thống (thiếu dấu, thừa chữ) thì bot coi đó là người ngoài team: tải của dev đó bị tính thiếu
> mà **không có cảnh báo**. Copy tên từ hệ thống cho chắc.

Chỉ dev có `Nhận việc` = `Y` mới được đề xuất. QA, RnD và TM không bao giờ được đề xuất.

### 3.2 File đơn (cho `assign`)

Đặt trong `input/don/`, một đơn một file `.md`. Mẫu:

```markdown
# Game Emulator - Chỉnh sửa và bổ sung luồng auto scan game

| Trường | Giá trị |
|---|---|
| ID | |
| App | Game Emulator |
| Ưu tiên | high |
| Hạn | 16/10/2026 |

Mô tả tự do: nội dung đơn, link SRS, link Figma, link tracking, …
```

| Phần | Cách bot đọc |
|---|---|
| Tên đơn | Dòng `# ` đầu tiên; không có thì lấy tên file |
| `ID` | ID đơn trên hệ thống (nếu đơn đã có) |
| `App` | Tên app, viết giống `App Name` trên hệ thống |
| `Ưu tiên` | `urgent`, `high`, `normal` hoặc `low` |
| `Hạn` | `YYYY-MM-DD` hoặc `DD/MM/YYYY` |
| Phần còn lại | Mô tả, giữ nguyên như viết |

Mọi trường đều **không bắt buộc**: để trống ô là được, nhưng không thêm trường lạ (bot báo lỗi). Bot đọc file này
**không dùng AI**.

**Bot tìm đơn trong sprint thế nào:**

1. Có `ID`: lấy đơn đó trên hệ thống. Tên, App, ưu tiên, hạn lấy từ hệ thống; file chỉ góp phần mô tả.
2. Không có `ID` nhưng tên trùng một đơn trong sprint: nối vào đơn đó.
3. Không trùng: coi là **đơn mới** chưa lên hệ thống, xếp sau các đơn hiện có.

**Riêng tư:** trước khi gửi mô tả cho AI, bot thay mọi link bằng loại link (`[link Figma]`, `[link Google Docs]`, …)
và tên người (dev trong `devs.xlsx`, người làm trên hệ thống, mọi chữ có dạng mã người như `LinhNV`) bằng `[người]`.
AI không mở link. Họ tên đầy đủ của người ngoài team thì bot không nhận ra: đừng ghi vào file đơn.

## 4. Custom rule: luật TM

TM điều chỉnh cách giao mà không phải sửa code, bằng **một file `.md` chứa một bảng luật**.

### 4.1 Đặt file ở đâu

- Một file `.md`, tên tuỳ ý, nằm **trực tiếp** trong `input/`, ví dụ `input/luat.md`. Bot tự tìm thấy.
- Hoặc để ở chỗ khác rồi chỉ đường dẫn: `--rules duong/dan/luat.md`.
- Không có file nào thì chạy không có luật. Có từ 2 file `.md` trong `input/` thì bot dừng và báo lỗi: bỏ bớt hoặc
  dùng `--rules`.
- **Đừng để file đơn trực tiếp trong `input/`**: `run` sẽ coi nó là file luật. File đơn để trong `input/don/`.

### 4.2 Mẫu

```markdown
# Luật giao việc

Ghi chú tự do ngoài bảng thì bot bỏ qua.

| Loại       | Dev    | App       | Số đơn | Từ ngày    | Đến ngày   | Ghi chú                 |
|------------|--------|-----------|--------|------------|------------|-------------------------|
| Chỉ định   | LinhNV | AR Dog    |        |            |            | Linh giữ AR Dog         |
| Không giao | MinhNM |           |        | 06/10/2026 | 17/10/2026 | Minh làm MVP sprint này |
| Tối đa đơn | AnTD   |           | 1      | 06/10/2026 | 17/10/2026 |                         |
| Ưu tiên    | TiếnBV | PS Remote |        |            |            | Cho Tiến học PS Remote  |
```

| Cột | Ý nghĩa |
|---|---|
| `Loại` | `Chỉ định`, `Không giao`, `Tối đa đơn` hoặc `Ưu tiên` |
| `Dev` | Một `Mã` có trong `devs.xlsx`; mỗi dòng một dev |
| `App` | Một app. Bắt buộc với `Chỉ định` và `Ưu tiên`; để trống ở `Không giao` nghĩa là mọi app; `Tối đa đơn` không dùng |
| `Số đơn` | Số nguyên ≥ 1, chỉ dùng cho `Tối đa đơn` |
| `Từ ngày`, `Đến ngày` | `DD/MM/YYYY` hoặc `YYYY-MM-DD`; để trống là không giới hạn phía đó |
| `Ghi chú` | Tự do; bot chép vào lý do chọn PIC |

### 4.3 Mỗi loại luật làm gì

| Loại | Tác dụng |
|---|---|
| `Chỉ định` | Đơn của app này giao thẳng cho dev này, bỏ qua giới hạn tải. Dev đó nghỉ cả sprint, `Nhận việc` = `N` hoặc đã đủ `Tối đa đơn` thì luật không tác dụng và đơn được xét như bình thường |
| `Không giao` | Dev không nhận đơn của app này, hoặc không nhận đơn nào nếu `App` trống |
| `Tối đa đơn` | Dev nhận tối đa N đơn trong sprint, tính cả đơn đã được giao sẵn |
| `Ưu tiên` | Dev được xếp trước mọi tiêu chí khác cho app này, nhưng vẫn phải qua giới hạn tải (không ai giữ quá số đơn của người ít đơn nhất + 1) |

- Luật chỉ có hiệu lực khi hôm nay nằm trong khoảng `Từ ngày`–`Đến ngày`. Chạy trước khi sprint bắt đầu thì bot tính
  theo ngày đầu sprint.
- `Không giao` và `Tối đa đơn` loại hết người cho một đơn: bot bỏ qua hai loại luật này cho riêng đơn đó và cảnh báo
  `RULE-NO-CANDIDATE`.
- Luật **không bao giờ** đổi đơn đã có người làm, không đưa người ngoài danh sách dev vào, và không được gửi cho AI.

### 4.4 Kiểm tra luật

- Terminal in ra dòng `Luật TM: file luat.md (4 luật, 3 có hiệu lực ngày …)`.
- Đơn chịu tác động của luật thì lý do chọn PIC ghi số dòng của luật đó và chép phần `Ghi chú`.
- Luật sai hoặc mâu thuẫn (hai `Chỉ định` khác dev cho một app, `Chỉ định` và `Không giao` cho cùng một dev, `Dev`
  không có trong `devs.xlsx`, …) thì bot **dừng** và chỉ đúng file, dòng, cột. Danh sách đủ các lỗi:
  [`docs/assignment-spec.md`](docs/assignment-spec.md) §14.2.

### 4.5 Những gì khác chỉnh được

| Muốn | Chỉnh ở |
|---|---|
| Tạm cho một dev nghỉ nhận việc, khai báo nghỉ phép, đổi level | `input/devs.xlsx` (mục 3.1) |
| Đổi AI, cho AI chờ lâu hơn, giao sprint khác, chạy như thể ngày khác | Tuỳ chọn dòng lệnh (mục 5.3) |
| Ngưỡng rủi ro, số giờ của mỗi độ lớn, thứ tự tiêu chí chọn PIC | Nằm trong code. Muốn đổi thì sửa spec ([`docs/bot-spec.md`](docs/bot-spec.md) §4, [`docs/assignment-spec.md`](docs/assignment-spec.md) §7) rồi mới sửa code |

## 5. Chạy

### 5.1 Giao một đơn: `assign`

1. Lưu file đơn vào `input/don/` (mục 3.2).
2. Chạy:
   ```bash
   uv run scrumbot assign input/don/req_from_ba_test.md --ai agy --ai-timeout 400
   ```
   Lần đầu trong ngày, AI phải ước lượng mọi đơn của sprint (khoảng 5–6 phút với 7 đơn). Các lần sau chỉ còn đơn
   trong file (khoảng 2 phút). Vội thì dùng `--ai off`.
3. Mở `output/output.md` (mục 6.1).

`assign` tính trên cả sprint đang chạy, nên tải và rủi ro là của sprint thật cộng thêm đơn này. Lệnh này **không lưu**
đề xuất vào bộ nhớ: muốn bot giữ đề xuất qua các lần chạy thì dùng `run`.

### 5.2 Giao cả sprint: `run`

```bash
uv run scrumbot run --ai agy             # chạy bình thường: báo cáo vào output/, cập nhật bộ nhớ
uv run scrumbot run --ai off             # không gọi AI; mọi đơn tính là M
uv run scrumbot run --today 2026-10-15   # như thể hôm nay là 15/10; không đọc, không ghi bộ nhớ
```

### 5.3 Tuỳ chọn (dùng chung cho `run` và `assign`)

| Tuỳ chọn | Mặc định | Ý nghĩa |
|---|---|---|
| `--ai gemini\|agy\|off` | `gemini` | Công cụ AI ước lượng độ lớn |
| `--ai-timeout GIÂY` | `180` | Số giây chờ AI; với `agy` nên để `400` |
| `--ai-model TÊN` | | Model truyền thẳng cho công cụ AI |
| `--sprint-id ID` | sprint đang chạy | Giao một sprint khác |
| `--today NGÀY` | hôm nay | Chạy như thể hôm nay là ngày này (`YYYY-MM-DD` hoặc `DD/MM/YYYY`) |
| `--input THƯ_MỤC` | `input/` | Nơi tìm `devs.xlsx` và file luật |
| `--devs FILE` | `input/devs.xlsx` | File dev |
| `--rules FILE` | file `.md` duy nhất trong `input/` | File luật TM |
| `--out THƯ_MỤC` | `output/` | Nơi ghi kết quả |
| `--state THƯ_MỤC` | `state/` | Bộ nhớ của bot |
| `-v` | tắt | In chi tiết lỗi và trao đổi với AI |

Xem đủ: `uv run scrumbot run --help`.

## 6. Output

### 6.1 `assign`: `output/output.md`

Đọc từ trên xuống:

| Mục | Nội dung |
|---|---|
| **Kết luận** | PIC đề xuất, lý do một câu, 2 người dự phòng, độ lớn AI ước lượng, số rủi ro liên quan. Đơn đã có người làm thì bot giữ nguyên, không đề xuất người khác |
| **Thông tin đơn** | Đơn mới hay đơn đã có trên hệ thống, App, ưu tiên, hạn, loại đơn và hạng mục AI nhận ra, mô tả đúng như AI đã đọc |
| **So sánh dev** | Mỗi dev một dòng: level, đã làm app chưa, số đơn, giờ việc còn lại / sức chứa, việc dở sprint trước, ngày nghỉ, vai trò (PIC, dự phòng) |
| **Rủi ro và phương án dự phòng** | Rủi ro của đơn, của PIC và của sprint, mỗi dòng có **Phòng ngừa** và **Nếu xảy ra**, ai xử lý, hạn xử lý |
| **Rủi ro kỹ thuật** | AI nhận xét, chỉ để tham khảo |
| **Cảnh báo dữ liệu** | Dữ liệu thiếu hoặc lạ |

Lần chạy sau **ghi đè** file này: muốn giữ thì copy ra chỗ khác.

### 6.2 `run`: `output/assignment_<sprint>_<YYYYMMDD-HHMMSS>.xlsx`

| Sheet | Nội dung |
|---|---|
| `Tóm tắt` | Sprint, ngày chạy, số đơn (giao sẵn / đề xuất mới / giữ từ lần trước), số rủi ro theo mức, từng rủi ro Cao. **Đọc trước** |
| `Phân công` | Mỗi đơn một dòng: dữ liệu gốc, độ lớn và lý do, PIC, lý do chọn, 2 người dự phòng, mã rủi ro |
| `Rủi ro` | Sổ rủi ro: mức, mã, vấn đề, ảnh hưởng, đề xuất xử lý, ai xử lý, hạn xử lý |
| `Thay đổi` | So với lần chạy trước: đơn mới hoặc bị bỏ, đổi ưu tiên / hạn / tên, TM giao có khớp đề xuất không |
| `Cảnh báo` | Dữ liệu thiếu hoặc lạ (AI lỗi, đơn thiếu app, đơn gấp chưa có hạn, …) |
| `Tải dev` | Mỗi dev: số đơn, giờ việc, sức chứa còn lại, việc dở, ngày nghỉ, app đã làm |

Bot **nhớ** đề xuất trong `state/`: một đơn đã được đề xuất thì lần sau vẫn giữ người đó cho tới khi đơn có người làm
trên hệ thống. Rủi ro chỉ để khuyên: không bao giờ đổi PIC.

### 6.3 Độ lớn đơn

| Độ lớn | Giờ tính vào tải |
|---|---|
| `S` | 4 |
| `M` | 16 |
| `L` | 32 |
| `XL` | 64 |

AI ước lượng từ tên đơn (`assign` có thêm mô tả trong file đơn). AI lỗi, hết giờ hoặc tắt thì đơn tính là `M` và
lần chạy vẫn tiếp tục.

### 6.4 Terminal và mã thoát

Terminal in tóm tắt: file luật, sprint, cách ước lượng độ lớn, mỗi đề xuất một dòng, các cảnh báo, đường dẫn kết quả.

| Mã thoát | Khi nào |
|---|---|
| `0` | Đã ghi kết quả (có hoặc không có cảnh báo, có hoặc không có AI) |
| `2` | Lỗi input hoặc lỗi API. Không ghi kết quả. Câu báo lỗi tiếng Việt chỉ rõ file, dòng, cột |
| `130` | Bấm Ctrl+C |

## 7. Lỗi thường gặp

| Bạn thấy | Làm gì |
|---|---|
| `Thiếu SCRUMBOT_API_TOKEN …` | Tạo `.env` theo mục 1 |
| `API từ chối token (401)` | Token sai hoặc hết hạn: xin TM token mới |
| `API vẫn giới hạn tải (429)` hoặc lỗi server (5xx) | Chạy lại sau ít phút |
| `Có nhiều … Chỉ định một file bằng --rules` | Chỉ để một file luật `.md` trong `input/`, hoặc dùng `--rules` |
| `File đơn … trường '…' không hợp lệ` | Bảng trong file đơn chỉ dùng `ID`, `App`, `Ưu tiên`, `Hạn` |
| `Có <k> đơn tên '…' trong …` | Nhiều đơn trùng tên: ghi `ID` của đơn vào file đơn |
| AI chạy lâu hoặc hết giờ | Tăng `--ai-timeout 400`, hoặc chạy `--ai off` |
| Một dev có tải thấp bất thường | `Tên` trong `devs.xlsx` viết khác hệ thống (mục 3.1) |
| Muốn xem bot làm gì khi lỗi | Thêm `-v` |
