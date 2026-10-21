# Hướng dẫn sử dụng scrumbot

scrumbot dành cho **BA/MO khi lên đơn**, hai bước trên cùng một file đơn: bot **review** đơn, rồi với đơn đã review
đạt thì đề xuất **PIC** (dev chịu trách nhiệm chính) và báo **rủi ro** của đơn và của sprint. Bot **chỉ đọc** hệ thống
nội bộ (server dev); có PIC đề xuất thì người lên đơn nhập PIC vào hệ thống.

```bash
scrumbot review input/don/<file đơn>.md      # bước 1; kết quả: output/output.md
scrumbot assign input/don/<file đơn>.md      # bước 2, khi review đạt; ghi đè output/output.md
```

Muốn biết bot review và chọn PIC thế nào, đọc [`README.md`](README.md) mục 2. Flow 3 module Input → AI → Output và cách
thay từng module: README mục 4. TM tích hợp phần lõi vào website: README mục 6.

## 1. Cài đặt (làm một lần)

### 1.1 Cho BA/MO: cài từ file `.whl`

Người giữ tool gửi cho bạn ba thứ: file `scrumbot-<version>-py3-none-any.whl`, file `.env` và file `devs.xlsx`.

1. Cài [`uv`](https://docs.astral.sh/uv/) (uv tự tải Python nếu máy chưa có):
   - macOS, Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
2. Cài tool: `uv tool install scrumbot-<version>-py3-none-any.whl`. Mở terminal mới rồi gõ `scrumbot --help` để thử;
   không thấy lệnh thì chạy `uv tool update-shell` rồi mở lại terminal.
3. Tạo một **thư mục làm việc**, ví dụ `scrumbot/`, và đặt file vào đúng chỗ (mục 2):
   ```
   scrumbot/
   ├── .env
   └── input/
       ├── devs.xlsx
       └── don/
   ```
   **Mọi lệnh `scrumbot` chạy trong thư mục này** (`cd scrumbot` trước), vì bot tìm `.env`, `input/`, `output/`,
   `state/` ngay tại đó.
4. Chọn AI (không bắt buộc), xem mục 1.3.

**Có bản mới:** `uv tool install --force scrumbot-<version mới>-py3-none-any.whl`. Thư mục làm việc giữ nguyên.

**Token:** mọi người dùng chung một token chỉ-đọc, vì server chỉ nhận một token. Không gửi `.env` cho người ngoài team.
Khi token đổi, người giữ tool gửi `.env` mới; bot báo `API từ chối token (401)` là dấu hiệu cần file mới.

### 1.2 Cho người giữ tool: chạy trong repo và đóng gói

1. Cài Python ≥ 3.11 và `uv`, rồi trong thư mục repo chạy `uv sync`. Chạy bằng `uv run scrumbot review …` rồi `uv run scrumbot assign …`.
2. Tạo `.env`: `cp .env.example .env`, rồi điền:
   ```
   SCRUMBOT_API_TOKEN=<token TM cấp>
   SCRUMBOT_API_BASE=https://devclickup.datlt.site
   ```
   Bot từ chối địa chỉ production. **Không commit `.env`.**
3. Đóng gói cho BA/MO: `uv build --wheel`, rồi gửi `dist/scrumbot-<version>-py3-none-any.whl` kèm `.env` và
   `input/devs.xlsx`. File `.whl` chỉ chứa code, không chứa dữ liệu. Sửa `devs.xlsx` hoặc đổi token thì gửi lại cho
   từng người.

### 1.3 AI

| `--ai` | Cần gì |
|---|---|
| `gemini` (mặc định) | Lệnh `gemini` và `GEMINI_API_KEY` trên máy |
| `agy` | `~/.gemini/bin/agy` (máy của người giữ tool dùng cái này) |
| `off` | Không cần gì; mọi đơn tính là `M` (16 giờ) và không có câu hỏi của AI |

Máy không có AI mà quên `--ai off` thì bot vẫn chạy: báo `SIZE-AI-FAILED` và tính mọi đơn là `M`.

## 2. Thư mục làm việc

```
input/
├── devs.xlsx          danh sách dev                      bắt buộc
├── <tên bất kỳ>.md    luật TM (custom rule, mục 4)       tuỳ chọn, chỉ được 1 file .md ở đây
└── don/
    └── <tên đơn>.md   file đơn (mục 3.2)                 mỗi đơn một file
output/output.md       kết quả lần chạy gần nhất
state/                 cache câu trả lời AI và các sprint cũ; xoá đi thì lần sau chạy lâu hơn
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

Người giữ tool sửa file này khi có người vào hoặc rời team, có người tạm không nhận việc, hoặc có lịch nghỉ phép, rồi
gửi lại cho BA/MO.

> `Tên` viết khác hệ thống (thiếu dấu, thừa chữ) thì bot coi đó là người ngoài team: tải của dev đó bị tính thiếu
> mà **không có cảnh báo**. Copy tên từ hệ thống cho chắc.

Chỉ dev có `Nhận việc` = `Y` mới được đề xuất. QA, RnD và TM không bao giờ được đề xuất.

### 3.2 File đơn

Đặt trong `input/don/`, một đơn một file `.md`. Mẫu:

```markdown
# Game Emulator - Chỉnh sửa và bổ sung luồng auto scan game

| Trường | Giá trị |
|---|---|
| ID | |
| App | Game Emulator |
| Ưu tiên | high |
| Hạn | 16/10/2026 |

Mô tả tự do: các hạng mục cần làm, link SRS, link Figma, link tracking, …
```

| Phần | Cách bot đọc |
|---|---|
| Tên đơn | Dòng `# ` đầu tiên; không có thì lấy tên file |
| `ID` | ID đơn trên hệ thống (nếu đơn đã có) |
| `App` | Tên app, viết giống `App Name` trên hệ thống |
| `Ưu tiên` | `urgent`, `high`, `normal` hoặc `low` |
| `Hạn` | `YYYY-MM-DD` hoặc `DD/MM/YYYY` |
| Phần còn lại | Mô tả, giữ nguyên như viết |

Ô trống thì để trống, nhưng không thêm trường lạ (bot báo lỗi). Bot đọc file này **không dùng AI**. Để đơn **qua
review** (mục 5.1): có `App`, đơn `urgent`/`high` phải có `Hạn`, mô tả từ 30 ký tự trở lên (không tính link). Sửa file
sau khi review đạt thì phải review lại trước khi `assign`.

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
- File đơn để trong `input/don/`. File đơn đang được chạy thì không bao giờ bị coi là file luật.

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
| Đổi AI, cho AI chờ lâu hơn, giao vào sprint khác, chạy như thể ngày khác | Tuỳ chọn dòng lệnh (mục 5.2) |
| Ngưỡng review, ngưỡng rủi ro, số giờ của mỗi độ lớn, thứ tự tiêu chí chọn PIC | Nằm trong code. Muốn đổi thì sửa spec ([`docs/bot-spec.md`](docs/bot-spec.md) §4 và §7.3, [`docs/assignment-spec.md`](docs/assignment-spec.md) §7) rồi mới sửa code |

## 5. Chạy

### 5.1 Lên một đơn

1. Lưu file đơn vào `input/don/` (mục 3.2).
2. **Review** trong thư mục làm việc:
   ```bash
   scrumbot review input/don/req_from_ba_test.md
   ```
   rồi mở `output/output.md` (mục 6):
   - **`Review: chưa đạt`**: sửa từng mục được liệt kê trong file đơn (hoặc trên hệ thống, nếu đơn đã có ở đó), rồi
     review lại. Lúc này bot chưa gọi AI nên xong ngay.
   - **`Review: đạt`**: đọc câu hỏi của AI (nếu có). Bổ sung mô tả nếu thấy đúng, nhưng sửa file là phải review lại.
     Đơn đạt thì AI được gọi một lần cho riêng đơn này (với `agy` khoảng 1–2 phút; terminal in `Đang hỏi <AI> về mô tả
     đơn…`).
3. **Giao** khi review đạt, với đúng file đó:
   ```bash
   scrumbot assign input/don/req_from_ba_test.md
   ```
   (trong repo: `uv run scrumbot assign … --ai agy --ai-timeout 400`). Đơn chưa review đạt, hoặc đã sửa sau lần review
   đạt, thì bot dừng với mã thoát `2` và câu `Đơn chưa qua review, …`: quay lại bước 2. Lần chạy đầu trên một máy (hoặc
   sau khi xoá `state/`), AI phải ước lượng mọi đơn của sprint (với `agy` khoảng 5–6 phút cho 7 đơn). Bot nhớ câu trả
   lời theo ID và tên đơn, nên các lần sau AI chỉ ước lượng đơn trong file cùng các đơn mới hoặc đổi tên. Trong lúc
   chờ, terminal in `Đang ước lượng độ lớn bằng <AI>… (<n> đơn)`. Vội thì dùng `--ai off`.
4. Mở lại `output/output.md`: đọc PIC đề xuất và rủi ro, rồi **nhập PIC vào hệ thống**. Bot không nhớ đề xuất: nhập
   ngay để lần chạy sau tính đúng tải của dev.

| Mã review | Bot dừng khi | Cách sửa |
|---|---|---|
| `REVIEW-APP` | Đơn không có App | Ghi dòng `App` |
| `REVIEW-DUE` | Đơn `urgent`/`high` không có Hạn | Ghi dòng `Hạn` |
| `REVIEW-DESC` | Mô tả dưới 30 ký tự, không tính link | Ghi rõ các hạng mục cần làm |

Đơn đã có người làm trên hệ thống thì bot không review (`Review: không cần`); `assign` chạy được ngay, chỉ báo ai đang
giữ và rủi ro. Bot tính trên cả sprint đang chạy, nên tải và rủi ro là của sprint thật cộng thêm đơn này.

### 5.2 Tuỳ chọn

Hai lệnh nhận cùng các tuỳ chọn:

| Tuỳ chọn | Mặc định | Ý nghĩa |
|---|---|---|
| `--ai gemini\|agy\|off` | `gemini` | Công cụ AI: đặt câu hỏi (`review`), ước lượng độ lớn (`assign`) |
| `--ai-timeout GIÂY` | `180` | Số giây chờ AI; với `agy` nên để `400` |
| `--ai-model TÊN` | | Model truyền thẳng cho công cụ AI |
| `--sprint-id ID` | sprint đang chạy | Đặt đơn vào một sprint khác |
| `--today NGÀY` | hôm nay | Chạy như thể hôm nay là ngày này (`YYYY-MM-DD` hoặc `DD/MM/YYYY`) |
| `--input THƯ_MỤC` | `input/` | Nơi tìm `devs.xlsx` và file luật |
| `--devs FILE` | `input/devs.xlsx` | File dev |
| `--rules FILE` | file `.md` duy nhất trong `input/` | File luật TM |
| `--out THƯ_MỤC` | `output/` | Nơi ghi `output.md` |
| `--state THƯ_MỤC` | `state/` | Câu trả lời AI, các lần review đạt, cache các sprint cũ. Hai lệnh phải dùng chung thư mục này |
| `-v` | tắt | In chi tiết lỗi và trao đổi với AI |

Xem đủ: `scrumbot review --help`.

## 6. Output: `output/output.md`

**Sau `review`** (`# Review đơn: …`): mục `Review: chưa đạt` liệt kê mã và cách sửa từng mục, hoặc `Review: đạt` với
câu hỏi của AI cho người lên đơn (tối đa 2, chỉ để nhắc) và lời nhắc chạy `assign`; cuối là bảng thông tin đơn (đơn mới
hay đã có trên hệ thống, App, ưu tiên, hạn, mô tả đúng như AI đã đọc). Không có PIC, không có rủi ro.

**Sau `assign`** (`# Giao đơn: …`, đọc từ trên xuống):

| Mục | Nội dung |
|---|---|
| **Kết luận** | PIC đề xuất, lý do một câu, 2 người dự phòng, độ lớn AI ước lượng, số rủi ro liên quan. Đơn đã có người làm thì bot giữ nguyên, không đề xuất người khác |
| **Thông tin đơn** | Đơn mới hay đơn đã có trên hệ thống, App, ưu tiên, hạn, loại đơn và hạng mục AI nhận ra, mô tả đúng như AI đã đọc |
| **So sánh dev** | Mỗi dev một dòng: level, đã làm app chưa, số đơn, giờ việc còn lại / sức chứa, việc dở sprint trước, ngày nghỉ, vai trò (PIC, dự phòng) |
| **Rủi ro và phương án dự phòng** | Rủi ro của đơn, của PIC và của sprint, mỗi dòng có **Phòng ngừa** và **Nếu xảy ra**, ai xử lý, hạn xử lý |
| **Rủi ro kỹ thuật** | AI nhận xét, chỉ để tham khảo |
| **Cảnh báo dữ liệu** | Dữ liệu thiếu hoặc lạ |

Lần chạy sau **ghi đè** file này: muốn giữ thì copy ra chỗ khác, hoặc dùng `--out <thư mục khác>`.

### 6.1 Độ lớn đơn

| Độ lớn | Giờ tính vào tải |
|---|---|
| `S` | 4 |
| `M` | 16 |
| `L` | 32 |
| `XL` | 64 |

AI ước lượng đơn trong file từ tên và mô tả, các đơn khác của sprint từ tên đơn (API chưa trả mô tả). AI lỗi, hết giờ
hoặc tắt thì đơn tính là `M` và lần chạy vẫn tiếp tục.

### 6.2 Terminal và mã thoát

Terminal in tóm tắt: nguồn dữ liệu, file luật, lịch sử, đơn; rồi với `review` là kết quả review và lệnh tiếp theo, với
`assign` là độ lớn, PIC đề xuất, rủi ro, các cảnh báo; cuối là đường dẫn kết quả.

| Mã thoát | Khi nào |
|---|---|
| `0` | Đã ghi `output.md`: `review` đạt hay chưa đạt; `assign` (có hoặc không có cảnh báo, có hoặc không có AI) |
| `2` | Lỗi input hoặc lỗi API, gõ thiếu lệnh, hoặc `assign` khi đơn chưa review đạt. Không ghi kết quả. Câu báo lỗi tiếng Việt chỉ rõ file, dòng, cột |
| `130` | Bấm Ctrl+C |

## 7. Lỗi thường gặp

| Bạn thấy | Làm gì |
|---|---|
| `scrumbot: command not found` | `uv tool update-shell`, mở terminal mới (mục 1.1) |
| `Không có file đơn '…'` | Sai đường dẫn file đơn, hoặc chưa `cd` vào thư mục làm việc |
| `Không có thư mục input 'input'` | Chưa `cd` vào thư mục làm việc (mục 1.1) |
| `Không tìm thấy file devs.xlsx …` | Thiếu `input/devs.xlsx`, hoặc file bị đổi tên (ví dụ `devs (1).xlsx`) |
| `Thiếu SCRUMBOT_API_TOKEN …` | Thiếu `.env` trong thư mục làm việc (mục 1.1) |
| `API từ chối token (401)` | Token đã đổi: xin người giữ tool `.env` mới |
| `API vẫn giới hạn tải (429)` hoặc lỗi server (5xx) | Chạy lại sau ít phút |
| `Có nhiều … Chỉ định một file bằng --rules` | Chỉ để một file luật `.md` trong `input/`, hoặc dùng `--rules` |
| `File '…' không có bảng luật …` | Một file `.md` không phải luật (thường là file đơn) nằm thẳng trong `input/`: chuyển nó vào `input/don/` |
| `File đơn … trường '…' không hợp lệ` | Bảng trong file đơn chỉ dùng `ID`, `App`, `Ưu tiên`, `Hạn` |
| `Có <k> đơn tên '…' trong …` | Nhiều đơn trùng tên: ghi `ID` của đơn vào file đơn |
| `Không có đơn gốc ID '…' trong …` | ID sai, hoặc đơn không thuộc sprint đang chạy: sửa ID, để trống ID, hoặc dùng `--sprint-id` |
| `Đơn chưa qua review, hoặc đã đổi sau lần review đạt gần nhất …` | Chạy `scrumbot review` với đúng file đó (cùng `--state`) cho tới khi đạt, rồi mới `assign`. Sửa file đơn, hoặc App/Hạn trên hệ thống đổi, thì phải review lại |
| AI chạy lâu hoặc hết giờ | Tăng `--ai-timeout 400`, hoặc chạy `--ai off` |
| Một dev có tải thấp bất thường | `Tên` trong `devs.xlsx` viết khác hệ thống (mục 3.1), hoặc PIC lần trước chưa được nhập vào hệ thống |
| Muốn xem bot làm gì khi lỗi | Thêm `-v` |
