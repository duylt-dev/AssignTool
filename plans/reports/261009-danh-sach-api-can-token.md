# Danh sách API bot `scrumbot` cần

Hệ thống: Dev Sprint (`https://circle.datlt.site/`). Kiểm trên `/openapi.json` ngày 2026-10-09. Token và header
cần dùng được cho mọi API dưới đây.

| # | API | Dùng để | Trả về |
|---|---|---|---|
| R1 | `GET /folder/{folder_id}` | Lấy danh sách sprint của board Maintain update (`folder_id` = `90169740714`) và ngày bắt đầu/kết thúc của từng sprint | HTML (trang web) |
| R2 | `GET /sprint/{list_id}` | Lấy các đơn và subtask của một sprint: id, đơn cha, người làm, App, trạng thái, ưu tiên, hạn, ước lượng; kèm bảng trạng thái và danh sách user. Gọi cho sprint đang chạy, sprint trước và list Tech manager (`901609972453`) để biết ai đã làm app nào | HTML (trang web) |
| R3 | `GET /task/{task_id}/panel` | Lấy chi tiết một đơn: mô tả, loại (Task / Subtask / Bug), ngày tạo, ngày đóng, số bug mở/tổng | HTML (một phần trang) |
| R4 | `GET /task/{task_id}/tab-bug` | Lấy danh sách bug của một đơn và trạng thái từng bug | HTML (một phần trang) |
| R5 | `GET /api/task/{task_id}/hoat-dong?van_tay=` | Lấy nhật ký của đơn: tạo đơn, đổi trạng thái (từ → đến, thời điểm), bình luận. Dùng để biết đơn kẹt trạng thái và BA đã trả lời câu hỏi chưa | JSON `{ok, doi, van_tay, muc[]}` |
| R6 | `GET /api/sprint/{list_id}/progress` | Lấy tiến độ sprint | JSON `{total, done, pct}` |
| R7 | `GET /api/task/{task_id}/nguoi-tag` | Lấy danh sách user và `id`, để gán người làm và tag người tạo đơn | JSON `{ok, users[{id, username, initials, color, avatar_url}]}` |
| W1 | `POST /api/tasks/hang-loat/assignee`<br>body: `task_ids`, `user_id`, `them` | Gán người làm cho đơn (`them=1`); gỡ người cũ khi đổi PIC (`them=0`) | JSON `{ok, user, doi[{id, ids, names}], bo_qua}` |
| W2 | `POST /api/task/{task_id}/comment`<br>body: `body`, `parent_id`, `tra_loi_id`, `thread_ten` | Comment hỏi BA khi đơn chưa rõ; nhắc PIC khi đơn kẹt hoặc sắp trễ hạn | JSON |
| W3 | `POST /api/task/{task_id}/sprint`<br>body: `list_id` | Thêm đơn vào sprint sau khi sprint quá tải | JSON |

Body của các API `POST` gửi dạng `application/x-www-form-urlencoded`. Cấu trúc phản hồi của W2, W3 lấy từ
`/openapi.json`, chưa gọi thử.

## Cần thêm bản JSON cho R1–R4

R1–R4 trả HTML vì đó là trang web cho người xem, không phải API. Bot đọc được bằng cách bóc HTML, nhưng giao diện đổi
là bot đọc sai. Cần đội hệ thống thêm:

| Thay cho | API JSON cần | Trả về |
|---|---|---|
| R2, R3, R4 | Danh sách đơn của một sprint | Mỗi đơn: id, tên, đơn cha, loại, trạng thái, người làm (id), ưu tiên, hạn, ước lượng, App, người tạo, ngày tạo, ngày đóng, mô tả, số bug mở/tổng |
| R1 | Danh sách sprint của một folder | Mỗi sprint: id, tên, ngày bắt đầu, ngày kết thúc |
