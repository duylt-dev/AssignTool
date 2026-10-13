# Báo cáo: API của hệ thống nội bộ cho bot scrum master

Ngày 2026-10-09. Plan liên quan: [`plans/261008-1738-scrum-master-risk-management/`](../261008-1738-scrum-master-risk-management/plan.md).
Quyết định liên quan: `confirm.md` D19, D20, O8.

Mục tiêu: xác định những API cần gọi để bot scrum master lấy dữ liệu trực tiếp từ hệ thống, thay cho file export
(báo cáo PO §3.2), và những gì còn thiếu cần xin đội hệ thống.

## 1. Tóm tắt

- Hệ thống là **"Dev Sprint" (Pion Workspace)** tại `https://circle.datlt.site/`, viết bằng FastAPI. Danh sách đầy
  đủ API nằm ở **`/openapi.json`**: 102 endpoint, 52 schema.
- **Ghi thì đủ, đọc thì thiếu.** Mọi thao tác bot cần ghi (gán người làm, bình luận cho BA, đổi trạng thái, đổi
  custom field) đều đã có endpoint. Nhưng **không có API JSON nào trả danh sách đơn của một sprint hay chi tiết một
  đơn**: các trang đó trả HTML (render phía server).
- **Không có cơ chế token.** OpenAPI không khai báo `securitySchemes`; cách đăng nhập duy nhất là Google OAuth
  (`/auth/google`) rồi dùng cookie phiên. Bot chạy tự động không có đường nào để xác thực nếu đội hệ thống không thêm.
- Có sẵn JSON tốt cho hai nhu cầu khó nhất của phần quản lý rủi ro: **nhật ký trạng thái có thời điểm** (đơn bị kẹt,
  ngày đóng) và **ánh xạ user ↔ id** (cần để ghi `Người làm`).

## 2. Cách khảo sát

- Mở hệ thống qua Claude in Chrome bằng phiên đăng nhập của user (tài khoản **không phải quản trị**), đọc
  `/openapi.json`, rồi gọi thử các endpoint **GET** để xem cấu trúc phản hồi thật.
- **Không gọi bất kỳ POST nào.** Cấu trúc body của API ghi lấy từ OpenAPI, chưa kiểm chứng bằng lời gọi thật.
- Chỉ ghi tên trường và kiểu, không chép dữ liệu đơn hay tên người. Mẫu: sprint đang mở của Maintain (43 dòng),
  15 đơn cho nhật ký hoạt động.

## 3. Nhu cầu dữ liệu → endpoint

Trạng thái: ✅ có JSON · 🟡 chỉ có HTML (đọc được bằng cách bóc HTML, dễ vỡ) · 🔒 có nhưng tài khoản này bị 403 ·
❌ không có.

| # | Bot cần | Dùng cho | Endpoint | Dạng | TT |
|---|---|---|---|---|---|
| 1 | Đơn của sprint: ID, tên, đơn cha, cấp, người làm, App, trạng thái, ưu tiên, hạn, ước lượng, người tạo | Giao PIC, `READY-GAPS`, tải dev | `GET /sprint/{list_id}` | HTML | 🟡 |
| 2 | Chi tiết đơn: mô tả, custom field, Bắt đầu, Ngày tạo, Cập nhật, **Ngày đóng**, Task cha, Mã ClickUp | Đơn đủ rõ chưa, phản hồi BA | `GET /task/{task_id}/panel` (~41 KB) | HTML | 🟡 |
| 3 | Danh sách sprint của board, ngày bắt đầu/kết thúc | Sức chứa, `DUE-AT-RISK`, số ngày còn lại | `GET /`, `GET /folder/{folder_id}` (thanh bên) | HTML | 🟡 |
| 4 | Tiến độ sprint | Báo cáo tổng | `GET /api/sprint/{list_id}/progress` | JSON | ✅ |
| 5 | Lịch sử: tạo đơn, đổi trạng thái (từ → đến, thời điểm), bình luận | Đơn kẹt, ngày đóng, so với lần chạy trước | `GET /api/task/{task_id}/hoat-dong` | JSON | ✅ |
| 6 | User và id | Đổi tên dev ↔ `user_id` để ghi | `GET /api/task/{task_id}/nguoi-tag` | JSON | ✅ |
| 7 | Thành viên theo space / folder / list | Ai thuộc board | `GET /api/quan-tri/{space\|folder\|list}/{id}/thanh-vien` | JSON | 🔒 |
| 8 | Lịch sử list "Tech manager" (quen app) | Tiêu chí 2 của §7 | `GET /sprint/{list_id}` của list đó | HTML | 🟡 |
| 9 | Giờ làm thực tế | Đối chiếu kích thước AI, tải | Không có worklog. `/quan-tri/bao-cao` (lọc team, kỳ, người, từ, đến) có thể chứa số liệu này | HTML/PDF | 🔒 |
| 10 | Ngày nghỉ của dev | `PIC-ABSENT`, sức chứa | — | — | ❌ |
| 11 | Backlog | Đơn chưa vào sprint | `GET /backlog` (~3,4 MB) | HTML | 🟡 |

### Chi tiết các API đọc JSON đã kiểm chứng

| Endpoint | Cấu trúc phản hồi |
|---|---|
| `GET /api/sprint/{list_id}/progress` | `{total, done, pct}` |
| `GET /api/task/{task_id}/hoat-dong?van_tay=` | `{ok, doi, van_tay, muc[]}`. Mỗi mục: `loai` ∈ {`tao_task`, `trang_thai`, `comment`}, `luc` (thời điểm), `user{id, username, initials, color, avatar_url}`. `trang_thai` có `tu{ten, mau}` → `den{ten, mau}`; `comment` có `id, body, thread, tra_loi_id, cam_xuc, cua_toi, build`. `van_tay` là dấu vân tay để hỏi "có gì mới không" (`doi`). |
| `GET /api/task/{task_id}/nguoi-tag` | `{ok, users[{id, username, initials, color, avatar_url}]}`: 23 user |
| `GET /api/thong-bao?sau=`, `/api/thong-bao/ds` | Thông báo của chính người đăng nhập; bot không cần |

**Trong 15 đơn mẫu không có mục nào ghi việc đổi người làm.** Nếu hệ thống không ghi loại này, bot không biết PIC đổi
lúc nào và ai đổi (cần cho "so với lần chạy trước" và backtest).

### Cấu trúc HTML trang sprint (nếu phải bóc HTML tạm thời)

- Mỗi đơn là một `TR` có `data-task` (ID dạng `n_xxxxxxxxxx`), `data-parent`, `data-lvl` (0 = đơn gốc; subtask lồng
  tới cấp 4), `data-assignee-ids`, `data-appname`. Ô trạng thái có `data-status` (tên trạng thái).
- Custom field có id cố định: App Name = `d0419a6d-68c8-4b0c-98e3-ca92ab1eba8d`. Panel đơn còn có Design Type,
  Diagram type, Mạng QC, Định Dạng và Git Pull Request.
- 17 cột của bảng: Task · App Name. · Trạng thái · Người làm · Ưu tiên · Hạn · Ước lượng (h) · Người tạo · điểm ·
  Đánh giá DEV · Đánh giá Test · Dev Review · Test Review · Relate to · note · Git Pull Request · Ads SDK.
- Ngày bắt đầu/kết thúc sprint chỉ có trong tên list (`Sprint 10 (10/6 - 10/17)`) và tiêu đề trang.
- Trường **Loại** không có trên bảng, chỉ có trong panel đơn: nút `.pn-loai .loai-nut` (class `la-task`, …). Bổ
  sung 2026-10-09 ([`261009-bao-cao-du-lieu-he-thong-qua-chrome.md`](261009-bao-cao-du-lieu-he-thong-qua-chrome.md) §3).

## 4. API ghi bot sẽ dùng (giai đoạn C, D19)

Tất cả là `POST` với body `application/x-www-form-urlencoded`. **Chưa gọi thử.**

| Việc | Endpoint | Body |
|---|---|---|
| Gán người làm | `POST /api/task/{task_id}/assignee` | `user_id` (int, bắt buộc) |
| Gán hàng loạt | `POST /api/tasks/hang-loat/assignee` | `task_ids`, `user_id`, `them` |
| Bình luận / phản hồi BA | `POST /api/task/{task_id}/comment` | `body`, `parent_id`, `tra_loi_id`, `thread_ten` |
| Đổi trạng thái | `POST /api/task/{task_id}/status` | `status_id` (int, bắt buộc) |
| Đổi custom field | `POST /api/task/{task_id}/custom-field/{field_id}` | `value` |
| Hạn, ưu tiên, loại, ước lượng | `POST /api/task/{task_id}/{due-date\|priority\|loai\|time-estimate}` | `due_date` / `priority` / `loai` / `time_estimate` |
| Chuyển sprint | `POST /api/task/{task_id}/sprint` | `list_id` |

**Đã rõ (2026-10-09, đọc `/static/app.js`):** `POST /api/task/{id}/assignee` là **bật/tắt**: gọi cho người
đã có trên đơn là gỡ người đó (phản hồi `added = false`). Bản hàng loạt có cờ `them` (`1` thêm, `0` gỡ), gửi
`task_ids` lặp lại cho mỗi task. Bot chỉ dùng bản hàng loạt với `them=1` (`confirm.md` A46).

## 5. Cần xin đội hệ thống

Theo thứ tự ưu tiên. Mục P1 chặn mọi việc tích hợp.

| Ưu tiên | Yêu cầu | Lý do |
|---|---|---|
| P1 | **Token / API key cho bot** (tài khoản dịch vụ). *2026-10-09: user không xin token; xem `confirm.md` D41, O11.* Quyền đọc board Maintain, MVP và list Tech manager; quyền ghi `assignee` và `comment` | Hiện chỉ có đăng nhập Google; D20 nói tool không được cấp tài khoản |
| P1 | **`GET` JSON danh sách đơn của một list/sprint**: id, tên, `parent_id`, trạng thái, `assignee_ids`, ưu tiên, hạn, ước lượng, người tạo, ngày tạo, ngày đóng, custom field (App Name, Loại), mô tả | Thay cho bóc HTML ở mục 1, 2, 8 |
| P2 | `GET` JSON danh sách sprint của một folder, kèm ngày bắt đầu/kết thúc | Mục 3; đang phải đọc ngày từ tên list |
| P2 | Ghi **đổi người làm** vào `hoat-dong` (một `loai` mới, có `tu` → `den`) | Theo dõi PIC đổi, so với lần chạy trước |
| ~~P2~~ | ~~Xác nhận ngữ nghĩa của `POST .../assignee`~~: đã rõ, là bật/tắt (mục 4) | — |
| P3 | Giờ làm thực tế (worklog) và ngày nghỉ của dev | Mục 9, 10; hiện vẫn lấy từ `devs.xlsx` |
| P3 | Quyền đọc `thanh-vien` cho token của bot | Mục 7 |

**Không nên dùng phiên Google cá nhân để bóc HTML cho bot thật.** HTML đổi là bot vỡ; mọi hành động sẽ mang tên
người dùng chứ không phải bot; và D20 đã nói tool không được cấp quyền. Chỉ dùng cách này để làm bản thử, khi chủ hệ
thống đã đồng ý.

## 6. Ảnh hưởng tới plan và `confirm.md`

- Đã sửa `confirm.md` ngày 2026-10-09 (user đồng ý): D19, D20 và O8 ghi theo kết quả khảo sát này. Sửa luôn câu
  tương ứng trong `README.md`.
- O8 cần "tài liệu API": danh sách API đã có ở `/openapi.json`. Còn thiếu token và API đọc JSON (mục 5).
- D20 từng viết "có API đọc đơn": thực tế chỉ có trang HTML, chưa có API JSON đọc đơn.
- ID đơn có dạng `n_xxxxxxxxxx`, panel còn có `Mã ClickUp`. File export theo sprint vẫn chưa có cột ID (O8).
- Panel có **Ngày đóng** và nhật ký có thời điểm chuyển trạng thái. Hai nguồn này có thể bù cho việc file Tech
  manager chỉ có 1/178 đơn có `Ngày đóng` (plan, mục "Out of scope").

## Câu hỏi còn mở

1. ~~`POST /api/task/{id}/assignee` thêm, thay hay bật/tắt?~~ Bật/tắt (mục 4).
2. `/openapi.json` có mở cho người chưa đăng nhập không? (Lần khảo sát này đọc khi đã đăng nhập.)
3. ~~Trường "Loại" của đơn nằm ở đâu trong hệ thống?~~ Trong panel đơn (mục 3).
4. Báo cáo `/quan-tri/bao-cao` có giờ làm thực tế không? Cần một tài khoản quản trị xem giúp.
