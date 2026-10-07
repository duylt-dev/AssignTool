# Quyết định phạm vi: `assigntool`

File này ghi mọi quyết định về phạm vi và hành vi của tool. Các file khác dẫn chiếu tới nó bằng mã `Dn`/`An`/`On`.

- **`Dn`: user đã chốt.** Có hiệu lực xuyên lượt: không hỏi lại, không đề xuất lại. Chỉ đổi khi user nói đổi.
- **`An`: mặc định do Claude chọn.** Được đổi khi có số đo hoặc dữ liệu thật cho thấy nó sai. Khi đổi, ghi lý do vào
  dòng đó.
- **`On`: còn mở.** Code xây theo phương án mặc định ghi trong dòng, nhưng không coi là đã chốt.

Ngày chốt: 2026-10-06; cập nhật 2026-10-07 theo câu trả lời trong `plans/reports/261007-cau-hoi-export-t2-t10.md` (mục tiêu mới: hệ thống tự giao việc cho dev). Dữ liệu tham chiếu: `input/Maintain_update_Sprint_10_va_9.xlsx` (sheet Sprint 10 và Sprint 6–9) và `input/Tech_manager_T2-T10_2026.xlsx` (list Tech manager xuất từ CSDL, tháng 2–10/2026).

---

## D: user đã chốt

| # | Quyết định |
|---|---|
| D1 | Tool viết bằng Python, dùng để giao đơn cho dev. Đơn do BA lên trên tool nội bộ; user export ra Excel để chuẩn hoá. |
| D2 | Chạy tay, **lúc nào cũng được**: đầu sprint và mỗi khi BA lên đơn mới. Đơn đã có người giữ nguyên (D10) và tính vào tải; tool chỉ giao đơn còn trống. Đổi ngày 2026-10-07 (câu A3); trước đây là "giao hàng loạt đầu sprint", nhưng 59/116 đơn của các sprint 2 tuần được lên khi sprint đã chạy. |
| D3 | Không dùng ước lượng do người nhập (est). Độ lớn đơn do AI ước lượng (D13). |
| D4 | Output là một file Excel (bản dev). |
| D5 | Đơn vị giao là **PIC theo đơn** (một Task gốc). PIC tự tách subtask cho đơn của mình (232/234 subtask thuộc đúng dev của đơn). Chỉ giao đơn gốc của board Maintain; bug vẫn do QA giao (không có luật đơn giản: chỉ 78% bug về dev gần nhất trong cây); đơn board MVP / nghiên cứu không qua tool (câu A4, 2026-10-07). |
| D6 | Lịch sử "ai đã làm app này" là **file export list Tech manager** lấy từ CSDL hệ thống nội bộ: `.xlsx` (mỗi tháng một sheet, như file mẫu) hoặc `.csv`, cùng 18 cột. Mỗi lần chạy cần hai file: file export theo sprint (đơn cần giao kèm `Mô tả`, sheet sprint trước để tính việc dở) và file Tech manager (lịch sử). Đổi ngày 2026-10-07 (câu B1); trước đây là một file `.csv` tự định dạng (A20). |
| D7 | Danh sách được giao việc chỉ gồm 4 dev Android: LinhNV (middle+), MinhNM (middle), AnTD (junior+), TiếnBV (junior). QA, RnD và Tech Manager nằm ngoài phạm vi; họ chỉ tham gia khi cần thêm người để đẩy tiến độ, và việc đó không qua tool. |
| D8 | Trạng thái tính là dev **còn việc** từ sprint trước: `qa - need fix`, `all issue`, `in progress`, `ready to progress`, `need to be clean`, `internal - cant fix`, `internal - need fix`, `đã ro`. Mọi trạng thái khác (đang chờ test, đã xong, `pending`, `qa - cant fix`) không tính. Hai trạng thái cuối và `qa - cant fix` chốt ngày 2026-10-07 (câu B5). `đã ro` tính là còn việc theo lựa chọn của user, dù trong dữ liệu nó chỉ xuất hiện ở Sprint 8, sprint có 11/11 đơn đã xong. |
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
| D19 | Mục tiêu cuối: tool **tự giao và ghi thẳng `Người làm` vào hệ thống nội bộ, không cần TM duyệt** (câu A1, 2026-10-07). Chưa làm được: tool chưa có token và chưa có tài liệu API (D20). Cho tới khi có, kết quả của tool nằm trong file Excel và người có quyền nhập vào hệ thống (O8). |
| D20 | Hệ thống nội bộ do công ty tự phát triển, **có API đọc đơn và ghi `Người làm`**, nhưng tool **không** được cấp tài khoản hay token. File Tech manager do người có quyền truy vấn SQL rồi export cho user; user không truy cập được code và hệ thống (câu A2). |
| D21 | Mỗi đơn **1 PIC và 2 người dự phòng**, như hiện nay. TM tự thêm người thứ hai khi cần (câu A5). |
| D22 | Độ tin cậy được đo bằng **backtest** trên các sprint Maintain có trong file Tech manager: với mỗi sprint, bỏ `Người làm`, cho tool giao lại, so với người TM đã giao. Báo tỉ lệ khớp theo từng sprint và từng đơn. **Không đặt ngưỡng**: user xem kết quả rồi quyết định (câu A6). Lệch với TM chưa chắc là sai, vì luật cố ý cân tải. Cách chạy lại: A29. |
| D23 | File Tech manager gồm hai board: **Maintain** (sprint 2 tuần) và **MVP / nghiên cứu** (sprint 1–2 tháng). Đơn MVP **không** tính vào tải hay việc dở; chỉ dùng làm lịch sử "quen app" (câu B2). Export chưa có cột phân biệt board (A21). |
| D24 | Đơn gốc không có Sprint không được giao và không tính vào tải (câu B3). |
| D25 | Người export **có thể thêm** cột `ID task cha`, `Mô tả`, `Ước lượng (h)` vào file Tech manager (câu B4). Hiện chưa cần vì dùng cả hai file (D6). File có cột `Ước lượng (h)` thì số giờ đó được gửi cho AI làm ví dụ (A19). |
| D26 | Giới hạn chênh tải tính theo **số đơn**: chỉ xét dev có số đơn ≤ (ít đơn nhất) + 1. Số giờ vẫn là tiêu chí thứ 3 của spec §7 (câu C1, đóng O7 và O5). Khi mọi đơn là M, kết quả y hệt cách tính theo giờ cũ. |
| D27 | Chấp nhận độ lớn AI thay đổi giữa các lần chạy (câu C2, đóng O6). Sau D26, độ lớn chỉ còn ảnh hưởng tới tiêu chí tải giờ. |

## A: mặc định của Claude

| # | Mặc định | Lý do |
|---|---|---|
| A1 | Python `>=3.11`, `.python-version` 3.13, quản lý bằng `uv`. Phụ thuộc runtime duy nhất: `openpyxl`. CSV đọc bằng `csv`, AI gọi bằng `subprocess` của stdlib. | Một phụ thuộc là đủ cho đọc/ghi xlsx; pandas nặng và không cần cho vài trăm dòng. |
| A2 | Lệnh `assigntool` (CLI). Tìm input trong `input/` theo nội dung: `devs.xlsx` là file dev; file `.xlsx` có sheet `Sprint N` là file export sprint; file `.xlsx` không có sheet `Sprint N`, hoặc file `.csv`, là file lịch sử (không bắt buộc, tối đa một, xem A8). Có cờ để chỉ định rõ. Chạy được trên Windows, Linux, macOS. | Chạy không cần gõ đường dẫn; khi mơ hồ thì báo lỗi và yêu cầu chỉ định, không đoán. Tìm theo nội dung chứ không theo tên vì tên file export do người export đặt; đổi ngày 2026-10-07 khi `input/` có hai file `.xlsx` export. |
| A3 | Sprint cần giao là sheet `Sprint N` có N lớn nhất; sheet `Sprint N-1` là sprint trước. Ghi đè bằng `--sheet`. | File mẫu có Sprint 10 và Sprint 9; thứ tự sheet có thể đổi, số sprint thì không. |
| A4 | Đơn là dòng có `Loại` = `Task`. Dòng `Subtask` không được giao. Cây task dựng theo thụt lề `└`, không theo cột `Task cha`. | `Task cha` chứa tên chứ không phải mã, và tên bị trùng: Sprint 9 có 8 dòng "QA testing". |
| A5 | Thứ tự xử lý đơn: `Ưu tiên` (urgent > high > normal/trống > low) → `Hạn` (sớm trước, trống sau) → `Ngày tạo` → `STT`. | Đơn gấp được chọn người trước, khi mọi người còn nhẹ việc. |
| A6 | Luật chọn PIC: xem spec §7. Tóm tắt: quen app (làm version gần nhất > từng làm > chưa) → đơn urgent/high hoặc app chưa ai làm thì ưu tiên middle trở lên → tải trong sprint (giờ) → việc dở sprint trước → ngày nghỉ. Chỉ xét dev có số đơn ≤ ít đơn nhất + 1 (D26). | Trên file mẫu, chỉ với 1 sprint lịch sử, luật khớp 3/5 đơn TM đã giao (spec §12). Giới hạn chênh tải ngăn một người quen nhiều app nhận hết đơn. |
| A7 | AI xếp mỗi đơn vào một hạng; tải tính bằng giờ theo hạng: **S = 4h, M = 16h, L = 32h, XL = 64h**. Giới hạn chênh tải tính theo số đơn (D26). AI lỗi hoặc tắt thì mọi đơn là M. | Xếp hạng chịu được sai số của AI tốt hơn đoán số giờ. Các mốc giờ khớp 4 nhóm `Ước lượng (h)` của 12 đơn Sprint 9 (2–4h, 10–22h, 26–26.5h, 57–83h). Khi mọi đơn là M, luật cho kết quả giống hệt bản đếm số đơn, nên §12 vẫn kiểm chứng được. |
| A8 | "Quen app" lấy từ file lịch sử (D6). **Không có file lịch sử** thì lấy từ các sheet sprint cũ hơn trong chính workbook (file mẫu: Sprint 6–9, 34 đơn) và báo INFO `HISTORY-FROM-WORKBOOK`. Không bao giờ dùng cả hai cùng lúc. | Đổi ngày 2026-10-06 theo yêu cầu "chạy tool là phải ra file trong output/": trước đây thiếu CSV thì tool dừng với exit 2. Sheet cũ có đúng các cột của CSV. Không gộp hai nguồn để tránh đếm trùng sprint đã có trong CSV. |
| A9 | "Việc dở" chỉ lấy từ sheet sprint trước trong cùng workbook. Không có sheet đó thì coi mọi dev không còn việc và cảnh báo `PREV-SPRINT-MISSING`. | File export đã có sẵn sheet sprint trước với trạng thái mới nhất. |
| A10 | So khớp tên người: chuẩn hoá NFC, gộp khoảng trắng, không phân biệt hoa thường. So khớp `App Name`: NFC, bỏ mọi khoảng trắng, không phân biệt hoa thường. | Tên app do người gõ ("SpeakerCleaner", "spin wheel 2"); macOS có thể ghi chữ có dấu ở dạng NFD. |
| A11 | *(Đã thay bằng D14.)* Trước đây đề xuất khai QA/RnD/TM trong `devs.xlsx` để cảnh báo tên lạ. Hệ quả đã biết của D14: nếu tên một dev bị gõ sai trong file export, tool coi đó là người lạ và tính sai tải của dev đó mà không báo. | — |
| A12 | Dev nghỉ trọn mọi ngày làm việc (T2–T6) của sprint thì bị loại. Nghỉ một phần chỉ dùng để phá hoà. | Không có số giờ thật của từng người nên không quy được ngày nghỉ ra tải một cách có cơ sở. |
| A13 | `Level` hợp lệ: `junior`, `junior+`, `middle`, `middle+`, `senior`. Giá trị khác là lỗi input. | Viết khác đi (vd "journey") thì dừng và báo lỗi rõ ràng, không ngầm hiểu. |
| A14 | Output gồm 3 sheet: `Phân công`, `Cảnh báo`, `Tải dev`. File: `output/assignment_<sprint>_<YYYYMMDD-HHMMSS>.xlsx`. | Khi còn dev trong danh sách thì đơn nào cũng giao được, nên sheet thứ hai chỉ còn chứa vấn đề dữ liệu và lỗi AI. |
| A15 | File lịch sử dạng CSV: UTF-8 (có hoặc không BOM), phân cách bằng `,` hoặc `;`, ngày `YYYY-MM-DD` hoặc `DD/MM/YYYY`. | Excel "CSV UTF-8" ghi kèm BOM; Excel với locale Việt Nam dùng `;` và `DD/MM/YYYY`. |
| A16 | *(Đã thay bằng D18.)* Trước đây: `input/` và `output/` không đưa lên git. | — |
| A17 | Chọn công cụ AI bằng `--ai gemini\|agy\|off`, **mặc định `gemini`** (D16). `agy` (Antigravity) chỉ để dùng trên máy dev. | Trên máy dev (đo ngày 2026-10-06), `gemini` 0.57.0 không xác thực được: `GEMINI_API_KEY` trong `.claude/settings.json` bị Google báo `API_KEY_INVALID`, còn đăng nhập Google báo "client no longer supported … migrate to Antigravity". `agy` 1.2.17 trả JSON đúng sau 3–10 giây. Dạng JSON của `gemini` đọc từ mã nguồn 0.57.0 (`JsonFormatter`: `session_id`, `response`, `stats`, `error`, `warnings`). Sau khi thay key mới (2026-10-06), `gemini` chạy thành công trên máy dev: exit 0, 10 giây, trả `session_id`, `response`, `stats`. |
| A18 | Gọi AI **một lần cho cả sprint**, ở chế độ chỉ đọc (`--mode plan` / `--approval-mode plan`), trong một thư mục tạm rỗng, timeout 180 giây. Gửi đi: STT, app, ưu tiên, tiêu đề và mô tả (bỏ link, cắt ngắn) của đơn sprint này, cùng app, tiêu đề và số giờ của các đơn cũ. **Không gửi tên người.** | Một lần gọi nhanh hơn và để AI so các đơn với nhau. Thư mục rỗng ngăn agent đọc `input/`. D17 cho phép gửi nội dung đơn, nhưng vẫn bỏ tên người và link: AI không cần chúng để ước lượng, và bỏ link còn tránh agent tự mở link. |
| A19 | `Ước lượng (h)` của đơn sprint đang giao bị bỏ qua (D3). `Ước lượng (h)` của đơn cũ trong file lịch sử, khi file có cột này, được dùng làm ví dụ mẫu cho AI. File Tech manager hiện chưa có cột này nên AI không có ví dụ (D25). | Lúc giao, đơn chưa có est. Số giờ đã ghi nhận của đơn cũ (thường là tổng subtask) là cách tốt nhất để AI hiểu thang đo của team. |
| A20 | *(Đã thay bằng D6 ngày 2026-10-07.)* Trước đây: CSV lịch sử dùng các cột của file export sprint, thêm cột `Sprint`. | — |
| A21 | Board Maintain được nhận ra theo **độ dài nhãn sprint**: nhãn dài tối đa 21 ngày là sprint Maintain, dài hơn là MVP / nghiên cứu. Một sprint được nhận diện bằng cả số, ngày bắt đầu và ngày kết thúc. | Trong file Tech manager, sprint Maintain dài 4–17 ngày, sprint MVP 27–54 ngày. `Sprint 1 (5/22 - 6/5)` (Maintain) và `Sprint 1 (5/22 - 7/15)` (MVP) trùng cả số lẫn ngày bắt đầu. Đổi sang cột board nếu export có thêm (D23). |
| A22 | Lịch sử chỉ gồm việc **đã có trước lần chạy**: bỏ các đơn của sprint đang giao (câu M1), đơn lên sau ngày chạy, và đơn của sprint chưa bắt đầu. Ngày chạy là hôm nay; trong backtest là ngày đơn được lên. File lịch sử không bao giờ gộp với các sheet cũ của workbook (A8). | Một đơn không tự làm lịch sử cho chính nó. Cùng một luật cho lần chạy thật và backtest, để backtest đo đúng cái tool làm và không nhìn thấy tương lai. |
| A23 | Lịch sử gồm mọi đơn gốc (`Loại` = `Task`, `Task cha` trống) có app và có tên một dev trong danh sách, kể cả đơn MVP / nghiên cứu và đơn không có Sprint (câu M2). | Dev quen app qua đơn MVP thì vẫn là quen app (D23). |
| A24 | Đơn có nhiều sprint (`Sprint 18 (…), Sprint 19 (…)`) thuộc mọi sprint được liệt kê. Năm của nhãn (`10/6 - 10/17`) là năm làm ngày bắt đầu gần `Ngày lên đơn` nhất (câu M3). | Nhãn chỉ có tháng/ngày; sprint qua năm mới vẫn đúng. |
| A25 | Cột lý do trích **nhãn sprint đầy đủ** như trong file (vd `Sprint 3 (9/3 - 9/30)`); đơn không có sprint thì trích tháng lên đơn (`Tháng 9/2026`) (câu M4). | Có hai "Sprint 3" khác nhau. |
| A26 | "Quen app" chỉ tính `Người làm` của **đơn gốc** (câu M5). | Chỉ 6 đơn có dev ở subtask mà không ở đơn gốc. |
| A27 | Tên app chỉ chuẩn hoá theo A10, không có bảng tên gọi khác: `fakecal` và `Fake Call` là hai app (câu M6). | Bảng tên gọi phải có người giữ; chưa thấy đủ trường hợp để đáng làm. |
| A28 | Giữ bộ test nghiệm thu A–D trên file Maintain (spec §12), thêm lần chạy với file Tech manager và backtest nhiều sprint (câu M7). | |
| A29 | Backtest (D22): `assigntool --backtest`, chỉ cần file Tech manager và `devs.xlsx`. Với mỗi sprint Maintain: đơn của sprint mà TM đã giao cho dev trong danh sách được xoá `Người làm` rồi giao lại; đơn mang sang từ sprint Maintain trước giữ nguyên người TM giao (như đơn giao sẵn). Đơn được giao lại theo **ngày lên đơn**: đơn lên trước ngày bắt đầu được giao cùng lúc vào ngày bắt đầu, mỗi ngày sau là một lần chạy (D2). Mọi đơn là `M` và việc dở bằng 0. Khớp khi PIC của tool là một trong các dev TM đã giao. | File Tech manager không có `Mô tả` nên AI không ước lượng được; trạng thái trong file là trạng thái hiện tại, không phải lúc sprint bắt đầu, nên không tính được việc dở. |

## O: còn mở

| # | Câu hỏi | Mặc định đang dùng |
|---|---|---|
| O8 | Ghi `Người làm` thẳng vào hệ thống (D19). Cần: tài liệu API đọc/ghi đơn, một token cho tool (D20), và `ID` của đơn trong file export theo sprint (file hiện chưa có cột `ID`; file Tech manager có). | Tool ghi file Excel; người có quyền nhập vào hệ thống. |
| O9 | Các mặc định M1–M7 của file câu hỏi: user đánh dấu cột "Không đồng ý" ở cả 7 dòng nhưng không ghi lý do. Phủ định của M2 (bỏ đơn MVP khỏi lịch sử) và M7 (bỏ backtest) mâu thuẫn với câu B2 và A6 user đã chọn, nên Claude hiểu là đồng ý. | Áp dụng M1–M7 (A22–A28); đổi được khi user nói. |

Đã đóng: O1 (đo độ lớn đơn) → D13, O2 (git) → D15, O3 (công cụ AI trên máy TM) → D16, O4 (gửi dữ liệu lên AI) → D17, O5 (đơn XL/app mới bị giới hạn tải) và O7 (giới hạn theo giờ hay số đơn) → D26, O6 (độ lớn AI thay đổi) → D27.
