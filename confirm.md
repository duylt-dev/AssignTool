# Quyết định phạm vi: `assigntool`

File này ghi mọi quyết định về phạm vi và hành vi của tool. Các file khác dẫn chiếu tới nó bằng mã `Dn`/`An`/`On`.

- **`Dn`: user đã chốt.** Có hiệu lực xuyên lượt: không hỏi lại, không đề xuất lại. Chỉ đổi khi user nói đổi.
- **`An`: mặc định do Claude chọn.** Được đổi khi có số đo hoặc dữ liệu thật cho thấy nó sai. Khi đổi, ghi lý do vào
  dòng đó.
- **`On`: còn mở.** Code xây theo phương án mặc định ghi trong dòng, nhưng không coi là đã chốt.

Ngày chốt: 2026-10-06. Dữ liệu tham chiếu: `input/Maintain_update_Sprint_10_va_9.xlsx` (sheet Sprint 10 và Sprint 6–9; Sprint 6–8 được thêm ngày 2026-10-06 làm dữ liệu lịch sử).

---

## D: user đã chốt

| # | Quyết định |
|---|---|
| D1 | Tool viết bằng Python, dùng để giao đơn cho dev. Đơn do BA lên trên tool nội bộ; user export ra Excel để chuẩn hoá. |
| D2 | Giao **hàng loạt đầu sprint** (Tech Manager xác nhận). Đầu sprint gần như mọi dev đều rảnh vì đã xong việc sprint trước. |
| D3 | Không dùng ước lượng do người nhập (est). Độ lớn đơn do AI ước lượng (D13). |
| D4 | Output là một file Excel (bản dev). |
| D5 | Đơn vị giao là **PIC theo đơn** (một Task gốc). PIC tự tách subtask cho đơn của mình. |
| D6 | Lịch sử "ai đã làm app này" lấy từ hệ thống nội bộ, đưa vào tool dưới dạng **một file `.csv`**. Đó chỉ là dữ liệu: định dạng và các cột do dự án tự quyết (A20). |
| D7 | Danh sách được giao việc chỉ gồm 4 dev Android: LinhNV (middle+), MinhNM (middle), AnTD (junior+), TiếnBV (junior). QA, RnD và Tech Manager nằm ngoài phạm vi; họ chỉ tham gia khi cần thêm người để đẩy tiến độ, và việc đó không qua tool. |
| D8 | Trạng thái tính là dev **còn việc** từ sprint trước: `qa - need fix`, `all issue`, `in progress`, `ready to progress`, `need to be clean`, `internal - cant fix`. Mọi trạng thái khác (đang chờ test, đã xong, `pending`) không tính. |
| D9 | Không đo độ lớn đơn bằng số subtask: lúc giao, đơn chỉ có một task duy nhất, subtask do PIC tách sau. |
| D10 | Đơn đã có người làm trong file thì giữ nguyên; tool chỉ điền đơn còn trống. |
| D11 | File dev chỉ chứa thông tin tĩnh: `Tên` (đúng như trong tool nội bộ) · `Mã` · `Level` · `Nhận việc` · `Ngày nghỉ`. Không lưu năm sinh. Trạng thái rảnh/bận suy ra từ sheet sprint trước, không nhập tay. |
| D12 | `.claude/` và docs được cấu hình lại cho dự án này: sao lưu bản cũ, xoá skill/agent mobile và design, docs theo cấu trúc README + `confirm.md` + `LLM.md` + best practices + spec. Docs kỹ thuật viết tiếng Anh; nội dung người dùng thấy (Excel output, thông báo lỗi) và `AGENTS.md` viết tiếng Việt. |
| D13 | **Độ lớn đơn do AI (Gemini) ước lượng tự động.** Mục tiêu của Tech Manager là làm tay càng ít càng tốt. |
| D14 | **Không cảnh báo gì về người ngoài danh sách dev.** Tool chỉ quan tâm tới người có trong `devs.xlsx`; tên khác trong mọi file đều bị bỏ qua, không báo. |
| D15 | Dự án dùng git (khởi tạo 2026-10-06, nhánh `main`). |
| D16 | Máy của Tech Manager dùng **Gemini CLI (`gemini`) với một API key hợp lệ** (trả lời O3). |
| D17 | Công ty **cho phép** gửi tiêu đề và mô tả đơn lên dịch vụ AI của Google (trả lời O4). |
| D18 | **`input/` và `output/` được commit vào git** (file export mẫu, `devs.xlsx`, các báo cáo). `LLM.md` và `AGENTS.md` không commit, chỉ giữ trên máy. `.claude/` không commit vì `settings.json` và `.env` chứa `GEMINI_API_KEY`. Chốt ngày 2026-10-06, thay A16. Hệ quả đã biết: dữ liệu nội bộ và tên người (kể cả người ngoài danh sách dev) nằm trong lịch sử git; các doc đã commit vẫn link tới `LLM.md`, nên người clone repo gặp link chết. |

## A: mặc định của Claude

| # | Mặc định | Lý do |
|---|---|---|
| A1 | Python `>=3.11`, `.python-version` 3.13, quản lý bằng `uv`. Phụ thuộc runtime duy nhất: `openpyxl`. CSV đọc bằng `csv`, AI gọi bằng `subprocess` của stdlib. | Một phụ thuộc là đủ cho đọc/ghi xlsx; pandas nặng và không cần cho vài trăm dòng. |
| A2 | Lệnh `assigntool` (CLI). Tìm input trong `input/`: `devs.xlsx` là file dev, file `*.csv` duy nhất là lịch sử (không bắt buộc, xem A8), file `*.xlsx` còn lại là workbook sprint. Có cờ để chỉ định rõ. Chạy được trên Windows, Linux, macOS. | Chạy không cần gõ đường dẫn; khi mơ hồ thì báo lỗi và yêu cầu chỉ định, không đoán. |
| A3 | Sprint cần giao là sheet `Sprint N` có N lớn nhất; sheet `Sprint N-1` là sprint trước. Ghi đè bằng `--sheet`. | File mẫu có Sprint 10 và Sprint 9; thứ tự sheet có thể đổi, số sprint thì không. |
| A4 | Đơn là dòng có `Loại` = `Task`. Dòng `Subtask` không được giao. Cây task dựng theo thụt lề `└`, không theo cột `Task cha`. | `Task cha` chứa tên chứ không phải mã, và tên bị trùng: Sprint 9 có 8 dòng "QA testing". |
| A5 | Thứ tự xử lý đơn: `Ưu tiên` (urgent > high > normal/trống > low) → `Hạn` (sớm trước, trống sau) → `Ngày tạo` → `STT`. | Đơn gấp được chọn người trước, khi mọi người còn nhẹ việc. |
| A6 | Luật chọn PIC: xem spec §7. Tóm tắt: quen app (làm version gần nhất > từng làm > chưa) → đơn urgent/high hoặc app chưa ai làm thì ưu tiên middle trở lên → tải trong sprint → việc dở sprint trước → ngày nghỉ. Chỉ xét dev có tải ≤ tải thấp nhất + 16h. | Trên file mẫu, chỉ với 1 sprint lịch sử, luật khớp 3/5 đơn TM đã giao (spec §12). Giới hạn chênh tải ngăn một người quen nhiều app nhận hết đơn. |
| A7 | AI xếp mỗi đơn vào một hạng; tải tính bằng giờ theo hạng: **S = 4h, M = 16h, L = 32h, XL = 64h**. Giới hạn chênh tải là 16h (một đơn M). AI lỗi hoặc tắt thì mọi đơn là M. | Xếp hạng chịu được sai số của AI tốt hơn đoán số giờ. Các mốc giờ khớp 4 nhóm `Ước lượng (h)` của 12 đơn Sprint 9 (2–4h, 10–22h, 26–26.5h, 57–83h). Khi mọi đơn là M, luật cho kết quả giống hệt bản đếm số đơn, nên §12 vẫn kiểm chứng được. |
| A8 | "Quen app" lấy từ CSV lịch sử. **Không có CSV** thì lấy từ các sheet sprint cũ hơn trong chính workbook (file mẫu: Sprint 6–9, 34 đơn) và báo INFO `HISTORY-FROM-WORKBOOK`. Không bao giờ dùng cả hai cùng lúc. | Đổi ngày 2026-10-06 theo yêu cầu "chạy tool là phải ra file trong output/": trước đây thiếu CSV thì tool dừng với exit 2. Sheet cũ có đúng các cột của CSV. Không gộp hai nguồn để tránh đếm trùng sprint đã có trong CSV. |
| A9 | "Việc dở" chỉ lấy từ sheet sprint trước trong cùng workbook. Không có sheet đó thì coi mọi dev không còn việc và cảnh báo `PREV-SPRINT-MISSING`. | File export đã có sẵn sheet sprint trước với trạng thái mới nhất. |
| A10 | So khớp tên người: chuẩn hoá NFC, gộp khoảng trắng, không phân biệt hoa thường. So khớp `App Name`: NFC, bỏ mọi khoảng trắng, không phân biệt hoa thường. | Tên app do người gõ ("SpeakerCleaner", "spin wheel 2"); macOS có thể ghi chữ có dấu ở dạng NFD. |
| A11 | *(Đã thay bằng D14.)* Trước đây đề xuất khai QA/RnD/TM trong `devs.xlsx` để cảnh báo tên lạ. Hệ quả đã biết của D14: nếu tên một dev bị gõ sai trong file export, tool coi đó là người lạ và tính sai tải của dev đó mà không báo. | — |
| A12 | Dev nghỉ trọn mọi ngày làm việc (T2–T6) của sprint thì bị loại. Nghỉ một phần chỉ dùng để phá hoà. | Không có số giờ thật của từng người nên không quy được ngày nghỉ ra tải một cách có cơ sở. |
| A13 | `Level` hợp lệ: `junior`, `junior+`, `middle`, `middle+`, `senior`. Giá trị khác là lỗi input. | Viết khác đi (vd "journey") thì dừng và báo lỗi rõ ràng, không ngầm hiểu. |
| A14 | Output gồm 3 sheet: `Phân công`, `Cảnh báo`, `Tải dev`. File: `output/assignment_<sprint>_<YYYYMMDD-HHMMSS>.xlsx`. | Khi còn dev trong danh sách thì đơn nào cũng giao được, nên sheet thứ hai chỉ còn chứa vấn đề dữ liệu và lỗi AI. |
| A15 | CSV: UTF-8 (có hoặc không BOM), phân cách bằng `,` hoặc `;`, ngày `YYYY-MM-DD` hoặc `DD/MM/YYYY`. | Excel "CSV UTF-8" ghi kèm BOM; Excel với locale Việt Nam dùng `;` và `DD/MM/YYYY`. |
| A16 | *(Đã thay bằng D18.)* Trước đây: `input/` và `output/` không đưa lên git. | — |
| A17 | Chọn công cụ AI bằng `--ai gemini\|agy\|off`, **mặc định `gemini`** (D16). `agy` (Antigravity) chỉ để dùng trên máy dev. | Trên máy dev (đo ngày 2026-10-06), `gemini` 0.57.0 không xác thực được: `GEMINI_API_KEY` trong `.claude/settings.json` bị Google báo `API_KEY_INVALID`, còn đăng nhập Google báo "client no longer supported … migrate to Antigravity". `agy` 1.2.17 trả JSON đúng sau 3–10 giây. Dạng JSON của `gemini` đọc từ mã nguồn 0.57.0 (`JsonFormatter`: `session_id`, `response`, `stats`, `error`, `warnings`). Sau khi thay key mới (2026-10-06), `gemini` chạy thành công trên máy dev: exit 0, 10 giây, trả `session_id`, `response`, `stats`. |
| A18 | Gọi AI **một lần cho cả sprint**, ở chế độ chỉ đọc (`--mode plan` / `--approval-mode plan`), trong một thư mục tạm rỗng, timeout 180 giây. Gửi đi: STT, app, ưu tiên, tiêu đề và mô tả (bỏ link, cắt ngắn) của đơn sprint này, cùng app, tiêu đề và số giờ của các đơn cũ. **Không gửi tên người.** | Một lần gọi nhanh hơn và để AI so các đơn với nhau. Thư mục rỗng ngăn agent đọc `input/`. D17 cho phép gửi nội dung đơn, nhưng vẫn bỏ tên người và link: AI không cần chúng để ước lượng, và bỏ link còn tránh agent tự mở link. |
| A19 | `Ước lượng (h)` của đơn sprint đang giao bị bỏ qua (D3). `Ước lượng (h)` của đơn cũ trong CSV được dùng làm ví dụ mẫu cho AI. | Lúc giao, đơn chưa có est. Số giờ đã ghi nhận của đơn cũ (thường là tổng subtask) là cách tốt nhất để AI hiểu thang đo của team. |
| A20 | CSV lịch sử dùng **chính các cột của file export sprint**, thêm cột `Sprint`; mỗi dòng là một task. Chỉ dòng `Loại` = `Task` được dùng. Bắt buộc: `Sprint`, `Loại`, `App Name`, `Người làm`, `Ngày tạo`. Nên có: `Task`, `Ước lượng (h)`, `Mô tả`. | Một bộ tên cột cho cả hai file. Lấy từ CSDL thì chỉ cần thêm cột sprint, có thể dump cả bảng, kể cả subtask. |

## O: còn mở

| # | Câu hỏi | Mặc định đang dùng |
|---|---|---|
| O5 | Lần chạy thật đầu tiên (spec §12, ghi chú cuối): AI xếp nhiều đơn XL nên tải chênh lớn, và giới hạn chênh 16h buộc đơn Roblox skin (XL, app mới) về TiếnBV (junior) vì chỉ Tiến đủ điều kiện. Giữ nguyên, hay để đơn XL/app mới được vượt giới hạn cho dev middle trở lên? | Giữ nguyên luật đã duyệt (A6, A7). Lý do có ghi rõ dev middle trở lên bị loại vì cân tải (spec §8 phần 7). |
| O6 | Độ lớn AI thay đổi giữa các lần chạy: cùng file mẫu, lần 1 Phone Cleaner là M, lần 2 là XL, nên đơn Roblox skin lần 1 về TiếnBV, lần 2 về MinhNM. Chấp nhận, hay làm ổn định (vd hỏi AI 3 lần lấy trung vị, hoặc lưu độ lớn lần đầu vào file để lần sau dùng lại)? | Chấp nhận (spec §6.4 "Determinism"); độ lớn và lý do của AI hiện trong báo cáo để TM kiểm tra. |
| O7 | Giới hạn chênh tải tính theo **giờ** (hiện tại: tải ≤ thấp nhất + 16h) hay theo **số đơn** (≤ thấp nhất + 1 đơn; giờ vẫn là tiêu chí thứ 3 của spec §7)? Với lịch sử Sprint 6–9, AnTD là người duy nhất làm Roblox skin, nhưng cả 3 lần Gemini chạy được đều loại AnTD vì AI xếp đơn giao sẵn của An là L + XL (96h so với 64h), nên đơn về MinhNM. Xét mọi 4.096 tổ hợp độ lớn: theo giờ, Roblox về MinhNM 42%, AnTD 30%, TiếnBV 28%; theo số đơn, về AnTD 100%. Backtest khớp TM 4/5 ở 100% tổ hợp (theo giờ: từ 2/5 đến 5/5). Khi `--ai off` hai cách cho kết quả y hệt (spec §12). Cách này cũng giải trường hợp của O5. | Giữ theo giờ cho tới khi user chọn. Claude đề xuất đổi sang số đơn. |

Đã đóng: O1 (đo độ lớn đơn) → D13, O2 (git) → D15, O3 (công cụ AI trên máy TM) → D16, O4 (gửi dữ liệu lên AI) → D17.
