# Báo cáo: dữ liệu mục H lấy thẳng từ hệ thống qua Claude in Chrome

Ngày 2026-10-09. Trả lời mục H của form [`261009-cau-hoi-bot-scrum-master.md`](261009-cau-hoi-bot-scrum-master.md).
Liên quan: báo cáo API [`261009-bao-cao-api-he-thong-noi-bo.md`](261009-bao-cao-api-he-thong-noi-bo.md), `confirm.md`
D36–D48, A45–A53, O8, O11–O13.

User yêu cầu (09/10): mục H thì Claude tự lấy dữ liệu trong `https://circle.datlt.site/` bằng Claude in Chrome, **không
cần user cung cấp token nữa**.

## 1. Tóm tắt

| Mục H | Kết quả |
|---|---|
| 1. Token, API JSON danh sách đơn | **Không xin token.** Claude đọc hệ thống qua Chrome bằng phiên đăng nhập của user. Trang sprint đọc được ổn định qua thuộc tính `data-*` và các khối JSON nhúng trong trang (§3), không phải bóc chữ. Bot chạy theo lịch trên server vẫn chưa có cách xác thực: ghi thành O11. |
| 2. Ngữ nghĩa `POST /api/task/{id}/assignee` | **Bật/tắt** (toggle): gọi cho người đã có trên đơn là **gỡ** người đó. API hàng loạt có cờ `them=1` (chỉ thêm) / `them=0` (chỉ gỡ). Bot chỉ được dùng API hàng loạt với `them=1` (§4). |
| 3. Webhook chat | Không cần: Q10 chọn "chưa dùng chat". |
| 4. Máy chạy bot, Gemini key | Vẫn cần user. Xem O11: server không dùng được phiên Chrome của user. |
| 5. Nhật ký `hoat-dong` Sprint 6–10 | **Đã đo** trên 425 dòng (40 đơn gốc, 385 subtask). Nhật ký trạng thái chỉ có từ **10/09/2026**. Ngưỡng kẹt trạng thái đo được ở §5; QA trả về được ghi bằng **bug**, gần như không qua trạng thái `qa - need fix` (§6). |
| 6. Nhãn TM cho 18 đơn Sprint 9–10 | Vẫn cần TM (không lấy được từ hệ thống). Ghi thành O13. |

## 2. Cách làm

- Claude in Chrome, tab mới, phiên Google của user (tài khoản thường). **Chỉ gọi GET**: trang folder, 5 trang sprint,
  425 lần `GET /api/task/{id}/hoat-dong`, 40 lần `GET /task/{id}/panel`, và file `/static/app.js`.
- Mọi phép tính chạy trong trình duyệt; chỉ số tổng hợp được mang ra. **Không chép tiêu đề, mô tả, bình luận hay tên
  người vào repo.**
- Sprint của board Maintain (folder `90169740714`): Sprint 6 `901616498181`, Sprint 7 `901616498301`, Sprint 8
  `901617139722`, Sprint 9 `n_40b430b2f9`, Sprint 10 `n_663e74c178`.
- "Ngày làm việc" ở báo cáo này = khoảng thời gian trừ thứ Bảy và Chủ nhật, tính theo đơn vị 24 giờ; chưa trừ ngày lễ
  (T5). Mốc thời gian trong nhật ký là giờ địa phương dạng `YYYY-MM-DD HH:MM:SS`, không ghi múi giờ.

## 3. Đọc hệ thống không cần token

Phiên đăng nhập của user đọc được mọi thứ bot cần ở giai đoạn 2, trừ ngày nghỉ (vẫn ở `devs.xlsx`, D11).

| Dữ liệu | Lấy ở đâu | Dạng |
|---|---|---|
| Sprint của board, ngày bắt đầu/kết thúc | `GET /folder/90169740714`: link `/sprint/{list_id}`; ngày nằm trong tên list | HTML |
| Đơn của sprint | `GET /sprint/{list_id}`: mỗi `tr[data-task]` có `data-parent`, `data-lvl` (0 = đơn gốc), `data-assignee-ids`, `data-appname`; trong dòng có nút `st-btn[data-status]`, `pri-btn[data-value]`, `due-btn[data-value]`, `est-btn[data-value]`, `cf-btn[data-field][data-value]` | HTML, thuộc tính có cấu trúc |
| Bảng trạng thái, user ↔ id | Khối JSON nhúng trong trang sprint: `status-sets` (id → tên trạng thái), `user-data` (33 người đang hoạt động), `user-data-all` (54, gồm người đã rời), `cf-meta`, `filter-fields` | JSON |
| Loại đơn (Task / Subtask / Bug), Ngày tạo, Ngày đóng, Mã ClickUp, mô tả, số bug | `GET /task/{id}/panel`: nút `.pn-loai .loai-nut` (class `la-task`, …); tab Bug có `data-mo` / `data-tong` (bug mở / tổng) | HTML |
| Nhật ký trạng thái, bình luận | `GET /api/task/{id}/hoat-dong` | JSON |

Hai điều cần biết khi thiết kế nguồn dữ liệu (O11):

- **Kết quả trả về qua công cụ Chrome bị lọc:** đoạn nào trông như query string hay cookie bị thay bằng
  `[BLOCKED: …]`. Link trong mô tả đơn vì vậy không mang ra nguyên vẹn được. Không ảnh hưởng tới AI vì AI vốn không
  nhận link (A18), nhưng snapshot phải bỏ link trước khi trả về, hoặc trang tự lưu file.
- **File export của hệ thống không có loại `Bug`:** sheet Sprint 6–10 chỉ có `Task` và `Subtask`. Số bug của một đơn chỉ
  có trên hệ thống.

## 4. `POST /api/task/{id}/assignee` là bật/tắt

Bằng chứng từ `/static/app.js` (code của chính trang, chỉ đọc):

- Chú thích trong code: một task có nhiều người làm, nên đây "không phải chọn-một mà là bật/tắt": chọn lại người đang
  có dấu ✓ thì gỡ người đó ra.
- Body: `user_id`. Phản hồi: `{ok, ids[], names, added, user}`; `added = false` nghĩa là vừa **gỡ**.
- API hàng loạt `POST /api/tasks/hang-loat/assignee`: body `task_ids` (lặp lại cho mỗi task), `user_id`, `them`
  (`1` thêm, `0` gỡ). Phản hồi `{ok, user, doi[{id, ids, names}], bo_qua}`. Đây là cách duy nhất có ý định rõ ràng.

Hệ quả cho bot (A46): chỉ gán qua API hàng loạt với `them=1`, kể cả khi gán một đơn. Gọi lại nhầm cũng không gỡ ai.
Trước khi gọi, đọc lại đơn và bỏ qua nếu `Người làm` không còn trống (K1); sau khi gọi, kiểm `ids` trả về có đúng
người vừa gán. **Chưa gọi thử API ghi nào.**

Nhật ký `hoat-dong` của cả 425 dòng chỉ có 3 loại mục: `tao_task` (425), `trang_thai` (541), `comment` (120).
**Hệ thống không ghi việc đổi người làm**, nên muốn biết PIC đổi lúc nào thì bot phải tự so giữa các lần chạy (K6).

## 5. Ngưỡng kẹt trạng thái (K4)

### Độ phủ của nhật ký

Mục `trang_thai` sớm nhất là **10/09/2026 14:04**: hệ thống bắt đầu ghi nhật ký trạng thái từ ngày đó. Sprint 6–7 gần
như không có lịch sử, Sprint 8 có một phần.

| Sprint | Đơn gốc | có nhật ký trạng thái | Subtask | có nhật ký trạng thái |
|---|---|---|---|---|
| 6 (10/8–14/8) | 3 | 1 | 105 | 1 |
| 7 (17/8–28/8) | 8 | 0 | 72 | 14 |
| 8 (4/9–18/9) | 11 | 8 | 57 | 28 |
| 9 (21/9–2/10) | 12 | 12 | 113 | 98 |
| 10 (6/10–17/10, đang chạy) | 6 | 5 | 38 | 29 |
| **Cộng** | **40** | **26** | **385** | **170** |

Không có lần chuyển trạng thái nào mà `tu` khác trạng thái trước đó: nhật ký liền mạch.

### Thời gian nằm ở một trạng thái (ngày làm việc)

Chỉ tính các lần đã rời trạng thái. Trạng thái có dưới 10 lần chỉ để tham khảo.

| Trạng thái | Đơn gốc: n · P50 · **P80** · P90 · max | Subtask: n · P50 · **P80** · P90 · max |
|---|---|---|
| `all issue` | 11 · 0 · **0,29** · 1,91 · 2,20 | 110 · 0,43 · **1,18** · 2,08 · 12,10 |
| `ready to progress` | 16 · 0,86 · **1,92** · 4,17 · 11,93 | 44 · 0,91 · **2,08** · 3,94 · 8,51 |
| `in progress` | 16 · 0,65 · **3,93** · 4,93 · 6,55 | 94 · 0,21 · **1,07** · 1,18 · 3,21 |
| `ready to qa-testing` | 12 · 0,21 · **1,89** · 1,91 · 1,95 | 66 · 0,67 · **1,89** · 3,16 · 3,67 |
| `qa - testing` | 3 · 0,09 · 0,21 · 0,21 · 0,21 | 34 · 0,13 · **1,06** · 2,19 · 4,17 |
| `need to be clean` | 2 · – | 14 · 0,99 · **2,10** · 3,03 · 3,04 |
| `pending` | 1 · – | 18 · 2,03 · 6,98 · 7,22 · 7,22 |
| `ready to release` | 4 · 4,06 · 5,71 · 5,71 · 5,71 | 0 |
| `ready to internal testing` | 0 | 5 · 0,12 · 0,13 · 0,13 · 0,13 |

### Ngưỡng đề xuất (A49)

Cách tính: trạng thái có ít nhất 10 lần thì ngưỡng = P80 làm tròn lên số ngày nguyên; ít hơn 10 lần thì lấy số lớn hơn
giữa mặc định của form (2 ngày) và P80 làm tròn lên. Chỉ áp cho `in progress` và các trạng thái `ready to …` (K4);
`pending` là trạng thái chờ có chủ đích nên không xét.

| Trạng thái | Đơn gốc | Subtask | So với mặc định của form |
|---|---|---|---|
| `in progress` | **> 4 ngày** | **> 2 ngày** | Form: > 3 (đơn gốc thực tế lâu hơn) |
| `ready to progress` | > 2 | > 3 | Form: > 2 |
| `ready to qa-testing` | > 2 | > 2 | Như form |
| `ready to internal testing` | > 2 (chưa có số đo) | > 2 | Như form |
| `ready to release` | > 6 (4 lần đo, P50 đã 4 ngày) | > 2 (chưa có số đo) | Form 2 ngày sẽ bật trên hơn nửa số đơn |

Thận trọng: số đo chỉ gồm 4 tuần (10/09–09/10) và 16 lần với đơn gốc. Bot đo lại ngưỡng cuối mỗi sprint khi đã có
nguồn dữ liệu từ hệ thống.

Thử trên Sprint 10 đang chạy (sáng 09/10, ngưỡng của đơn gốc áp cho cả subtask): **2/6 đơn gốc** và **12/38 subtask**
đang vượt ngưỡng. Ngưỡng subtask chặt hơn nên số subtask vượt thực tế còn cao hơn. Đó là lý do Q4 gộp subtask kẹt vào
một dòng rủi ro của đơn cha, và K3 giới hạn mỗi đơn một lời nhắc mỗi loại mỗi ngày.

## 6. QA trả về: ghi bằng bug, không qua trạng thái

| Số đo trên 40 đơn gốc Sprint 6–10 | Giá trị |
|---|---|
| Đơn có ít nhất một lần chuyển sang `qa - need fix` (cả cây đơn) | **1** (1 lần) |
| Đơn về `qa - need fix` từ 2 lần trở lên (định nghĩa rủi ro 11 của Q11) | **0** |
| Đơn có ít nhất 1 bug (tab Bug của panel) | **25/40** |
| Số bug mỗi đơn: P50 · P80 · P90 · max | 1 · **5** · 12 · 61 |
| Đơn có từ 5 bug trở lên | 9/40 |
| Đơn đang có bug mở (09/10) | 11/40 |

Rủi ro 11 theo đúng định nghĩa đã chốt sẽ **không bao giờ bật** trên dữ liệu thật. QA trả về ở team này nghĩa là tạo
bug dưới đơn. Đề xuất (O12, chờ user): rủi ro 11 bật khi đơn về `qa - need fix` từ 2 lần trở lên **hoặc** có từ 5 bug
(P80) **hoặc** còn bug mở khi còn ≤ 3 ngày làm việc tới hạn. Số bug chỉ có trên hệ thống nên rủi ro này vẫn thuộc giai
đoạn 2.

## 7. Bình luận

120 bình luận trên 425 dòng, gần như tất cả ở Sprint 9–10 (Sprint 6–7: 0). Một đơn có 71 bình luận trong cây. Rủi ro 12
("BA chưa trả lời") đọc được từ nhật ký, nhưng hệ thống không đánh dấu bình luận nào là câu trả lời cho câu hỏi nào
ngoài `tra_loi_id` / `thread`; bot phải đặt câu hỏi trong thread riêng của mình để nhận ra câu trả lời.

## Câu hỏi còn mở

1. **O11:** bot chạy theo lịch (D36) trên server (D42) cần một cách xác thực không phụ thuộc trình duyệt của user. Không
   có token thì chỉ còn: Claude đọc qua Chrome trên máy user (máy phải bật, Chrome phải mở), hoặc dùng cookie phiên
   của user (Q6 đã không chọn). Mặc định đang dùng: giai đoạn 1 đọc file export; giai đoạn 2 Claude chụp snapshot qua
   Chrome khi user yêu cầu.
2. **O12:** đổi định nghĩa rủi ro 11 như §6?
3. Có cần giữ ngưỡng `ready to release` không? Trạng thái này chờ phát hành lên store, có thể không phải việc của dev.
