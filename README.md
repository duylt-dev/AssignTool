# assigntool

Tool dòng lệnh đề xuất **dev phụ trách (PIC)** cho từng đơn đầu sprint. Đơn do BA lên trên tool nội bộ. Tech Manager
export danh sách đơn ra Excel, chạy tool, đọc đề xuất kèm lý do trong file báo cáo, rồi tự quyết định và giao trên
tool nội bộ. Tool chỉ đề xuất: không sửa file input, không ghi ngược vào tool nội bộ.

> **Trạng thái (2026-10-06):** bản v1 chạy được (82 test pass; đã chạy thật với Gemini trên file mẫu).

## 1. Cài đặt

| Cần | Ghi chú |
|---|---|
| Python ≥ 3.11 và [`uv`](https://docs.astral.sh/uv/) | Chạy `uv sync` một lần trong thư mục repo để cài thư viện. |
| Gemini CLI (`gemini`) trong `PATH` | Dùng để AI ước lượng độ lớn đơn. |
| Biến môi trường `GEMINI_API_KEY` với một key hợp lệ | Gemini CLI không còn đăng nhập bằng tài khoản Google được; phải có key. |

Thiếu Gemini CLI hoặc key thì tool **vẫn chạy và vẫn ra báo cáo**, nhưng mọi đơn được tính cùng độ lớn `M` và sheet
`Cảnh báo` ghi lý do.

## 2. Chạy nhanh

1. Đặt file vào `input/` (mục 3). Repo đã có sẵn file mẫu Sprint 6–10 và `devs.xlsx` của 4 dev.
2. Chạy:

   ```bash
   uv run assigntool
   ```

3. Mở file `output/assignment_<sprint>_<thời gian>.xlsx` (mục 4): xem đề xuất ở sheet `Phân công`, xử lý các dòng
   ở sheet `Cảnh báo`, rồi giao trên tool nội bộ.

Các cách chạy khác:

```bash
uv run assigntool --ai off                  # không gọi AI; mọi đơn tính là M (16h)
uv run assigntool --ai agy                  # dùng Antigravity thay cho gemini (máy dev)
uv run assigntool --sprint path/export.xlsx # chỉ định file export khi input/ có nhiều file .xlsx
uv run assigntool --help                    # mọi tuỳ chọn (mục 6)
```

## 3. Input

```
input/
├── <file export sprint>.xlsx   bắt buộc · đúng 1 file .xlsx ngoài devs.xlsx
├── devs.xlsx                   bắt buộc
└── <lịch sử>.csv               không bắt buộc · tối đa 1 file
```

Tool tự tìm file theo đuôi. Có 0 hoặc nhiều hơn một file ứng viên thì tool dừng, liệt kê các file tìm thấy và chỉ
cờ cần dùng (`--sprint`, `--devs`, `--history`); tool không đoán. File bắt đầu bằng `~$` (file khoá khi Excel đang
mở) và `.` bị bỏ qua. Khi sang sprint mới, **thay** file export cũ bằng file mới, đừng để cả hai trong `input/`.

### 3.1 File export sprint (`.xlsx`)

File export của tool nội bộ, giữ nguyên định dạng, không cần sửa tay.

- Mỗi sprint là một sheet tên `Sprint N`. Sheet có tên khác bị bỏ qua.
- **Sheet được giao** là `Sprint N` có N lớn nhất (đổi bằng `--sheet`). Sheet `Sprint N-1` là **sprint trước**,
  dùng để tính việc dở của từng dev. Các sheet nhỏ hơn N là **lịch sử** khi không có file CSV (mục 3.3).
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
| `Trạng thái` | ✓ | Chỉ dùng ở sheet sprint trước: dòng có trạng thái `qa - need fix`, `all issue`, `in progress`, `ready to progress`, `need to be clean` hoặc `internal - cant fix` tính là việc dở. |
| `Người làm` | ✓ | Đã có tên (cách nhau bằng dấu phẩy) thì đơn là **giao sẵn**: tool giữ nguyên, chỉ cộng tải cho dev. Trống thì tool đề xuất. |
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

- Chỉ dev có `Nhận việc` = `Y` được đề xuất. Dev nghỉ trọn mọi ngày làm việc (thứ 2–6) của sprint bị loại khỏi lần
  giao đó; nghỉ một phần chỉ dùng để phân định khi hai người ngang nhau.
- Người không có trong file (QA, RnD, Tech Manager…) bị bỏ qua hoàn toàn, không cảnh báo. Vì vậy nếu tên một dev bị
  gõ khác trong file export (thiếu dấu, thừa chữ), tool coi đó là người lạ và tính thiếu tải cho dev đó mà không báo.

### 3.3 File lịch sử `.csv` (không bắt buộc)

Danh sách các đơn đã làm ở các sprint trước, export từ hệ thống nội bộ. Tool dùng nó để biết ai đã làm app nào và
version nào gần nhất; số giờ của đơn cũ được gửi cho AI làm mốc so sánh.

Dùng **chính các cột của file export**, thêm cột `Sprint`. Mỗi dòng một task; chỉ dòng `Loại` = `Task` được dùng,
nên có thể dump cả bảng gồm subtask.

```csv
Sprint,STT,Task,Loại,App Name,Người làm,Ước lượng (h),Ngày tạo,Mô tả
Sprint 9,1,1.1.1 - Fix ads/FIx luồng/ fix policy,Task,PS Remote,"Ngọc Văn Linh, Nguyễn Nhật Minh",68,2026-09-21,
Sprint 9,165,1.0.3. Fix crash,Task,Game Emulator,Trần Đức An,17,2026-09-22,
```

- Bắt buộc: `Sprint`, `Loại`, `App Name`, `Người làm`, `Ngày tạo`. Nên có: `Task`, `Ước lượng (h)`.
- UTF-8 có hoặc không BOM; phân cách `,` hoặc `;`; ngày `YYYY-MM-DD` hoặc `DD/MM/YYYY`. "CSV UTF-8" lưu từ Excel đọc
  được, kể cả Excel locale Việt Nam.
- **Không có file CSV** thì tool lấy mọi sheet sprint cũ hơn trong file export làm lịch sử (file mẫu: Sprint 6–9) và
  ghi một dòng INFO. Có CSV thì chỉ dùng CSV; hai nguồn không bao giờ gộp, để không đếm trùng một sprint.

### 3.4 Dữ liệu gửi cho AI

Tool gọi AI **một lần** cho cả sprint, chỉ để xếp độ lớn từng đơn. AI không chọn người.

- Gửi đi: STT, app, ưu tiên, tiêu đề, mô tả (đã bỏ link và cắt ngắn) của các đơn sprint này, và tối đa 30 đơn cũ
  (app · tiêu đề · số giờ) làm mốc. **Không gửi tên người, không gửi link.**
- AI chạy ở chế độ chỉ đọc, trong một thư mục tạm rỗng, nên không đọc được `input/`. Quá 180 giây thì bị dừng
  (đổi bằng `--ai-timeout`).
- AI lỗi, hết giờ hoặc trả sai định dạng: mọi đơn (hoặc các đơn bị thiếu) tính là `M`, báo cáo vẫn được ghi.
- Cùng một input, hai lần chạy có thể ra độ lớn khác nhau, nên đề xuất cũng có thể khác. Độ lớn và lý do của AI có
  trong báo cáo để kiểm tra.

## 4. Output

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
Làm version gần nhất của PS Remote (Sprint 9: 1.1.1 - Fix ads/FIx luồng/ fix policy) · Đơn urgent → ưu tiên middle
trở lên · Tải sprint này: 0h (0 đơn) · Việc dở Sprint 9: 0
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
| `HISTORY-MISSING` | WARN | Không có CSV và không có sheet sprint cũ; coi như chưa ai làm app nào. | Thêm file CSV lịch sử hoặc export kèm các sprint cũ. |
| `HISTORY-FROM-WORKBOOK` | INFO | Không có CSV; dùng các sheet sprint cũ làm lịch sử. | Không cần làm gì. |
| `DEV-ON-LEAVE` | INFO | Một dev nghỉ cả sprint nên không được giao. | Không cần làm gì. |

### Sheet `Tải dev`

Mỗi dev trong danh sách một dòng (kể cả dev nghỉ cả sprint): `Mã`, `Tên`, `Level`, `Việc dở sprint trước`,
`Ngày nghỉ`, `Đơn giao sẵn`, `Đơn tool đề xuất`, `Tổng đơn`, `Tổng giờ ước tính`, `Danh sách đơn` (tiêu đề kèm độ
lớn, mỗi đơn một dòng) và `App đã làm`.

### Màn hình

Ví dụ trên file mẫu với `--ai off`:

```
Lịch sử: sheet Sprint 6, Sprint 7, Sprint 8, Sprint 9 trong workbook (không có file .csv)
Sprint: Sprint 10
Độ lớn: tắt AI (mọi đơn M)
Đơn: 6 · giao sẵn: 5 · tool đề xuất: 1 · cảnh báo: 0 WARN, 1 INFO
STT 10 · Roblox skin 1.0.4 - Fix luồng/Add Ads/Fix UI [M] → AnTD (dự phòng: MinhNM, TiếnBV)
Báo cáo: output/assignment_sprint-10_20261006-171450.xlsx
```

Khi có AI, trước đó in thêm `Đang ước lượng độ lớn bằng gemini…` và dòng độ lớn thành `Độ lớn: AI (gemini, 6/6 đơn)`
(số đơn AI ước lượng được trên tổng số đơn). Mỗi cảnh báo WARN được in một dòng `WARN <mã>: <nội dung>`. Chi tiết đầy
đủ nằm trong file Excel.

| Exit code | Ý nghĩa |
|---|---|
| `0` | Đã ghi báo cáo (có hay không có cảnh báo, có hay không có AI). |
| `2` | Lỗi input hoặc sai cách gọi; **không** ghi báo cáo. Thông báo `Lỗi: …` chỉ rõ file, sheet, dòng hoặc cột. |
| `130` | Dừng bằng Ctrl+C. |

Các lỗi input dừng tool: thiếu file hoặc có nhiều file ứng viên; thiếu cột bắt buộc; `Level` sai; `Nhận việc` không
phải `Y`/`N`; trùng `Tên` hoặc `Mã`; ngày không đọc được; không còn dev nào để giao sau khi trừ người nghỉ.

## 5. Tool chọn PIC thế nào

1. **AI xếp độ lớn** từng đơn, kể cả đơn giao sẵn (vì chúng cũng tính vào tải):

   | Hạng | Giờ | Ý nghĩa |
   |---|---|---|
   | `S` | 4 | Tối đa một ngày: sửa crash, sửa policy, đổi text/config. |
   | `M` | 16 | Hai đến ba ngày. |
   | `L` | 32 | Khoảng một tuần. |
   | `XL` | 64 | Hơn một tuần: tính năng mới, SDK mới, nhiều luồng cùng lúc. |

2. **Đơn giao sẵn giữ nguyên**, chỉ cộng giờ vào tải của dev được ghi tên.
3. **Đơn trống được xét lần lượt**: urgent → high → normal → low, rồi hạn sớm, rồi ngày tạo, rồi `STT`.
4. Với mỗi đơn, chỉ xét dev có tải **không vượt quá người ít việc nhất + 16 giờ** (để một người quen nhiều app không
   ôm hết). Trong số đó, chọn người tốt nhất theo thứ tự ưu tiên:
   1. Đã làm version gần nhất của app → từng làm app → chưa làm.
   2. Đơn urgent/high, hoặc app chưa ai trong team làm: ưu tiên level middle trở lên.
   3. Ít giờ việc hơn trong sprint này.
   4. Ít việc dở hơn từ sprint trước.
   5. Ít ngày nghỉ hơn.
   6. Level cao hơn, rồi theo `Mã` (để kết quả luôn giống nhau).

   Hai người tiếp theo theo cùng thứ tự (bỏ qua giới hạn tải) là dự phòng.
5. Cột `Lý do` ghi lại từng bước trên. Nếu người quen app hơn bị loại vì giới hạn tải, lý do cũng ghi rõ, vd
   `AnTD quen app hơn nhưng đang có 96h (cân tải)`.

## 6. Tuỳ chọn dòng lệnh

| Tuỳ chọn | Mặc định | Ý nghĩa |
|---|---|---|
| `--input DIR` | `input/` | Thư mục tìm file input. |
| `--sprint FILE` | file `.xlsx` duy nhất khác `devs.xlsx` | File export sprint. |
| `--devs FILE` | `<input>/devs.xlsx` | File dev. |
| `--history FILE` | file `.csv` duy nhất; không có thì dùng sheet sprint cũ | File lịch sử. |
| `--sheet NAME` | `Sprint N` lớn nhất | Sheet cần giao, vd `--sheet "Sprint 9"`. |
| `--out DIR` | `output/` | Thư mục ghi báo cáo; tự tạo nếu chưa có. |
| `--ai gemini\|agy\|off` | `gemini` | Công cụ AI. `agy` cho máy dev; `off` tính mọi đơn là M. |
| `--ai-model NAME` | mặc định của công cụ AI | Tên model truyền thẳng cho công cụ AI. |
| `--ai-timeout SECONDS` | `180` | Số giây chờ AI. |
| `-v` | tắt | In traceback khi lỗi và nội dung trao đổi với AI. |

## 7. Dành cho người phát triển

```bash
uv run ruff check . && uv run ruff format --check . && uv run pytest   # chạy sau mọi thay đổi code
ASSIGNTOOL_TEST_AI=gemini uv run pytest -m ai                         # thêm 1 lần gọi AI thật (cần mạng và key)
```

Test nghiệm thu (`tests/test_real_input.py`) chạy trên `input/Maintain_update_Sprint_10_va_9.xlsx`; thiếu file đó
thì test được bỏ qua kèm lý do.

| Tài liệu | Nội dung |
|---|---|
| [`docs/assignment-spec.md`](docs/assignment-spec.md) | Spec đầy đủ: định dạng input, ước lượng bằng AI, luật chọn PIC, nội dung lý do, cảnh báo, output, kết quả kỳ vọng trên file mẫu |
| [`confirm.md`](confirm.md) | Các quyết định đã chốt (D), mặc định (A) và câu hỏi còn mở (O) |
| [`docs/python-best-practices.md`](docs/python-best-practices.md) | Quy tắc viết code |
