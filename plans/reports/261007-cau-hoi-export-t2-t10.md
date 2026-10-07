# Câu hỏi: hệ thống tự giao việc cho dev

Bản 2, ngày 2026-10-07. Thay cho bản 1 (bản 1 chưa được trả lời). Viết lại theo mục tiêu mới: **một hệ thống tự giao
việc cho dev**, dùng 3 file trong `input/` làm dữ liệu tham chiếu.

**Cách trả lời**

- Đánh `x` vào ô bạn chọn: `- [x]`.
- **Để trống cả câu nghĩa là đồng ý với phương án có ghi "(đề xuất)".** Bạn chỉ cần điền những chỗ không đồng ý
  hoặc những chỗ có hỏi thêm.
- Ghi chú thêm thì viết vào dòng `Trả lời:` của câu đó.

Sau khi bạn trả lời, mình ghi các quyết định vào `confirm.md` (D/A/O) rồi mới lập kế hoạch.

---

## Những gì mình đọc được từ input

### Ba file

| File | Là gì | Điểm mạnh | Điểm thiếu |
|---|---|---|---|
| `Maintain_update_Sprint_10_va_9.xlsx` | Export theo sprint của folder "Product Development / Maintain update". Sheet Sprint 6–10. | Có `Mô tả`, `Ước lượng (h)`, cây task theo thụt lề (chính xác). | Chỉ 5 sprint, chỉ board Maintain. |
| `Tech_manager_T2-T10_2026.xlsx` | Toàn bộ list "Tech manager" xuất từ CSDL, tháng 2–10/2026. 3.144 dòng, 178 đơn gốc. | Lịch sử 9 tháng, gồm cả đơn MVP và nghiên cứu. | Không có `Mô tả`, `Ước lượng (h)`. `Task cha` là **tên**, không phải ID. Subtask không có Sprint. |
| `devs.xlsx` | 4 dev trong danh sách. | Level, ngày nghỉ. | — |

Hai file export là cùng một hệ thống: 6 đơn Sprint 10 và 12 đơn Sprint 9 khớp đúng nhau.

### Các phát hiện ảnh hưởng tới thiết kế

| # | Phát hiện | Số liệu |
|---|---|---|
| P1 | **Một nửa số đơn được lên khi sprint đã chạy**, không phải trước ngày bắt đầu. Giao đầu sprint (D2) chỉ phủ khoảng một nửa. | 116 đơn của các sprint 2 tuần: 55 lên trước ngày bắt đầu, 59 lên trong sprint, 2 lên sau khi sprint kết thúc. |
| P2 | Có đủ dữ liệu để **backtest nhiều sprint**: so luật của tool với người TM đã thực sự giao. Trước đây chỉ backtest được 1 sprint. | 16 sprint Maintain (Sprint 14–19, rồi đánh số lại Sprint 1–10), khoảng 100 đơn có dev trong danh sách. |
| P3 | Phần lớn đơn có 1 dev; một số có 2 dev. | Trong file Maintain, 6/36 đơn có dev trong danh sách được giao cho 2 dev (vd Phone Cleaner 1.0.2: Linh + Tiến; PS Remote 1.1.1: Linh + Minh). |
| P4 | **Subtask luôn do dev của đơn làm.** Giao đúng đơn là đủ, subtask tự theo. | 232/234 subtask có dev trong danh sách thuộc đúng dev của đơn. |
| P5 | Bug do QA tạo (Linh Đặng, Oanh, Thơ) và giao cho dev, nhưng **không theo một luật đơn giản**. | 707 bug. Dev nhận bug trùng dev gần nhất phía trên trong cây ở 482/619 bug (78%). |
| P6 | Dev trong danh sách cũng làm đơn của **board MVP / nghiên cứu** (sprint dài 1–2 tháng). Việc đó hiện không được tính vào tải. | Phone Cleaner MVP: Tiến (`Sprint 3 (9/3 - 9/30)`); spin wheel 2 MVP: Linh; Game mode 2 MVP: Tiến. |
| P7 | Hệ thống nội bộ có thể đã chuyển từ ClickUp sang hệ thống khác giữa tháng 9. | Ảnh trong `Mô tả` nằm trên `clickup-attachments.com`; ID đổi từ `TICKET-…` sang `n_…` từ giữa tháng 9. |
| P8 | `đã ro` là trạng thái **đã xong**. | Sprint 8 (11/11 đơn xong) chỉ có hai nhóm trạng thái: `done` và `đã ro`. |

---

## Phần A. Mục tiêu "tự giao việc"

### A1. Mức độ tự động

Hiện tại tool chỉ đề xuất, TM quyết định và tự nhập vào hệ thống; tool không bao giờ ghi vào hệ thống nội bộ.

- [ ] **(đề xuất)** Làm theo hai bước. **Bước 1:** tool đề xuất, TM duyệt trên file Excel như hiện nay; dùng
  backtest (A6) để đo mức khớp với TM. **Bước 2:** khi bạn tin kết quả, tool ghi `Người làm` thẳng vào hệ thống sau
  khi TM bấm duyệt.
- [ ] Làm luôn bước 2: tool ghi thẳng vào hệ thống, TM duyệt trước khi ghi.
- [x] Tool tự giao và ghi thẳng, không cần TM duyệt.

Trả lời:

### A2. Hệ thống nội bộ

Chỉ cần trả lời nếu A1 có bước ghi vào hệ thống, hoặc nếu muốn tool đọc thẳng từ hệ thống thay vì từ file export.

| Câu hỏi | Trả lời |
|---|---|
| Hệ thống là gì? (ClickUp / tự viết / khác) | Hệ thống công ty tự phát triển|
| Có API để **đọc** đơn không? | [x] Có  [ ] Không  [ ] Không rõ |
| Có API để **ghi** `Người làm` không? | [x] Có  [ ] Không  [ ] Không rõ |
| Tool được cấp tài khoản hoặc token riêng không? | [ ] Có  [x] Không  [ ] Không rõ |
| File Tech manager được lấy từ CSDL bằng cách nào? (truy vấn SQL, công cụ export…) | Truy vấn SQL rồi export ra data cho tôi, tôi không có quyền truy cập vào code + hệ thống|

### A3. Khi nào tool giao việc

D2 chốt "giao hàng loạt đầu sprint". Nhưng P1 cho thấy một nửa số đơn đến khi sprint đã chạy.

- [x] **(đề xuất)** Chạy tay, **lúc nào cũng được**: đầu sprint và mỗi khi BA lên đơn mới. Tool đã làm được như vậy:
  đơn đã có người thì giữ nguyên (D10) và tính vào tải, chỉ giao đơn còn trống. Chỉ cần sửa tài liệu và D2.
- [ ] Chỉ đầu sprint (giữ nguyên D2).
- [ ] Tự chạy theo lịch (vd mỗi sáng). Cần nơi chạy cố định và đọc được dữ liệu mới (A2).
- [ ] Tự chạy ngay khi BA lên đơn. Cần API hoặc webhook (A2).

Trả lời:

### A4. Loại việc được giao

- [x] **(đề xuất)** Chỉ **đơn gốc** của board Maintain (D5). Subtask do dev của đơn tự tách (P4). Bug vẫn do QA giao,
  vì không có luật đơn giản (P5).
- [ ] Giao thêm **bug**.
- [ ] Giao thêm đơn của **board MVP / nghiên cứu**.

Trả lời:

### A5. Một hay hai dev cho một đơn

- [x] **(đề xuất)** Giữ như hiện nay: 1 PIC và 2 người dự phòng. TM tự thêm người thứ hai khi cần (P3).
- [ ] Đơn lớn (XL) được giao 2 dev.
- [ ] Cách khác:

Trả lời:

### A6. Làm sao biết tool giao đúng

- [x] **(đề xuất)** Backtest trên 16 sprint (P2): với mỗi sprint, xoá `Người làm`, cho tool giao lại, rồi so với
  người TM đã giao. Báo tỉ lệ khớp theo từng sprint và từng đơn lệch. Không đặt ngưỡng: bạn xem kết quả rồi quyết định
  sang bước 2 của A1. Lưu ý: lệch với TM chưa chắc là sai, vì luật cố ý cân tải.
- [ ] Đặt ngưỡng: khớp ≥ ____ % mới cho tool tự giao.

Trả lời:

---

## Phần B. Dữ liệu

### B1. Mỗi file dùng vào việc gì

- [x] **(đề xuất)** Mỗi file dùng đúng điểm mạnh của nó:
  - **File export theo sprint** (dạng `Maintain_update…`): đơn cần giao, kèm `Mô tả` để AI ước lượng; sheet sprint
    trước để tính việc dở (cây task chính xác).
  - **File Tech manager** (thay cho file `.csv` lịch sử của D6): lịch sử "ai từng làm app nào". Lịch sử chỉ cần đơn
    gốc, nên `Task cha` là tên cũng không sao.
  - Mỗi lần chạy cần export cả hai file.
- [ ] Chỉ dùng file Tech manager, bỏ file export theo sprint. Khi đó cần thêm cột ở B4.
- [ ] Chỉ dùng file export theo sprint, nhưng export nhiều sprint hơn (vd 16 sprint).

**Hỏi thêm:** sau này file Tech manager export ra `.xlsx` như bây giờ hay ra `.csv`?

- [x] **(đề xuất)** `.xlsx`, cùng 18 cột
- [x] `.csv`, cùng 18 cột

Trả lời:

### B2. Board MVP / nghiên cứu

List Tech manager có vẻ gồm hai board: **Maintain** (sprint 2 tuần) và **MVP / nghiên cứu** (sprint 1–2 tháng, vd
`Sprint 1 (5/22 - 7/15)`, `Sprint 3 (9/3 - 9/30)`). Nhận định này đúng không?

- [x] Đúng
- [ ] Sai, thực tế là:

Đơn MVP mà dev trong danh sách đang làm (P6) có được tính vào tải hoặc việc dở của dev đó không?

- [x] **(đề xuất)** Không. Chỉ dùng làm lịch sử "quen app".
- [ ] Có, tính vào tải.
- [ ] Có, tính vào việc dở.

Export có thêm được cột phân biệt board (vd `Folder`, `List`) không? Tên cột:

Trả lời:

### B3. Đơn không có Sprint

Có 15 đơn gốc không có Sprint, trạng thái `ready to progress`, chưa có người làm. 9 đơn từ tháng 4–8 có vẻ tồn đọng.
Một vài đơn đã có subtask đang làm: Fake Call 1.3.0 (Linh, Minh, Tiến), sattelite 1.2.3 (Linh).

- [x] **(đề xuất)** Không giao, không tính vào tải.
- [ ] Giao luôn.
- [ ] Không giao, nhưng tính vào tải của dev đang làm subtask.

Trả lời:

### B4. Thêm cột vào file Tech manager

**Chỉ cần nếu B1 chọn "chỉ dùng file Tech manager", hoặc A2 cho đọc thẳng CSDL.**

| Cột | Tại sao cần | Thêm được? |
|---|---|---|
| `ID task cha` | `Task cha` là tên, và 35% subtask có nhiều task cha cùng tên. Dựng cây theo tên sai 33/397 dòng (8%) so với file Maintain. Cần cây để tính việc dở. | [x] Có  [ ] Không |
| `Mô tả` | AI cần mô tả để ước lượng độ lớn đơn. | [x] Có  [ ] Không |
| `Ước lượng (h)` | Ví dụ cho AI biết thang đo giờ của team (A19). `Điểm` không phải giờ: 4h → 2.5, 24h → 9, 83h → 21.5. | [x] Có  [ ] Không |

Trả lời:

### B5. Trạng thái mới chưa có trong D8

| Trạng thái | Số dòng | Đề xuất | Tính là còn việc? |
|---|---|---|---|
| `qa - cant fix` | 34 | Có, giống `internal - cant fix` | [] Có  [x] Không |
| `internal - need fix` | 2 | Có, giống `qa - need fix` | [x] Có  [ ] Không |
| `đã ro` | 33 | Không, vì đây là trạng thái đã xong (P8) | [x] Có  [ ] Không |

Trả lời:

---

## Phần C. Luật chọn PIC (các câu còn mở O5–O7)

Thêm lịch sử giúp tool biết ai quen app nào tốt hơn: cả 6 app của Sprint 10 giờ đều có người từng làm (trước đây
Phone Cleaner bị coi là app mới). Nhưng nó **không** làm đề xuất hết thay đổi giữa các lần chạy, vì:

- độ lớn do AI ước lượng khác nhau giữa các lần chạy (O6);
- giới hạn chênh tải đang tính theo **giờ** (O7).

Ví dụ: với lịch sử Sprint 6–9, cả 3/3 lần chạy Gemini đều loại AnTD, người duy nhất từng làm Roblox skin, vì AI xếp
hai đơn giao sẵn của An là L + XL.

### C1. Giới hạn chênh tải (O7)

- [x] **(đề xuất)** Tính theo **số đơn**: chỉ xét dev có tải ≤ (ít đơn nhất) + 1 đơn. Số giờ vẫn là tiêu chí thứ 3.
  Khi chạy `--ai off` kết quả y hệt hiện nay. Giải luôn O5.
- [ ] Giữ theo **giờ** (tải ≤ thấp nhất + 16h).

### C2. Độ lớn AI thay đổi giữa các lần chạy (O6)

- [x] **(đề xuất)** Chấp nhận. Sau C1, độ lớn chỉ còn ảnh hưởng tới tiêu chí tải.
- [ ] Hỏi AI 3 lần, lấy trung vị (chậm gấp khoảng 3 lần).
- [ ] Lưu độ lớn của lần chạy đầu để các lần sau dùng lại.

Trả lời:

---

## Các mặc định mình sẽ áp dụng mà không hỏi

Đánh `x` vào ô **Không đồng ý** nếu muốn khác, rồi ghi lý do.

| # | Mặc định | Không đồng ý |
|---|---|---|
| M1 | Lịch sử từ file Tech manager **bỏ các đơn của sprint đang giao**, để đơn không tự làm lịch sử cho chính nó. File này đã phủ Sprint 6–9, nên không cộng thêm các sheet cũ của file Maintain (A8: không bao giờ gộp hai nguồn). | [x] |
| M2 | Lịch sử gồm mọi đơn gốc có app và có tên một dev trong danh sách, kể cả đơn MVP / nghiên cứu và đơn không có Sprint. | [x] |
| M3 | Đơn có nhiều sprint (`Sprint 18 (…), Sprint 19 (…)`) thuộc mọi sprint được liệt kê. Năm của nhãn sprint (vd `10/6 - 10/17`) lấy theo `Ngày lên đơn`. | [x] |
| M4 | Cột lý do trích **nhãn sprint đầy đủ** (vd `Sprint 3 (9/3 - 9/30)`), vì có hai "Sprint 3" khác nhau. Đơn không có sprint thì trích tháng. | [x] |
| M5 | "Quen app" chỉ tính `Người làm` của **đơn gốc**, như hiện nay. Chỉ 6 đơn có dev ở subtask mà không ở đơn gốc. | [x] |
| M6 | Tên app chỉ chuẩn hoá theo A10 (bỏ khoảng trắng, không phân biệt hoa thường), không có bảng tên gọi khác: `fakecal` và `Fake Call` là hai app. | [x] |
| M7 | Giữ bộ test nghiệm thu A–D trên file Maintain (spec §12), thêm backtest nhiều sprint (A6) trên file Tech manager. | [x] |

Ghi chú:
