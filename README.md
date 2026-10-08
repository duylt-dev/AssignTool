# assigntool

Tool dòng lệnh **giao dev phụ trách (PIC)** cho các đơn còn trống của board Maintain. Đơn do BA lên trên hệ thống nội
bộ. Chạy tool lúc nào cũng được trong sprint (đầu sprint, và mỗi khi BA lên đơn mới): đơn đã có người thì giữ nguyên,
đơn trống thì tool chọn người và ghi lý do vào file báo cáo.

Mục tiêu là tool tự ghi `Người làm` thẳng vào hệ thống, không cần duyệt. Việc đó cần API và một token cho tool, hiện
chưa có (`confirm.md` O8). Vì vậy hiện tại tool ghi kết quả ra file Excel, và người có quyền nhập vào hệ thống. Tool
không sửa file input.

> **Trạng thái (2026-10-07):** chạy được với file lịch sử Tech manager, giới hạn tải theo số đơn, backtest và file
> luật của TM (154 test pass).

## 1. Cài đặt

| Cần | Ghi chú |
|---|---|
| Python ≥ 3.11 và [`uv`](https://docs.astral.sh/uv/) | Chạy `uv sync` một lần trong thư mục repo để cài thư viện. |
| Gemini CLI (`gemini`) trong `PATH` | Dùng để AI ước lượng độ lớn đơn. |
| Biến môi trường `GEMINI_API_KEY` với một key hợp lệ | Gemini CLI không còn đăng nhập bằng tài khoản Google được; phải có key. |

Thiếu Gemini CLI hoặc key thì tool **vẫn chạy và vẫn ra báo cáo**, nhưng mọi đơn được tính cùng độ lớn `M` và sheet
`Cảnh báo` ghi lý do.

## 2. Chạy nhanh

1. Đặt file vào `input/` (mục 3). Repo đã có sẵn file export Sprint 6–10, file lịch sử Tech manager tháng 2–10/2026
   và `devs.xlsx` của 4 dev.
2. Chạy:

   ```bash
   uv run assigntool
   ```

3. Mở file `output/assignment_<sprint>_<thời gian>.xlsx` (mục 4): người được giao ở sheet `Phân công`, các dòng cần
   xử lý ở sheet `Cảnh báo`. Nhập `PIC` vào hệ thống nội bộ.

Các cách chạy khác:

```bash
uv run assigntool --ai off                  # không gọi AI; mọi đơn tính là M (16h)
uv run assigntool --ai agy                  # dùng Antigravity thay cho gemini (máy dev)
uv run assigntool --sprint path/export.xlsx # chỉ định file export khi input/ có nhiều file .xlsx
uv run assigntool --backtest                # giao lại các sprint cũ trong file lịch sử và so với TM (mục 4.2)
uv run assigntool --rules path/luat.md      # dùng file luật TM nằm ngoài input/ (mục 3.5)
uv run assigntool --today 2026-10-19        # chạy như thể hôm nay là 19/10/2026 (lịch sử và ngày áp luật)
uv run assigntool --help                    # mọi tuỳ chọn (mục 6)
```

## 3. Input

```
input/
├── <file export sprint>.xlsx       bắt buộc · file .xlsx có sheet "Sprint N"
├── devs.xlsx                       bắt buộc
├── <file lịch sử Tech manager>     nên có · .xlsx (không có sheet "Sprint N") hoặc .csv · tối đa 1 file
└── <file luật TM>.md               không bắt buộc · tối đa 1 file (mục 3.5)
```

Mỗi lần chạy cần export lại **cả hai file** từ hệ thống: file export sprint (đơn cần giao, mô tả, việc dở) và file
Tech manager (lịch sử ai làm app nào). Tool nhận ra file theo **nội dung**, không theo tên: file `.xlsx` có sheet
`Sprint N` là file export sprint; file `.xlsx` còn lại hoặc file `.csv` là file lịch sử; file `.md` là file luật. Có 0
hoặc nhiều hơn một file ứng viên thì tool dừng, liệt kê các file tìm thấy và chỉ cờ cần dùng (`--sprint`, `--devs`,
`--history`, `--rules`); tool không đoán. File bắt đầu bằng `~$` (file khoá khi Excel đang mở) và `.` bị bỏ qua. Khi export lại, **thay** file cũ bằng
file mới, đừng để cả hai trong `input/`.

### 3.1 File export sprint (`.xlsx`)

File export của tool nội bộ, giữ nguyên định dạng, không cần sửa tay.

- Mỗi sprint là một sheet tên `Sprint N`. Sheet có tên khác bị bỏ qua.
- **Sheet được giao** là `Sprint N` có N lớn nhất (đổi bằng `--sheet`). Sheet `Sprint N-1` là **sprint trước**,
  dùng để tính việc dở của từng dev. Các sheet nhỏ hơn N là **lịch sử** khi không có file lịch sử (mục 3.3).
- Dòng 3 chứa `Thời gian: YYYY-MM-DD → YYYY-MM-DD`: ngày bắt đầu và kết thúc sprint, dùng để tính ngày nghỉ. Không
  có dòng này thì ngày nghỉ bị bỏ qua.
- Dòng tiêu đề là dòng đầu tiên trong 10 dòng đầu có ô cột A là `STT`. Cột được tìm **theo tên**, thứ tự cột không
  quan trọng. Dữ liệu chạy tới dòng đầu tiên mà `STT` không phải số (dòng tổng cuối bảng bị bỏ qua).
- Task con thụt lề bằng `└` là subtask: không được giao, không dùng để đo độ lớn.

| Cột | Bắt buộc | Tool dùng để |
|---|---|---|
| `STT` | ✓ | Định danh dòng trong báo cáo và cảnh báo. |
| `Task` | ✓ | Tiêu đề đơn, gửi cho AI. |
| `Loại` | ✓ | `Task` là đơn cần giao; `Subtask` bị bỏ qua. Giá trị khác: bỏ dòng và cảnh báo. |
| `App Name.` | ✓ | App của đơn, để biết ai từng làm app đó. Không phân biệt hoa thường và khoảng trắng. |
| `Trạng thái` | ✓ | Chỉ dùng ở sheet sprint trước: dòng có trạng thái `qa - need fix`, `all issue`, `in progress`, `ready to progress`, `need to be clean`, `internal - cant fix`, `internal - need fix` hoặc `đã ro` tính là việc dở. `qa - cant fix`, `pending` và các trạng thái khác không tính. |
| `Người làm` | ✓ | Đã có tên (cách nhau bằng dấu phẩy) thì đơn là **giao sẵn**: tool giữ nguyên, chỉ cộng tải cho dev. Trống thì tool giao. |
| `Ưu tiên` | ✓ | `urgent`, `high`, `normal`, `low` hoặc trống (= normal). Đơn gấp được xét trước. |
| `Hạn` | ✓ | Thứ tự xét đơn (hạn sớm trước, trống sau). |
| `Ngày tạo` | ✓ | Thứ tự xét đơn. |
| `Mô tả` | — | Gửi cho AI sau khi thay mọi link bằng `[link]` và cắt còn 600 ký tự. |
| `Ước lượng (h)` | — | **Bỏ qua** ở sheet được giao: tool không dùng ước lượng do người nhập. |
| Cột khác | — | Chép nguyên sang báo cáo. |

Ở sheet sprint trước chỉ cần 3 cột `Loại`, `Trạng thái`, `Người làm`.

### 3.2 `devs.xlsx`

Tự quản lý, chỉ sửa khi có người vào/ra team hoặc nghỉ phép. Sheet đầu tiên, tiêu đề ở dòng 1, mỗi dòng một dev.

| Cột | Bắt buộc | Giá trị |
|---|---|---|
| `Tên` | ✓ | Họ tên **đúng như tool nội bộ ghi** trong cột `Người làm`. Không trùng. |
| `Mã` | ✓ | Mã ngắn hiện trong báo cáo, vd `LinhNV`. Không trùng. |
| `Level` | ✓ | `junior`, `junior+`, `middle`, `middle+`, `senior` (không phân biệt hoa thường). |
| `Nhận việc` | ✓ | `Y` hoặc `N`. `N` tạm đưa dev ra khỏi danh sách giao mà không cần xoá dòng. |
| `Ngày nghỉ` | — | Các ngày nghỉ trong sprint, cách nhau bằng dấu phẩy: `YYYY-MM-DD` hoặc `DD/MM/YYYY`. |

Ví dụ:

| Tên | Mã | Level | Nhận việc | Ngày nghỉ |
|---|---|---|---|---|
| Ngọc Văn Linh | LinhNV | middle+ | Y | |
| Nguyễn Nhật Minh | MinhNM | middle | Y | 2026-10-08, 09/10/2026 |
| Trần Đức An | AnTD | junior+ | Y | |
| Bùi Văn Tiến | TiếnBV | junior | Y | |

- Chỉ dev có `Nhận việc` = `Y` được giao. Dev nghỉ trọn mọi ngày làm việc (thứ 2–6) của sprint bị loại khỏi lần
  giao đó; nghỉ một phần chỉ dùng để phân định khi hai người ngang nhau.
- Người không có trong file (QA, RnD, Tech Manager…) bị bỏ qua hoàn toàn, không cảnh báo. Vì vậy nếu tên một dev bị
  gõ khác trong file export (thiếu dấu, thừa chữ), tool coi đó là người lạ và tính thiếu tải cho dev đó mà không báo.

### 3.3 File lịch sử Tech manager (nên có)

File export list "Tech manager" từ CSDL hệ thống nội bộ, giữ nguyên định dạng. Tool dùng nó để biết ai đã làm app nào
và version nào gần nhất.

- `.xlsx`: mỗi tháng một sheet, tiêu đề ở dòng 1. Sheet không có cột `Ngày lên đơn` (vd sheet `Tổng hợp`) bị bỏ qua.
  Hoặc `.csv` với cùng các cột: UTF-8 có hoặc không BOM, phân cách `,` hoặc `;`, ngày `YYYY-MM-DD` hoặc `DD/MM/YYYY`.
- Cột bắt buộc: `Ngày lên đơn`, `Tên task`, `Loại`, `Task cha`, `App Name`, `Người làm`, `Sprint`. Cột khác bị bỏ qua.
- Chỉ dùng **đơn gốc**: `Loại` = `Task` và `Task cha` trống. Subtask và bug bị bỏ qua.
- Lấy cả đơn board MVP / nghiên cứu và đơn không có sprint: dev làm MVP của app nào thì cũng là quen app đó. Đơn MVP
  không tính vào tải.
- Bỏ các đơn của sprint đang giao (một đơn không tự làm lịch sử cho chính nó), đơn lên sau hôm nay, và đơn của sprint
  chưa bắt đầu.
- Nhãn sprint đọc dạng `Sprint 10 (10/6 - 10/17)`, một ô có thể có nhiều nhãn. Sprint dài tối đa 21 ngày là sprint
  Maintain, dài hơn là MVP / nghiên cứu (export chưa có cột board).
- Nếu sau này export có thêm cột `Ước lượng (h)`, số giờ đó được gửi cho AI làm mốc so sánh. Hiện file chưa có cột này.
- **Không có file lịch sử** thì tool lấy mọi sheet sprint cũ hơn trong file export làm lịch sử (file mẫu: Sprint 6–9)
  và ghi một dòng INFO. Có file lịch sử thì chỉ dùng file đó; hai nguồn không bao giờ gộp, để không đếm trùng.

### 3.4 Dữ liệu gửi cho AI

Tool gọi AI **một lần** cho cả sprint, chỉ để xếp độ lớn từng đơn. AI không chọn người.

- Gửi đi: STT, app, ưu tiên, tiêu đề, mô tả (đã bỏ link và cắt ngắn) của các đơn sprint này, và tối đa 30 đơn cũ có
  số giờ (app · tiêu đề · số giờ) làm mốc; file Tech manager hiện chưa có số giờ nên phần mốc trống. **Không gửi tên
  người, không gửi link.**
- AI chạy ở chế độ chỉ đọc, trong một thư mục tạm rỗng, nên không đọc được `input/`. Quá 180 giây thì bị dừng
  (đổi bằng `--ai-timeout`).
- AI lỗi, hết giờ hoặc trả sai định dạng: mọi đơn (hoặc các đơn bị thiếu) tính là `M`, báo cáo vẫn được ghi.
- Cùng một input, hai lần chạy có thể ra độ lớn khác nhau. Độ lớn chỉ ảnh hưởng tới tiêu chí số giờ (mục 5), không
  quyết định ai được xét. Độ lớn và lý do của AI có trong báo cáo để kiểm tra.

### 3.5 File luật TM (`.md`, không bắt buộc)

TM dùng file này để điều khiển việc giao mà không phải sửa code: giữ một người cho một app, cho một người nghỉ nhận
đơn, giới hạn số đơn, hoặc ưu tiên một người học app. Luật là **một bảng markdown có cột cố định**; chữ ngoài bảng là
ghi chú tự do, tool bỏ qua. Tool đọc bảng trực tiếp, **AI không đọc luật** và không chọn người.

```markdown
| Loại       | Dev    | App       | Số đơn | Từ ngày    | Đến ngày   | Ghi chú                 |
|------------|--------|-----------|--------|------------|------------|-------------------------|
| Chỉ định   | LinhNV | AR Dog    |        |            |            | Linh giữ AR Dog         |
| Không giao | MinhNM |           |        | 06/10/2026 | 17/10/2026 | Minh làm MVP sprint này |
| Tối đa đơn | AnTD   |           | 1      | 06/10/2026 | 17/10/2026 |                         |
| Ưu tiên    | TiếnBV | PS Remote |        |            |            | Cho Tiến học PS Remote  |
```

| Loại | Tác dụng | Cột cần |
|---|---|---|
| `Chỉ định` | Dev đó nhận mọi đơn của app, kể cả khi đang giữ nhiều đơn hơn người khác (vượt cân tải). | `App` |
| `Không giao` | Dev không nhận đơn của app; `App` trống là không nhận đơn nào. | — |
| `Tối đa đơn` | Dev đã giữ đủ số đơn (tính cả đơn giao sẵn) thì không nhận thêm; giới hạn được cả `Chỉ định`. | `Số đơn` |
| `Ưu tiên` | Dev được ưu tiên trước cả người quen app, nhưng vẫn trong giới hạn cân tải. | `App` |

- `Dev` là `Mã` trong `devs.xlsx`. Mỗi dòng một dev, một app; muốn hai app thì viết hai dòng. Có thể chia luật thành
  nhiều bảng (vd mỗi sprint một bảng), miễn bảng có cột `Loại` và `Dev`.
- `Từ ngày` / `Đến ngày` (`DD/MM/YYYY` hoặc `YYYY-MM-DD`) để trống là không giới hạn. Một lần chạy dùng luật có hiệu
  lực **hôm nay, hoặc ngày bắt đầu sprint nếu chạy trước sprint** (vd chạy thứ Sáu trước Sprint 10 thì luật ghi ngày
  của Sprint 10 vẫn áp).
- Luật không bao giờ đổi đơn đã giao sẵn. Cột `Lý do` ghi luật nào đã quyết định, kèm số dòng và ghi chú, vd
  `Luật TM dòng 5: chỉ định LinhNV cho AR Dog (Linh giữ AR Dog) · …`.
- Luật viết sai (loại lạ, mã dev không có trong `devs.xlsx`, ngày sai, thiếu cột cần, hai luật mâu thuẫn như hai
  `Chỉ định` khác người cho cùng một app) thì tool **dừng** và báo tên file, số dòng. Luật đúng nhưng dev đang nghỉ cả
  sprint hoặc `Nhận việc` = `N` thì bị bỏ qua, kèm cảnh báo.
- Trước khi dùng một luật mới, chạy `uv run assigntool --backtest` để xem luật đó làm tỉ lệ khớp với TM thay đổi thế
  nào (mục 4.2).

## 4. Output

### 4.1 Báo cáo giao việc

Mỗi lần chạy ghi **một file mới** `output/assignment_<sprint>_<YYYYMMDD-HHMMSS>.xlsx`, vd
`assignment_sprint-10_20261006-143000.xlsx` (đổi thư mục bằng `--out`). Báo cáo cũ đang mở trong Excel không cản lần
chạy sau. Tool không sửa file nào trong `input/`.

### Sheet `Phân công`

Mỗi đơn (dòng `Task` của sprint được giao) một dòng, theo thứ tự `STT`. Giữ nguyên mọi cột gốc (kể cả `Người làm`
gốc), thêm các cột:

| Cột | Nội dung |
|---|---|
| `Độ lớn` | `S`, `M`, `L` hoặc `XL`; có thêm ` (mặc định)` khi AI không ước lượng được đơn này. |
| `Giờ ước tính` | 4, 16, 32 hoặc 64. |
| `Lý do độ lớn` | Lý do của AI; trống khi là mặc định. |
| `PIC` | Họ tên PIC. Với đơn giao sẵn: giữ `Người làm` gốc. |
| `Mã PIC` | Mã của PIC; với đơn giao sẵn là mã các dev trong danh sách được ghi tên. |
| `Nguồn` | `Đã giao sẵn` hoặc `Tool đề xuất`. |
| `Lý do` | Vì sao chọn người này (mục 5). Đơn giao sẵn ghi `Đã giao sẵn trong file`. |
| `Dự phòng 1`, `Dự phòng 2` | Hai người thay thế tốt nhất; trống với đơn giao sẵn. |

Ví dụ một ô `Lý do`:

```
Làm version gần nhất của PS Remote (Sprint 9 (9/21 - 10/2): 1.1.1 - Fix ads/FIx luồng/ fix policy) · Đơn urgent →
ưu tiên middle trở lên · Tải sprint này: 0h (0 đơn) · Việc dở Sprint 9: 0
```

### Sheet `Cảnh báo`

Cột `Mức` · `Mã` · `Vị trí` · `Nội dung`; WARN xếp trước INFO. Không có vấn đề gì thì sheet chỉ có một dòng
`Không có cảnh báo`. Cảnh báo không làm dừng tool.

| Mã | Mức | Khi nào | Nên làm gì |
|---|---|---|---|
| `SIZE-AI-FAILED` | WARN | Gọi AI thất bại; mọi đơn tính là M. | Kiểm tra `gemini` và `GEMINI_API_KEY`, chạy lại (thêm `-v` để xem lỗi chi tiết). |
| `SIZE-AI-INVALID` | WARN | AI không trả độ lớn hợp lệ cho một số đơn; các đơn đó tính là M. | Chạy lại, hoặc tự xem độ lớn các đơn được liệt kê. |
| `APP-MISSING` | WARN | Đơn không có `App Name`; coi như app chưa ai làm. | Điền App Name trên tool nội bộ, export lại. |
| `PRIORITY-UNKNOWN` | WARN | `Ưu tiên` không phải urgent/high/normal/low/trống; coi như normal. | Sửa ưu tiên trên tool nội bộ. |
| `DUE-BEFORE-CREATED` | WARN | `Hạn` trước `Ngày tạo`. | Kiểm tra hạn của đơn. |
| `TYPE-UNKNOWN` | WARN | `Loại` không phải Task/Subtask; dòng bị bỏ qua. | Sửa loại trên tool nội bộ. |
| `PREV-SPRINT-MISSING` | WARN | Không có sheet `Sprint N-1`; coi như không ai còn việc dở. | Export kèm sheet sprint trước. |
| `HISTORY-MISSING` | WARN | Không có file lịch sử và không có sheet sprint cũ; coi như chưa ai làm app nào. | Thêm file lịch sử Tech manager. |
| `HISTORY-FROM-WORKBOOK` | INFO | Không có file lịch sử; dùng các sheet sprint cũ làm lịch sử. | Nên thêm file lịch sử Tech manager: nhiều lịch sử hơn thì giao đúng hơn. |
| `DEV-ON-LEAVE` | INFO | Một dev nghỉ cả sprint nên không được giao. | Không cần làm gì. |
| `RULE-DEV-UNAVAILABLE` | WARN | Luật `Chỉ định` / `Ưu tiên` nhắc tới dev đang nghỉ cả sprint hoặc `Nhận việc` = `N`; luật bị bỏ qua. | Sửa hoặc xoá dòng luật đó. |
| `RULE-NO-CANDIDATE` | WARN | Luật `Không giao` / `Tối đa đơn` loại hết dev khỏi một đơn; đơn đó được giao như khi không có hai loại luật này. | Xem lại người được giao cho đơn đó, hoặc nới luật. |

### Sheet `Tải dev`

Mỗi dev trong danh sách một dòng (kể cả dev nghỉ cả sprint): `Mã`, `Tên`, `Level`, `Việc dở sprint trước`,
`Ngày nghỉ`, `Đơn giao sẵn`, `Đơn tool đề xuất`, `Tổng đơn`, `Tổng giờ ước tính`, `Danh sách đơn` (tiêu đề kèm độ
lớn, mỗi đơn một dòng) và `App đã làm`.

### Màn hình

Ví dụ trên file mẫu với `--ai off`:

```
Luật TM: không có
Lịch sử: file Tech_manager_T2-T10_2026.xlsx (172 đơn gốc)
Sprint: Sprint 10
Độ lớn: tắt AI (mọi đơn M)
Đơn: 6 · giao sẵn: 5 · tool đề xuất: 1 · cảnh báo: 0 WARN, 0 INFO
STT 10 · Roblox skin 1.0.4 - Fix luồng/Add Ads/Fix UI [M] → AnTD (dự phòng: MinhNM, TiếnBV)
Báo cáo: output/assignment_sprint-10_20261007-160752.xlsx
```

Khi có AI, trước đó in thêm `Đang ước lượng độ lớn bằng gemini…` và dòng độ lớn thành `Độ lớn: AI (gemini, 6/6 đơn)`
(số đơn AI ước lượng được trên tổng số đơn). Có file luật thì dòng đầu là
`Luật TM: file luat.md (4 luật, 3 có hiệu lực ngày 06/10/2026)`. Mỗi cảnh báo WARN được in một dòng `WARN <mã>: <nội dung>`. Chi tiết đầy
đủ nằm trong file Excel.

| Exit code | Ý nghĩa |
|---|---|
| `0` | Đã ghi báo cáo (có hay không có cảnh báo, có hay không có AI). |
| `2` | Lỗi input hoặc sai cách gọi; **không** ghi báo cáo. Thông báo `Lỗi: …` chỉ rõ file, sheet, dòng hoặc cột. |
| `130` | Dừng bằng Ctrl+C. |

Các lỗi input dừng tool: thiếu file hoặc có nhiều file ứng viên; file `.xlsx` không mở được; thiếu cột bắt buộc;
`Level` sai; `Nhận việc` không phải `Y`/`N`; trùng `Tên` hoặc `Mã`; ngày không đọc được; không còn dev nào để giao sau
khi trừ người nghỉ; file luật viết sai hoặc có hai luật mâu thuẫn (mục 3.5).

### 4.2 Backtest: tool có giao giống TM không

```bash
uv run assigntool --backtest
```

Chỉ cần file lịch sử Tech manager và `devs.xlsx`. Với mỗi sprint Maintain trong file lịch sử (file mẫu: 16 sprint,
tháng 1–10/2026), tool xoá `Người làm` của các đơn TM đã giao cho dev trong danh sách, giao lại theo đúng luật ở mục 5,
rồi so với người TM đã giao.

- Đơn được giao lại theo **ngày lên đơn**, như khi chạy tool mỗi lần BA lên đơn: đơn lên trước ngày bắt đầu sprint
  được giao cùng lúc vào ngày bắt đầu, mỗi ngày sau là một lần chạy. Lịch sử của mỗi lần chạy chỉ gồm việc đã có
  trước ngày đó.
- Đơn mang sang từ sprint trước giữ nguyên người TM giao (không so sánh). Đơn không có dev trong danh sách bị bỏ qua.
- **Mọi đơn tính là M và việc dở bằng 0**: file Tech manager không có mô tả để AI ước lượng, và trạng thái trong file
  là trạng thái hôm nay, không phải lúc sprint đó bắt đầu.
- **Khớp** khi người tool chọn là một trong các dev TM đã giao. Lệch chưa chắc là sai: luật cố ý cân tải.
- Có file luật TM (mục 3.5) thì backtest **áp luật** theo `Từ ngày` / `Đến ngày` so với ngày giao lại từng đơn. Luật
  rút ra từ chính lịch sử thì tất nhiên làm tỉ lệ khớp tăng; khi đó tỉ lệ đo cả luật của TM lẫn luật của tool.

File `output/backtest_<thời gian>.xlsx` có hai sheet: `Theo sprint` (số đơn so sánh, số khớp, tỉ lệ, số đơn mang
sang, số đơn chịu tác động của luật TM; dòng cuối là tổng) và `Theo đơn` (mỗi đơn: TM giao ai, tool giao ai, khớp hay
không, lý do của tool, các dòng luật TM đã tác động).

Kết quả trên file mẫu, không có file luật: **khớp 43/92 đơn (47%)**. Các sprint tháng 1–5 (ít lịch sử) chỉ khớp 3/19;
từ Sprint 1 (tháng 5) khớp 40/73 (55%); Sprint 9 khớp 8/11, Sprint 10 khớp 4/5. Chi tiết và cách đọc: spec §13. Thêm
hai dòng `Chỉ định LinhNV` cho AR Dog và VPN thì khớp 50/92 (54%): AR Dog 9/9, VPN 6/7 (chạy thử ngày 2026-10-07).

## 5. Tool chọn PIC thế nào

1. **AI xếp độ lớn** từng đơn, kể cả đơn giao sẵn (vì chúng cũng tính vào tải):

   | Hạng | Giờ | Ý nghĩa |
   |---|---|---|
   | `S` | 4 | Chỉ một việc nhỏ: một crash, một lần sửa policy hoặc store, đổi text/config. |
   | `M` | 16 | Hai đến ba ngày: một việc cỡ tính năng, hoặc hai ba việc nhỏ. |
   | `L` | 32 | Khoảng một tuần: nhiều việc, vd sửa ads hoặc IAP kèm sửa luồng hoặc UI. |
   | `XL` | 64 | Hơn một tuần: tính năng mới, SDK mới, app mới, hoặc rất nhiều việc cùng lúc. |

   AI được dặn rằng mỗi đơn là một version của app, PIC làm hết mọi việc ghi trong tiêu đề và mô tả. Để AI hiểu thang
   giờ của team, prompt kèm tối đa 30 đơn cũ có `Ước lượng (h)`: lấy từ file lịch sử nếu file có cột giờ, không thì
   lấy từ các sheet sprint cũ trong file export sprint (file Tech manager hiện chưa có cột giờ).

2. **Đơn giao sẵn giữ nguyên**, chỉ cộng giờ vào tải của dev được ghi tên.
3. **Đơn trống được xét lần lượt**: urgent → high → normal → low, rồi hạn sớm, rồi ngày tạo, rồi `STT`.
4. Với mỗi đơn, bỏ những dev mà luật TM (mục 3.5) không cho nhận đơn này (`Không giao`, `Tối đa đơn`). Có luật
   `Chỉ định` cho app thì giao luôn cho người đó. Nếu không, chỉ xét dev có **số đơn không vượt quá người ít đơn nhất
   + 1** (để một người quen nhiều app không ôm hết). Tính theo số đơn chứ không theo giờ, vì độ lớn do AI ước lượng
   thay đổi giữa các lần chạy. Trong số đó, chọn người tốt nhất theo thứ tự ưu tiên:
   0. Được luật TM `Ưu tiên` cho app này.
   1. Đã làm version gần nhất của app → từng làm app → chưa làm.
   2. Đơn urgent/high, hoặc app chưa ai trong team làm: ưu tiên level middle trở lên.
   3. Ít giờ việc hơn trong sprint này.
   4. Ít việc dở hơn từ sprint trước.
   5. Ít ngày nghỉ hơn.
   6. Level cao hơn, rồi theo `Mã` (để kết quả luôn giống nhau).

   Hai người tiếp theo theo cùng thứ tự (bỏ qua giới hạn tải) là dự phòng.
5. Cột `Lý do` ghi lại từng bước trên. Nếu người quen app hơn bị loại vì giới hạn tải, lý do cũng ghi rõ, vd
   `AnTD quen app hơn nhưng đang có 3 đơn (cân tải)`.

## 6. Tuỳ chọn dòng lệnh

| Tuỳ chọn | Mặc định | Ý nghĩa |
|---|---|---|
| `--input DIR` | `input/` | Thư mục tìm file input. |
| `--sprint FILE` | file `.xlsx` duy nhất có sheet `Sprint N` | File export sprint. |
| `--devs FILE` | `<input>/devs.xlsx` | File dev. |
| `--history FILE` | file `.xlsx` không có sheet `Sprint N`, hoặc file `.csv`; không có thì dùng sheet sprint cũ | File lịch sử Tech manager. |
| `--rules FILE` | file `.md` duy nhất trong `input/`; không có thì không dùng luật | File luật TM (mục 3.5). |
| `--sheet NAME` | `Sprint N` lớn nhất | Sheet cần giao, vd `--sheet "Sprint 9"`. |
| `--today DATE` | hôm nay | Chạy như thể hôm nay là ngày này (`YYYY-MM-DD` hoặc `DD/MM/YYYY`): lịch sử chỉ gồm việc có trước ngày đó, luật áp theo ngày đó. Dùng để chạy lại một sprint cũ hoặc bộ đánh giá trong `eval/`. Tên file báo cáo vẫn theo giờ thật. |
| `--out DIR` | `output/` | Thư mục ghi báo cáo; tự tạo nếu chưa có. |
| `--ai gemini\|agy\|off` | `gemini` | Công cụ AI. `agy` cho máy dev; `off` tính mọi đơn là M. |
| `--ai-model NAME` | mặc định của công cụ AI | Tên model truyền thẳng cho công cụ AI. |
| `--ai-timeout SECONDS` | `180` | Số giây chờ AI. |
| `--backtest` | tắt | Giao lại các sprint Maintain trong file lịch sử và so với TM (mục 4.2), có áp file luật. Bỏ qua `--sprint`, `--sheet`, `--today`, `--ai…`. |
| `-v` | tắt | In traceback khi lỗi và nội dung trao đổi với AI. |

## 7. Dành cho người phát triển

```bash
uv run ruff check . && uv run ruff format --check . && uv run pytest   # chạy sau mọi thay đổi code
ASSIGNTOOL_TEST_AI=gemini uv run pytest -m ai                         # thêm 1 lần gọi AI thật (cần mạng và key)
```

Test nghiệm thu (`tests/test_real_input.py`) chạy trên `input/Maintain_update_Sprint_10_va_9.xlsx` và
`input/Tech_manager_T2-T10_2026.xlsx`; thiếu file nào thì các test dùng file đó được bỏ qua kèm lý do.

Bộ đánh giá 5 case nằm trong [`eval/`](eval/README.md): 2 sprint thật dựng lại (đo độ khớp với TM và độ lớn AI so với
giờ thật) và 3 kịch bản giả lập (giữa sprint và nghỉ phép, luật TM, dữ liệu bẩn). Chạy lại sau mỗi thay đổi luật:

```bash
uv run python eval/build_cases.py   # sinh lại input của 5 case
uv run python eval/run_eval.py      # chạy tool (1 lần --ai off + 3 lần gemini mỗi case), ghi eval/results/<giờ>/bang-diem.md
```

| Tài liệu | Nội dung |
|---|---|
| [`docs/assignment-spec.md`](docs/assignment-spec.md) | Spec đầy đủ: định dạng input, ước lượng bằng AI, luật chọn PIC, nội dung lý do, cảnh báo, output, kết quả kỳ vọng trên file mẫu |
| [`confirm.md`](confirm.md) | Các quyết định đã chốt (D), mặc định (A) và câu hỏi còn mở (O) |
| [`docs/python-best-practices.md`](docs/python-best-practices.md) | Quy tắc viết code |
