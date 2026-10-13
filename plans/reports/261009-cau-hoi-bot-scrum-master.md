# Câu hỏi: bot scrum master (mục tiêu mới)

Ngày 2026-10-09. Liên quan: báo cáo API [`261009-bao-cao-api-he-thong-noi-bo.md`](261009-bao-cao-api-he-thong-noi-bo.md),
form 08/10 [`261008-cau-hoi-scrum-master-quan-ly-rui-ro.md`](261008-cau-hoi-scrum-master-quan-ly-rui-ro.md) (chưa có
trả lời, xem mục F), plan [`261008-1738-scrum-master-risk-management/`](../261008-1738-scrum-master-risk-management/plan.md).

**Mục tiêu mới (09/10):** một bot Python đóng vai scrum master: quản lý task, hiểu task, review task, giao người, và
**trọng tâm là quản lý rủi ro**. Được phép viết lại toàn bộ tool hiện tại.

**Cách trả lời**

- Đánh `x` vào ô bạn chọn: `- [x]`. Câu nào ghi "chọn nhiều" thì đánh được nhiều ô.
- **Để trống cả câu nghĩa là đồng ý với phương án có ghi "(đề xuất)".** Chỉ cần điền chỗ không đồng ý hoặc cần nói thêm.
- Bảng có cột `Đồng ý` / `Không đồng ý`: đánh một ô mỗi dòng; chọn "Không đồng ý" thì ghi lý do vào `Trả lời:`.

Sau khi bạn trả lời, mình ghi quyết định vào `confirm.md` (D/A/O), sửa spec và plan, rồi mới code.

---

## Hiện trạng cần biết trước khi trả lời

| Điều | Hiện trạng (khảo sát 09/10 và file mẫu) | Hệ quả cho bot |
|---|---|---|
| Ghi vào hệ thống | **Có API**: gán người làm, comment, đổi trạng thái / hạn / ưu tiên, chuyển sprint | Bot làm được mọi việc ghi cần thiết, khi có quyền |
| Đọc từ hệ thống | Danh sách đơn và chi tiết đơn **chỉ có trang HTML**. JSON chỉ có: nhật ký trạng thái và comment của **từng** đơn, tiến độ sprint, danh sách user | Muốn đọc sprint phải bóc HTML (dễ vỡ) hoặc vẫn dùng file export |
| Đăng nhập | Chỉ Google OAuth + cookie. **Không có token** | **Việc chặn số 1:** bot chạy tự động không có cách xác thực hợp lệ |
| `POST .../assignee` | Chưa rõ là thêm, thay hay bật/tắt người làm | Ghi sai sẽ gỡ người TM đã gán (trái D10); chưa ghi được cho tới khi rõ |
| Ngày nghỉ dev, giờ làm thực tế | Hệ thống không có | Ngày nghỉ vẫn lấy từ `devs.xlsx`; không đo được giờ thật |
| Link PR (`Git Pull Request`) | 1/220 dòng của Sprint 6–10 có link | Không có dữ liệu để review code |
| `Đánh giá DEV` trong file Tech manager | 1/3144 dòng | Không có dữ liệu để chấm điểm dev |
| Đơn không có mô tả bằng chữ | 22/40 đơn gốc Sprint 6–10 | Rủi ro "đơn chưa rõ" sẽ bật trên hơn nửa số đơn |
| Đơn lên khi sprint đã chạy | 59/116 đơn của các sprint 2 tuần | Bot phải chạy nhiều lần trong sprint, không chỉ đầu sprint |

---

## A. Bot là gì

### Q1. Hình thức bot

- [x] **(đề xuất)** **Chạy theo lịch, không cần người bấm:** mỗi sáng ngày làm việc (8h30) quét sprint, giao đơn trống,
  cập nhật sổ rủi ro, gửi bản tóm tắt; trong giờ hành chính, cứ 30 phút quét đơn mới để giao (D2). Vẫn chạy tay được
  bằng lệnh. Chưa chat hai chiều. *Chỉ chạy theo lịch được khi đã có token (Q6); trước đó chạy tay.*
- [ ] Vẫn là CLI chạy tay như hiện nay, chỉ thêm tính năng.
- [ ] Bot chat hai chiều: TM hỏi ("sprint này rủi ro gì?", "giao lại STT 5 cho AnTD") và bot làm. Cần máy chạy 24/7 và
  một kênh chat có API bot.

Trả lời:

### Q2. "Review task" là review cái gì? (chọn nhiều)

- [x] **(đề xuất)** **Review đơn trước khi giao:** đơn đủ rõ chưa, thiếu gì, hỏi lại BA và hạn bổ sung (bước 1 của
  feedback 08/10).
- [x] **(đề xuất)** **Review đơn đang chạy:** kẹt trạng thái, sắp trễ hạn, bị QA trả về nhiều lần, subtask chậm.
- [ ] Review code của dev qua PR. Chỉ 1/220 dòng có link PR; cần quyền đọc Git và dev phải điền link. Không đề xuất đợt này.
- [ ] Chấm `Đánh giá DEV` / `Điểm` khi đơn xong. Chưa có dữ liệu mẫu (1/3144 dòng). Không đề xuất đợt này.

Trả lời:

### Q3. "Hiểu task": AI được làm gì?

Hiện AI chỉ ước lượng độ lớn (D13); luật cố định chọn PIC (spec §7). Nhờ vậy mỗi lựa chọn có lý do kiểm được, và
backtest đo được luật (47% khớp TM trên 92 đơn; khác TM chủ yếu do cân tải).

- [x] **(đề xuất)** AI đọc tiêu đề và mô tả rồi trả về: loại đơn (ads, IAP, luồng/UI, policy, crash, SDK, tính năng),
  các hạng mục, độ lớn, mục checklist còn thiếu, tối đa 2 câu hỏi cho BA, rủi ro kỹ thuật thấy được (SDK mới, hạn
  store). **AI không chọn PIC và không quyết mức rủi ro:** luật cố định quyết.
- [ ] Như trên, và để AI chọn PIC luôn. Đổi D13; backtest không còn đo được luật; mỗi lần chạy có thể ra người khác.

Trả lời:

### Q4. Phạm vi

| Việc | Phạm vi đề xuất | Đồng ý | Không đồng ý |
|---|---|---|---|
| Giao PIC | Đơn gốc board Maintain còn trống. Giữ D5: không giao subtask, bug, đơn MVP | [x] | [ ] |
| Theo dõi rủi ro | Đơn gốc Maintain, kèm subtask và bug của chúng (subtask kẹt hay bug còn mở là rủi ro của đơn cha). Không theo dõi board MVP | [x] | [ ] |
| Người được giao / được nhắc việc | 4 dev Android (D7). QA, RnD, TM không bị giao việc | [x] | [ ] |

Trả lời:

### Q5. D14 với bot: nhắc tới người ngoài danh sách dev

D14: tool không cảnh báo gì về người ngoài danh sách dev. Bot mới cần (a) hỏi BA ngay trên đơn của họ, (b) báo đơn
kẹt ở khâu QA hoặc đang chờ BA trả lời.

- [x] **(đề xuất)** Bot được comment trên đơn và tag người tạo đơn để hỏi. Đơn kẹt ở khâu QA/BA được báo **theo đơn
  và trạng thái** ("STT 5 chờ QA test 4 ngày"), không nêu tên, không chấm ai. Ghi thành phần làm rõ của D14.
- [ ] Giữ D14 nguyên văn: không hỏi BA trực tiếp, không báo đơn kẹt ở khâu QA/BA.

Trả lời:

---

## B. Dữ liệu, quyền và nơi chạy

### Q6. Bot lấy dữ liệu thế nào khi chưa có token?

- [x] **(đề xuất)** **Xây lớp nguồn dữ liệu thay được.** Giai đoạn 1 đọc file export như hiện nay (chạy tay). Song
  song, bạn xin đội hệ thống token và API JSON danh sách đơn (mục P1 của báo cáo 09/10). Có token thì cắm nguồn API
  vào; luật không đổi.
- [ ] Làm bản thử đọc HTML bằng cookie đăng nhập Google của bạn. Chỉ khi chủ hệ thống đồng ý bằng văn bản. Mọi
  comment và lần gán người sẽ mang tên bạn; HTML đổi là bot vỡ; cookie hết hạn là bot dừng.
- [ ] Dừng lại, chờ có token rồi mới làm.

Bạn đã gửi yêu cầu token cho đội hệ thống chưa? Dự kiến khi nào có?

Trả lời:

### Q7. Ngày nghỉ, level, trạng thái nhận việc của dev

Hệ thống không có ngày nghỉ.

- [x] **(đề xuất)** Giữ `devs.xlsx` (D11). TM sửa file khi có người nghỉ.
- [ ] Có nguồn khác (sheet nghỉ phép của HR, Google Calendar…): ghi tên nguồn và cách lấy ở dòng `Trả lời:`.

Trả lời:

### Q8. Bot chạy ở đâu, dùng AI nào

Câu 7 trong báo cáo PO 08/10 chưa có trả lời.

- [x] **(đề xuất)** Chạy trên **một máy luôn bật** (server nội bộ hoặc VPS của công ty), gọi **Gemini API qua HTTPS**
  bằng key của công ty (D17 đã cho gửi nội dung đơn lên Google). Máy TM vẫn chạy tay được bằng Gemini CLI (D16).
- [ ] Chạy trên máy TM, chạy tay, Gemini CLI như hiện nay.
- [ ] AI khác (ghi tên). Lưu ý: D17 chỉ cho phép gửi dữ liệu lên Google.

Trả lời:

---

## C. Bot được làm gì trong hệ thống

### Q9. Mức tự động của từng hành động

"TM duyệt": bot ghi đề xuất ra file; TM đánh dấu dòng đồng ý rồi chạy lệnh `apply`. Khi có chat hai chiều thì duyệt
trong chat.

| # | Hành động | Tự động | TM duyệt rồi bot làm | Không làm |
|---|---|---|---|---|
| 1 | Gán `Người làm` cho đơn trống | **D19 đã chốt: tự động.** Chỉ bật khi đã rõ ngữ nghĩa API `assignee` (mục E, dữ liệu 2) | — | — |
| 2 | Comment hỏi BA khi đơn chưa rõ | [x] **(đề xuất)** | [ ] | [ ] |
| 3 | Comment nhắc PIC khi đơn kẹt hoặc sắp trễ hạn | [x] **(đề xuất)** | [ ] | [ ] |
| 4 | Đổi PIC khi PIC nghỉ hết phần còn lại của sprint. *Đổi D10.* | [ ] | [x] **(đề xuất)** | [ ] |
| 5 | Chuyển đơn sang sprint sau khi sprint quá tải | [ ] | [x] **(đề xuất)** | [ ] |
| 6 | Đổi trạng thái, hạn, ưu tiên của đơn | [ ] | [ ] | [x] **(đề xuất)** |

Trả lời:

### Q10. Ai nhận gì, qua kênh nào

| Nội dung | Người nhận | Kênh đề xuất | Đồng ý | Không đồng ý |
|---|---|---|---|---|
| Câu hỏi làm rõ đơn | BA lên đơn | Comment trên đơn (khi có token). Trước đó: sheet `Phản hồi BA` trong Excel, TM copy gửi | [x] | [ ] |
| Nhắc đơn kẹt hoặc sắp trễ hạn | PIC | Comment trên đơn (khi có token). Trước đó: chỉ trong sổ rủi ro | [x] | [ ] |
| Tóm tắt rủi ro mỗi sáng | TM | Kênh chat (chọn bên dưới) và file Excel | [x] | [ ] |
| Báo cáo cuối sprint: đã giao gì, rủi ro nào đã xảy ra, rủi ro nào bot báo đúng | TM, MD | File Excel | [x] | [ ] |

Team dùng kênh chat nào?

- [ ] Google Chat
- [ ] Slack
- [ ] Telegram
- [ ] Microsoft Teams
- [x] **(đề xuất, nếu chưa chọn được)** Chưa dùng chat: chỉ Excel và comment trên đơn.

Trả lời:

---

## D. Quản lý rủi ro

### Q11. Bot theo dõi những rủi ro nào?

Cột "Nguồn": **Export** = làm được ngay với file export; **Nhật ký** = cần nhật ký trạng thái `hoat-dong` của từng
đơn (API JSON, cần đăng nhập), nên làm ở giai đoạn 2. Mức Cao / Trung bình / Thấp cố định theo loại rủi ro, tăng một
bậc khi đơn urgent/high.

| # | Rủi ro | Phát hiện khi | Nguồn | Đồng ý | Không đồng ý |
|---|---|---|---|---|---|
| 1 | Đơn chưa rõ | Không có mô tả bằng chữ; đơn urgent/high không có `Hạn`; thiếu App Name; thiếu mục checklist theo loại đơn | Export + AI | [x] | [ ] |
| 2 | Dev quá tải | Tải (giờ theo độ lớn AI) vượt sức chứa còn lại của dev | Export | [x] | [ ] |
| 3 | Sprint quá tải | Tổng tải vượt sức chứa team; kèm danh sách đơn nên đẩy sang sprint sau | Export | [x] | [ ] |
| 4 | Đơn thêm giữa sprint | Đơn lên sau ngày bắt đầu sprint làm sprint vượt sức chứa | Export | [x] | [ ] |
| 5 | PIC chưa quen app | Đơn urgent/high giao cho dev chưa từng làm app; gợi ý người hỗ trợ | Export | [x] | [ ] |
| 6 | PIC vắng | PIC nghỉ hết phần còn lại của sprint; gợi ý người thay (theo đúng luật §7) | Export | [x] | [ ] |
| 7 | Sắp trễ hạn | Còn ≤ 3 ngày làm việc tới hạn mà đơn chưa bắt đầu, hoặc còn nhiều subtask mở | Export | [x] | [ ] |
| 8 | Việc dở dồn sang | Dev còn nhiều việc dở của sprint trước | Export | [x] | [ ] |
| 9 | Đơn bị đổi sau khi giao | Mô tả, hạn hoặc ưu tiên đổi so với lần chạy trước | Export (so lần trước) | [x] | [ ] |
| 10 | Đơn kẹt trạng thái | Nằm một trạng thái quá ngưỡng (mục G, K4) | Nhật ký | [x] | [ ] |
| 11 | QA trả về nhiều lần | Về `qa - need fix` từ 2 lần trở lên | Nhật ký | [x] | [ ] |
| 12 | BA chưa trả lời | Câu hỏi làm rõ quá hạn bổ sung (R4) mà chưa có comment trả lời | Nhật ký | [x] | [ ] |

Rủi ro nào bạn thấy quan trọng mà chưa có trong bảng? Ghi vào dòng `Trả lời:`.

Trả lời:

---

## E. Viết lại hay nâng cấp

### Q12. Kiến trúc

- [x] **(đề xuất)** **Giữ lõi, viết lại phần vỏ.** Giữ luật giao PIC, luật TM và backtest trong `rules/` (161 test, đã
  đo trên 92 đơn và bộ `eval/`). Tổ chức lại thành 4 lớp: **nguồn dữ liệu** (Excel, sau này HTML hoặc API), **hiểu
  đơn** (AI), **quyết định** (giao PIC và rủi ro, không I/O), **hành động** (Excel, comment, gán người, chat). Viết
  lại phần đọc file, báo cáo và lệnh chạy.
- [ ] Viết lại từ đầu. Mất backtest và `eval/` làm thước đo cho tới khi viết lại xong phần giao PIC.

Tên package và lệnh (để trống = `scrumbot`; đổi tên repo không bắt buộc): ___

Trả lời:

### Q13. Thứ tự làm

| GĐ | Nội dung | Cần token? |
|---|---|---|
| 1 | Tổ chức lại 4 lớp; AI hiểu đơn (Q3); sổ rủi ro các dòng 1–9 của Q11 trên file export; báo cáo Excel kèm sheet `Phản hồi BA` và `Thay đổi` | Không |
| 2 | Nguồn dữ liệu từ hệ thống (theo Q6); nhật ký trạng thái nên có các rủi ro 10–12; chạy theo lịch (Q1) | Có |
| 3 | Ghi vào hệ thống theo Q9 (gán người, comment); tóm tắt qua chat (Q10); lệnh `apply` cho các đề xuất cần TM duyệt | Có |

- [x] **(đề xuất)** Làm theo thứ tự trên. Giai đoạn 1 bắt đầu ngay.
- [ ] Đổi thứ tự (ghi ở dòng `Trả lời:`).

Trả lời:

---

## F. Các câu của form 08/10

Form 08/10 chưa có trả lời. R7, R10 và R11 đã được thay bằng Q9, Q10 và dòng 9 của Q11; R5 thay bằng Q5. Các câu còn
lại vẫn đúng với bot mới:

| Câu | Phương án "(đề xuất)" của form 08/10 |
|---|---|
| R1 | Đơn chưa rõ **vẫn được giao PIC**, kèm cờ `Cần làm rõ` và câu hỏi cho BA |
| R2 | "Đủ rõ" = 3 kiểm tra cố định + checklist theo loại đơn; AI chỉ đánh dấu mục thiếu và đặt tối đa 2 câu hỏi |
| R3 | Checklist khởi đầu cho 7 loại đơn (ads, IAP, luồng/UI, policy, crash, SDK, tính năng); TM giữ checklist trong file luật `.md` |
| R4 | Hạn bổ sung: urgent/high 1 ngày làm việc, đơn khác 2 ngày; không muộn hơn `Hạn` của đơn |
| R6 | Sức chứa: 6 giờ hiệu quả mỗi ngày làm việc, trừ ngày nghỉ; mức Cao khi vượt 1,5 lần |
| R8 | Không giao đơn mới cho dev nghỉ hết các ngày còn lại của sprint (đổi A12) |
| R9 | AI không đọc link Figma/Docs |
| T1–T7 | Các mặc định kỹ thuật của form 08/10 (mô tả < 30 ký tự là "không có mô tả", "sắp đến hạn" = ≤ 3 ngày làm việc, ngày làm việc T2–T6…) |

- [x] **(đề xuất)** Áp các phương án trên.
- [ ] Tôi sẽ trả lời form 08/10.

Trả lời:

---

## G. Mặc định kỹ thuật (Claude chọn, ghi thành dòng A)

| # | Mặc định | Đồng ý | Không đồng ý |
|---|---|---|---|
| K1 | Bot không bao giờ gỡ hay đổi người đã có trên đơn, trừ hành động 4 của Q9 khi TM duyệt. Ngay trước khi ghi, bot đọc lại đơn; `Người làm` không còn trống thì bỏ qua. | [x] | [ ] |
| K2 | Mọi hành động ghi vào hệ thống có chế độ chạy thử. Sprint đầu tiên của giai đoạn 3 chỉ chạy thử: bot ghi ra file những gì nó *sẽ* làm, TM xem rồi mới bật thật. Mọi lần ghi thật được lưu nhật ký trong `output/`. | [x] | [ ] |
| K3 | Chống spam: mỗi đơn tối đa 1 comment cho mỗi loại rủi ro mỗi ngày; nội dung không đổi thì không comment lại. | [x] | [ ] |
| K4 | Ngưỡng "kẹt trạng thái" tính từ dữ liệu thật: 80% số lần chuyển trạng thái của Sprint 6–10 xong trong bao lâu thì lấy mức đó (cần dữ liệu 5 ở mục H). Trước khi có số đo: `in progress` > 3 ngày làm việc, các trạng thái `ready to …` > 2 ngày làm việc. | [x] | [ ] |
| K5 | AI vẫn chạy chỉ đọc, không nhận tên người, không nhận link (A18). | [x] | [ ] |
| K6 | Bot nhớ giữa các lần chạy (đã hỏi gì, đã nhắc gì, lần chạy trước thấy gì) trong một file SQLite ở `state/`, **không commit**: file đổi liên tục và có tên người. | [x] | [ ] |
| K7 | Không thêm thư viện khi thư viện chuẩn của Python đủ dùng (gọi HTTP bằng `urllib`, SQLite bằng `sqlite3`). Chỉ thêm khi bóc HTML bắt buộc phải có. | [x] | [ ] |
| K8 | Tin nhắn cho người dùng (comment, tóm tắt, Excel) viết tiếng Việt (D12). | [x] | [ ] |

Trả lời:

---

## H. Dữ liệu cần bạn lấy giúp

> **Kết quả (09/10):** bạn yêu cầu Claude tự lấy qua Claude in Chrome và không cung cấp token. Mục 2 và 5 đã có;
> mục 1 và 4 thành `confirm.md` O11; mục 3 không cần (Q10 không dùng chat); mục 6 thành O13. Chi tiết:
> [`261009-bao-cao-du-lieu-he-thong-qua-chrome.md`](261009-bao-cao-du-lieu-he-thong-qua-chrome.md). Các câu A–G đã ghi
> vào `confirm.md` D36–D48 và A45–A53.

1. **Token hoặc tài khoản dịch vụ cho bot**, và **API JSON danh sách đơn của một sprint** (P1 trong báo cáo 09/10).
   Chặn giai đoạn 2 và 3. Khi có token, đừng dán vào chat; mình sẽ hướng dẫn đặt vào `.env`.
2. **Ngữ nghĩa của `POST /api/task/{id}/assignee`:** thêm, thay hay bật/tắt người làm? Chặn hành động 1 của Q9.
3. *(Nếu chọn chat ở Q10)* URL webhook của kênh chat và tên kênh nhận tóm tắt.
4. *(Nếu đồng ý Q8)* Máy chạy bot và Gemini API key cho máy đó.
5. **Cho phép mình đọc nhật ký `hoat-dong` của các đơn Sprint 6–10** qua Chrome bằng phiên đăng nhập của bạn, chỉ gọi
   GET như lần khảo sát 09/10. Dùng để đo ngưỡng kẹt trạng thái (K4) và số lần QA trả về. Không chép nội dung đơn hay
   tên người vào repo, chỉ lưu số đo.
6. *(Từ form 08/10, không gấp)* Nhãn của TM cho 18 đơn Sprint 9–10: "lúc giao, đơn này có thiếu thông tin không? Thiếu
   gì?". Dùng để đo độ chính xác của cờ `Cần làm rõ`.

## Ngoài phạm vi (đề xuất)

- Review code qua PR, chấm điểm dev (Q2): chưa có dữ liệu.
- Giao bug, board MVP (giữ D5).
- Điều phối họp sprint, retro.
- Velocity và burndown: làm được khi có nhật ký trạng thái (giai đoạn 2), nhưng chưa nằm trong đợt này.
