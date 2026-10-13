# Câu hỏi: nâng cấp tool theo hướng scrum master (quản lý rủi ro)

Ngày 2026-10-08. Plan: [`plans/261008-1738-scrum-master-risk-management/`](../261008-1738-scrum-master-risk-management/plan.md).

Feedback nhận được: bot không chỉ phân việc mà phải như một scrum master, theo 4 bước: (1) làm rõ đơn trước khi giao
(đơn thiếu gì, chưa rõ ở đâu, người lên đơn cần bổ sung thế nào, hạn khi nào), (2) tính toán, (3) đề xuất phân đơn,
(4) quản lý và ứng phó với thay đổi. Hướng đã chọn: **quản lý rủi ro**.

**Cách trả lời**

- Đánh `x` vào ô bạn chọn: `- [x]`.
- **Để trống cả câu nghĩa là đồng ý với phương án có ghi "(đề xuất)".** Chỉ cần điền chỗ không đồng ý hoặc cần nói thêm.
- Ghi chú thêm thì viết vào dòng `Trả lời:` của câu đó.

Sau khi bạn trả lời, mình ghi quyết định vào `confirm.md` (D/A/O), sửa spec rồi mới code.

---

## Vì sao cần: số liệu từ file mẫu

| Số liệu | Giá trị | Ý nghĩa |
|---|---|---|
| Đơn gốc Sprint 6–10 không có mô tả bằng chữ (dưới 30 ký tự sau khi bỏ link) | **22/40** | Bước 1 sẽ gắn cờ hơn nửa số đơn. Nếu chặn giao thì hơn nửa số đơn bị treo, trong khi TM vẫn giao được các đơn này. |
| Trong 22 đơn đó, số đơn có link (Figma, Docs, ClickUp) | 3 | Phần lớn đơn thiếu mô tả là thiếu thật, không phải mô tả nằm trong link. |
| Đơn có `Hạn` | 11/40 | Đơn không có `Hạn` lấy ngày cuối sprint làm hạn. |
| Đơn trong file Tech manager có `Ngày đóng` | 1/178 | Chưa tính được tỉ lệ trễ hạn theo app hay theo dev, nên rủi ro trễ chỉ tính từ trạng thái và hạn của sprint đang chạy. |
| Đơn không có số version trong tiêu đề | 8/40 | Cả 8 đều là đơn nghiên cứu hoặc `Nhiều App`, nên **không** kiểm tra "thiếu version" (sẽ báo sai). |
| Độ lớn AI đúng hạng (2 sprint thật) | 57%; lệch ≤ 1 hạng: 95% | Rủi ro quá tải tính bằng độ lớn AI nên chỉ là ước lượng. |

## Phương án đề xuất

Tool sinh thêm một **sổ rủi ro** (sheet `Rủi ro`) mỗi lần chạy. Mỗi dòng gồm: mức (Cao / Trung bình / Thấp), vấn
đề, ảnh hưởng, đề xuất xử lý, ai xử lý và hạn xử lý. Có 4 nhóm rủi ro, khớp 4 bước của feedback:

| Bước | Nhóm rủi ro | Ví dụ |
|---|---|---|
| 1 · Làm rõ đơn | Đơn chưa rõ | "Đơn STT 3 chưa rõ: không có mô tả bằng chữ; thiếu ad unit ID. Bổ sung trước 12/10/2026." Sheet `Phản hồi BA` có tin nhắn soạn sẵn cho từng người lên đơn. |
| 2 · Tính toán | Năng lực | "LinhNV giữ 80h việc, sức chứa còn 60h." "Sprint có 250h việc, team còn 240h: đề xuất đẩy STT 12, 9 sang sprint sau." |
| 3 · Đề xuất | Phân công | "PIC TiếnBV (junior) chưa làm app này, đơn urgent: nhờ LinhNV hỗ trợ khởi động." |
| 4 · Ứng phó thay đổi | Tiến độ + Thay đổi | "Đơn STT 5 còn 2 ngày tới hạn nhưng vẫn ready to progress." "MinhNM nghỉ hết sprint: đề xuất chuyển STT 7 cho AnTD." Sheet `Thay đổi` so với lần chạy trước. |

**Nguyên tắc giữ nguyên:** rủi ro chỉ là gợi ý. Luật chọn PIC (spec §7) vẫn quyết định; tool không tự đổi đơn đã
giao (D10). AI chỉ thêm việc đánh dấu mục checklist còn thiếu và đặt tối đa 2 câu hỏi cho mỗi đơn, trong cùng lần
gọi ước lượng độ lớn đang có.

---

## R1. Đơn chưa rõ có bị chặn giao không?

- [ ] **(đề xuất)** Vẫn giao PIC. Đơn được gắn cờ `Cần làm rõ`, có dòng trong sổ rủi ro và tin nhắn cho người lên đơn.
- [ ] Không giao đơn thiếu thông tin bắt buộc (thiếu App Name, hoặc đơn urgent/high chưa có `Hạn`) cho tới khi BA bổ sung. Đơn chỉ thiếu mục checklist vẫn giao.
- [ ] Không giao mọi đơn có cờ.

Trả lời:

## R2. "Đủ rõ" đo bằng gì?

- [ ] **(đề xuất)** 3 kiểm tra cố định, cộng checklist theo loại đơn:
  - 3 kiểm tra cố định: không có mô tả bằng chữ; đơn urgent/high chưa có `Hạn`; thiếu App Name.
  - Checklist do TM/BA viết, nằm trong file luật `.md`. AI chỉ đánh dấu mục checklist nào chưa thấy trong tiêu đề và mô tả, và đặt tối đa 2 câu hỏi.
- [ ] Chỉ 3 kiểm tra cố định, không dùng AI.
- [ ] Để AI tự nhận xét, không có checklist. Không khuyến nghị: mỗi lần chạy AI sẽ hỏi một kiểu.

Trả lời:

## R3. Checklist khởi đầu

Rút từ tiêu đề 40 đơn mẫu: `ads` 24 đơn, `luồng` 9, `policy` 7, `crash` 5, `feature` 4, `UI` 4, `IAP` 2, `SDK` 1.
Một đơn khớp nhiều loại thì gộp các mục lại.

| Loại đơn | Từ khoá trong tiêu đề | Cần có | Đồng ý | Sửa |
|---|---|---|---|---|
| Ads | ads, quảng cáo, native, admob | Loại quảng cáo và vị trí hiển thị; Ad unit ID hoặc nơi lấy ID; Tần suất hoặc điều kiện hiển thị | [ ] | [ ] |
| IAP | iap, subscription, gói | Product ID và giá; Màn paywall (thiết kế hoặc link) | [ ] | [ ] |
| Luồng / UI | luồng, flow, ui, màn | Thiết kế (Figma) hoặc mô tả màn hình; Luồng mới khác luồng cũ ở đâu | [ ] | [ ] |
| Policy | policy, store | Nội dung vi phạm hoặc email từ Google Play; Hạn store yêu cầu | [ ] | [ ] |
| Crash / lỗi | crash, lỗi, bug | Bước tái hiện hoặc log / link Crashlytics; Thiết bị hoặc version Android gặp lỗi | [ ] | [ ] |
| SDK | sdk | Tên và version SDK; Tài liệu tích hợp | [ ] | [ ] |
| Tính năng mới | feature, tính năng | Hành vi mong muốn; Thiết kế | [ ] | [ ] |

Ai giữ checklist?

- [ ] **(đề xuất)** TM, trong cùng file luật `.md` (một bảng riêng, không ảnh hưởng bảng luật).
- [ ] BA lead.

Trả lời:

## R4. Hạn bổ sung cho người lên đơn

- [ ] **(đề xuất)** Đơn urgent/high: 1 ngày làm việc sau ngày chạy. Đơn khác: 2 ngày làm việc. Không muộn hơn `Hạn` của đơn.
- [ ] Trước ngày bắt đầu sprint.
- [ ] Khác (ghi ở dòng Trả lời).

Trả lời:

## R5. Tên người lên đơn trong báo cáo (liên quan D14)

D14: tool không cảnh báo gì về người ngoài danh sách dev. Ô `Người tạo` vốn đã được chép nguyên vào sheet `Phân công`.

- [ ] **(đề xuất)** Có. Sheet `Phản hồi BA` nhóm theo ô `Người tạo` như trong file export và soạn sẵn tin nhắn. Tên chỉ dùng để biết gửi cho ai; tool không cảnh báo gì về BA. Đây là phần làm rõ thêm cho D14.
- [ ] Không. Chỉ ghi vai trò "BA lên đơn".

Trả lời:

## R6. Sức chứa của một dev

- [ ] **(đề xuất)** 6 giờ hiệu quả mỗi ngày làm việc, tức 60h cho sprint 10 ngày, trừ ngày nghỉ. Báo rủi ro khi tải vượt sức chứa; mức Cao khi vượt quá 1,5 lần.
- [ ] Số khác: ___ giờ/ngày.
- [ ] Thêm cột giờ/ngày cho từng dev trong `devs.xlsx`.

Trả lời:

## R7. Ứng phó khi có rủi ro tiến độ (dev nghỉ, đơn sắp đến hạn chưa làm)

- [ ] **(đề xuất)** Tool chỉ đề xuất người thay (tính bằng đúng luật chọn PIC) và việc cần làm. Không đổi đơn đã giao (giữ D10).
- [ ] Khi có API: tool tự đổi người, TM bấm duyệt (đổi D10).
- [ ] Khi có API: tool tự đổi người, không cần duyệt (đổi D10, theo D19).

Trả lời:

## R8. Dev nghỉ hết những ngày còn lại của sprint (chạy giữa sprint)

Hiện nay tool chỉ loại dev nghỉ **cả** sprint (A12). Chạy ngày 22/10 thì dev nghỉ 23–30/10 vẫn có thể được giao đơn mới.

- [ ] **(đề xuất)** Không giao đơn mới cho dev nghỉ hết các ngày còn lại. Đơn đã giao cho dev đó có rủi ro `PIC-ABSENT` kèm người đề xuất thay.
- [ ] Giữ như hiện nay.

Trả lời:

## R9. Cho AI đọc link Figma/Docs? (D17 chỉ cho gửi tiêu đề và mô tả)

- [ ] **(đề xuất)** Không. Chỉ 3 trong 22 đơn thiếu mô tả có link; lợi ít, trong khi phải đăng nhập và mở rộng phạm vi dữ liệu gửi Google.
- [ ] Có, với link công khai.

Trả lời:

## R10. Kênh phản hồi trước khi có API

- [ ] **(đề xuất)** Trong file Excel: sheet `Phản hồi BA` có tin nhắn soạn sẵn; TM copy dán vào comment của đơn hoặc chat.
- [ ] Gửi qua webhook chat (Slack / Google Chat / Telegram). Cần URL webhook và quyết định ai nhận.

Trả lời:

## R11. So sánh với lần chạy trước

- [ ] **(đề xuất)** Mỗi lần chạy tự so với báo cáo gần nhất của cùng sprint trong `output/` và ghi sheet `Thay đổi`: đơn mới, đơn bị bỏ, đổi ưu tiên / hạn / mô tả, TM giao khác đề xuất.
- [ ] Không cần.

Trả lời:

---

## Mặc định kỹ thuật (Claude chọn, ghi thành dòng A)

| # | Mặc định | Đồng ý | Không đồng ý |
|---|---|---|---|
| T1 | "Không có mô tả bằng chữ" = dưới 30 ký tự sau khi bỏ link. | [ ] | [ ] |
| T2 | Đơn "chưa bắt đầu" = trạng thái `ready to progress`, `pending` hoặc trống. | [ ] | [ ] |
| T3 | "Sắp đến hạn" = còn ≤ 3 ngày làm việc tới `Hạn`, hoặc tới ngày cuối sprint nếu đơn không có `Hạn`. | [ ] | [ ] |
| T4 | Mức rủi ro cố định theo loại rủi ro; tăng một bậc khi đơn urgent/high. | [ ] | [ ] |
| T5 | Ngày làm việc là T2–T6; chưa tính ngày lễ. | [ ] | [ ] |
| T6 | Tải dùng để tính sức chứa = các đơn có trạng thái "còn việc" (D8) hoặc trống. Giờ của việc dở sprint trước chưa có nên không cộng; chỉ ghi số dòng trong lời nhắn. | [ ] | [ ] |
| T7 | Không kiểm tra "thiếu số version" (8/40 đơn mẫu không có version, cả 8 là đơn nghiên cứu hoặc `Nhiều App`). | [ ] | [ ] |

## Dữ liệu cần bạn lấy giúp (không chặn việc làm plan)

1. **Cột `ID` trong file export theo sprint.** Dùng để khớp đơn giữa hai lần chạy (R11), và cũng cần cho O8. Khi chưa có, tool khớp theo App + Task + Ngày tạo: 40 đơn mẫu không có cặp nào trùng.
2. **Nhãn của TM cho 18 đơn Sprint 9–10:** "lúc giao, đơn này có thiếu thông tin không? Thiếu gì?". Dùng để đo độ chính xác của cờ `Cần làm rõ`. Thiếu nhãn này thì chỉ đo được số lượng cờ và độ ổn định giữa các lần chạy.
3. *(Không gấp)* `Ngày đóng` trong export Tech manager (hiện chỉ 1/178 đơn có). Có thì tính được tỉ lệ trễ hạn theo app và theo dev.

## Ngoài phạm vi đợt này

- Điều phối họp sprint, retro, velocity / burndown: chưa có dữ liệu ngày đóng đơn.
- Tự gửi tin, tự comment vào đơn, tự ghi `Người làm`: chờ API và token (D20, O8).
