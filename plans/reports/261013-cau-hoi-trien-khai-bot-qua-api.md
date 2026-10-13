# Câu hỏi: triển khai scrumbot đọc dữ liệu qua API `/api/doc/`

Ngày 2026-10-13. Liên quan: tài liệu API [`doc_api.md`](../../doc_api.md), danh sách API đã xin
[`261009-danh-sach-api-can-token.md`](261009-danh-sach-api-can-token.md), plan
[`261008-1738-scrum-master-risk-management/`](../261008-1738-scrum-master-risk-management/plan.md), `confirm.md`
D36–D48, A45–A53, O11–O13.

**Cách trả lời**

- Đánh `x` vào ô bạn chọn: `- [x]`. Câu nào ghi "chọn nhiều" thì đánh được nhiều ô.
- **Để trống cả câu nghĩa là đồng ý với phương án "(đề xuất)".** Chỉ cần điền chỗ không đồng ý hoặc cần nói thêm.
- Bảng mục D: đánh một ô `Đồng ý` / `Không đồng ý` mỗi dòng; chọn "Không đồng ý" thì ghi lý do ở `Trả lời:`.
- Trả lời ngắn trong chat cũng được, theo số câu ("Q2: b, K1 không đồng ý vì …").

Sau khi bạn trả lời, mình ghi quyết định vào `confirm.md`, viết spec, sửa plan, rồi mới code.

---

## Kết quả gọi thử API (13/10, 09:40, chỉ gọi GET)

| Điều | Kết quả | Hệ quả cho bot |
|---|---|---|
| Token trên **production** `circle.datlt.site` | 401 "cần đăng nhập Google" ở **mọi** đường dẫn `/api/doc/`, kể cả đường dẫn không tồn tại | Production chưa bật API này (hoặc chưa nhận token). Bot chưa đọc được production |
| Token trên **dev** `devclickup.datlt.site` | 200, cả 3 API chạy, mỗi lần gọi 0,4–1,2 s | Bot đọc được ngay từ dev |
| Độ mới dữ liệu dev | Lần cập nhật mới nhất: 12/10 22:27. Tới 09:40 ngày 13/10 chưa có thay đổi nào của hôm nay | Chưa biết dev dùng chung CSDL với production hay là bản sao, và nếu là bản sao thì đồng bộ lúc nào (Q1) |
| User-Agent | `urllib` của Python với User-Agent mặc định bị Cloudflare chặn (403, mã 1010); đặt User-Agent riêng thì qua | Ví dụ Python trong `doc_api.md` chạy nguyên văn sẽ lỗi 403. Bot tự đặt User-Agent (K2) |
| **Mô tả đơn** | **API không trả mô tả.** File export: 18/40 đơn gốc Sprint 6–10 có mô tả bằng chữ (Sprint 10: 2/6) | AI ước lượng độ lớn (D13) và rủi ro 1 "đơn chưa rõ" (D45) mất đầu vào chính (Q2) |
| Sprint | 34 list trong folder Maintain (từ 08/2025). Có **2 list cùng 06/10–17/10**: `Sprint 10` và `[Test sprint] Sprint 10 - sắp xếp lại`, mỗi list 6 đơn gốc | Cần luật chọn sprint đang chạy (Q4) |
| Sprint 10 | 6 đơn gốc (1 đơn chưa có người làm), 45 subtask, 4 bug. 2/6 đơn có ưu tiên, 1/6 có hạn. Cả 6 đơn gốc thuộc list Tech manager, được kéo vào sprint | |
| Tên người | Tên trong API khớp đúng cột `Tên` của 4 dev trong `devs.xlsx` | `devs.xlsx` dùng tiếp như D11, không cần thêm cột id |
| Tech manager | 350 đơn gốc / 5.808 dòng, 07/2025–10/2026, 1 trang, 2,3 MB. 248 đơn gốc có mặt trong ít nhất 1 sprint Maintain, 102 thì không. **9 đơn trống người làm**, tạo từ 17/09, chưa vào sprint nào | Lịch sử "quen app" dài hơn file export T2–T10. Phân biệt được board Maintain mà không cần cột (K3). 9 đơn trống: Q3 |
| Lịch sử trạng thái | Sprint 10: 55/55 dòng có lịch sử, 177 lần đổi trạng thái (sớm nhất 17/09), 58 comment (chỉ có ai và lúc nào, không có nội dung) | Rủi ro 10 "kẹt trạng thái" và 11 "QA trả về" làm được ngay, không phải chờ GĐ 2 |
| Ghi vào hệ thống | API chỉ đọc. Không có gán người, comment, chuyển sprint (W1–W3) | Hành động 1–5 của D43 vẫn chưa làm được. Kết quả vẫn ra file Excel |
| `.env` | Có một dòng `BearerToken = …` (có dấu cách quanh `=`) | K1 |

---

## A. Nguồn dữ liệu

### Q1. Bot đọc server nào?

- [ ] **(đề xuất)** **Đọc server dev ngay**, vì token chỉ chạy ở đó. Địa chỉ server nằm trong `.env` (K1), nên khi
  production bật API thì chỉ cần sửa `.env`, không sửa code. Báo cáo ghi rõ "dữ liệu cập nhật tới <giờ>" để TM thấy
  độ trễ. **Bạn hỏi giúp TM:** dev dùng chung CSDL với production hay là bản sao, đồng bộ lúc nào, và khi nào bật
  API trên production.
- [ ] Chờ TM bật API trên production rồi mới cho bot đọc. Trong lúc chờ, bot vẫn đọc file export.

Trả lời (13/10, chat): không đọc api trên production, triển khai trên bản dev, tech manager confirm với tôi là vẫn có
data full trên môi trường dev.

### Q2. API không có mô tả đơn. Làm thế nào?

- [ ] **(đề xuất)** **Xin TM thêm trường `mo_ta` vào `/api/doc/don`** (đã bỏ link, như cách API làm với tên đơn;
  D17 đã cho phép gửi mô tả lên AI). Trong lúc chờ: nếu `input/` có file export chứa sprint đó, bot lấy mô tả từ file,
  khớp đơn theo App + tên đơn + ngày tạo; không có file thì AI chỉ đọc tiêu đề. Kiểm tra "không có mô tả bằng chữ"
  của rủi ro 1 chỉ chạy với đơn có nguồn mô tả; đơn không có nguồn thì báo **một** dòng chung "chưa lấy được mô tả từ
  hệ thống", không bật cờ `Cần làm rõ` cho cả 6/6 đơn.
- [ ] Bỏ hẳn mô tả: AI chỉ đọc tiêu đề; rủi ro 1 chỉ còn kiểm tra ưu tiên cao mà không có hạn, thiếu App và checklist
  theo tiêu đề. Độ lớn sẽ kém chính xác hơn trên các đơn có mô tả (18/40).
- [ ] File export vẫn là nguồn chính như GĐ 1 cũ (D41); API chỉ thêm lịch sử trạng thái, bug và comment.

Trả lời (13/10, chat): Xử lý việc thiếu mô tả bằng cách là notification (log).

### Q3. Thứ tự giai đoạn (đổi D47)

D47 hiện ghi: GĐ 1 đọc file export; GĐ 2 cắm nguồn từ hệ thống, rủi ro 10–12, chạy theo lịch; GĐ 3 ghi vào hệ thống.
API đọc đã có sớm hơn dự kiến, nên GĐ 1 viết trên file rồi GĐ 2 viết lại trên API là làm hai lần.

- [ ] **(đề xuất)** **Gộp nguồn API vào GĐ 1.** GĐ 1 mới: đổi tên `scrumbot` và tổ chức 4 lớp (D46); nguồn dữ liệu
  mặc định là API, file export vẫn đọc được bằng `--source file` (cho `eval/`, backtest và khi API lỗi); AI hiểu đơn
  (D38); sổ rủi ro **1–12** (rủi ro 9 và 12 làm được một phần, xem K9 và Q5); báo cáo Excel kèm `Phản hồi BA` và
  `Thay đổi`. GĐ 2: chạy theo lịch (khi có máy, D42) và báo cáo cuối sprint. GĐ 3: ghi vào hệ thống (khi có API ghi).
- [ ] Giữ thứ tự cũ: làm xong GĐ 1 trên file export, rồi mới cắm API.

Trả lời (13/10, chat): Đưa nguồn API vào ngay giai đoạn 1, thay vì làm trên file export rồi làm lại trên API.

### Q4. Đơn nào được giao PIC?

Hiện trạng: Sprint 10 có 1 đơn gốc trống. List Tech manager có thêm 9 đơn trống tạo từ 17/09 chưa vào sprint nào
(6 `ready to progress`, 3 `all issue`).

- [ ] **(đề xuất)** Chỉ đơn gốc trống **trong sprint đang chạy** (như D5, D39). 9 đơn trống ngoài sprint chỉ được
  **đếm** trong tóm tắt ("9 đơn trống chưa vào sprint nào"), không giao, không vào sổ rủi ro.
- [ ] Chỉ đơn trong sprint đang chạy; không nhắc gì tới đơn ngoài sprint.
- [ ] Giao cả đơn trống ngoài sprint.

Trả lời (13/10, chat): Bot chỉ giao đơn trống trong sprint đang chạy.

---

## B. Rủi ro cần dữ liệu mới

### Q5. Rủi ro 12 "BA chưa trả lời": khi nào coi là BA đã trả lời?

API có comment (ai, lúc nào) nhưng không có nội dung. Bot chưa comment được (không có API ghi), nên câu hỏi cho BA
vẫn đi qua sheet `Phản hồi BA` và TM gửi tay.

- [ ] **(đề xuất)** BA coi là **đã trả lời** khi người tạo đơn có ít nhất một comment trên đơn (hoặc subtask của đơn)
  **sau** lần chạy đầu tiên bot đưa câu hỏi đó vào `Phản hồi BA` (bot nhớ trong `state/`, A51). Quá hạn bổ sung (R4)
  mà chưa có comment nào thì bật rủi ro 12. Bot không biết câu trả lời có đủ không.
- [ ] Hoãn rủi ro 12 tới GĐ 3, khi bot tự comment hỏi được.

Trả lời (13/10, chat): Với bản bot hiện tại (mặc định là BA đã xác minh).

---

## C. Nơi chạy

### Q6. Chạy theo lịch (D36) khi chưa có máy luôn bật (D42)

D36 cho chạy theo lịch khi bot đọc được hệ thống mà không cần người. Điều kiện đó nay đã có (với server dev), nhưng
chưa có máy luôn bật.

- [ ] **(đề xuất)** **Chạy tay** cho tới khi có máy (D42). Lệnh `scrumbot` không còn cần file export: đọc API +
  `devs.xlsx` (+ file luật TM nếu có).
- [ ] Đặt lịch trên máy Mac này (`launchd`): 8h30 T2–T6 chạy đầy đủ, rồi 30 phút một lần trong giờ hành chính để giao
  đơn mới. Chỉ chạy khi máy đang bật.

Trả lời (13/10, chat): đặt lịch chạy tự động trên máy Mac này.

---

## D. Mặc định kỹ thuật (Claude chọn, ghi thành dòng A)

| # | Mặc định | Đồng ý | Không đồng ý |
|---|---|---|---|
| K1 | `.env` dùng 2 biến: `SCRUMBOT_API_TOKEN` và `SCRUMBOT_API_BASE` (vd `https://devclickup.datlt.site`). Biến môi trường của shell thắng file. **Bạn tự sửa dòng `BearerToken = …` thành `SCRUMBOT_API_TOKEN=…`**: mình không mở hay sửa `.env`. Thêm `.env.example` (không có giá trị) vào repo. | [ ] | [ ] |
| K2 | Gọi HTTP bằng `urllib` (A52), header `User-Agent: scrumbot/<version>`, timeout 60 s. `429`: chờ 30 s, thử lại tối đa 3 lần. `401`, `404`, `5xx`: dừng với exit 2 và thông báo tiếng Việt nói rõ nên làm gì. Token không bao giờ được in, ghi log hay ghi vào báo cáo. | [ ] | [ ] |
| K3 | Đơn **thuộc board Maintain** = đơn gốc có mặt trong ít nhất một sprint của folder Maintain (248/350). 102 đơn còn lại coi là MVP / nghiên cứu / chưa xếp lịch: chỉ dùng cho "quen app", không tính tải (D23). Thay A21 (export không có cột board). | [ ] | [ ] |
| K4 | Mỗi lần chạy lưu JSON thô nhận từ API vào `state/snapshots/<giờ chạy>/` (không commit, A51; có tên người). Dùng để so với lần trước (rủi ro 9) và chạy lại không cần mạng (`--snapshot DIR`) cho test và điều tra. Giữ 30 ngày. | [ ] | [ ] |
| K5 | Sprint đã lưu trữ (`luu_tru`) không đổi nữa, nên đơn của chúng được cache trong `state/`. Một lần chạy thường ≤ 10 request (giới hạn 120/phút). | [ ] | [ ] |
| K6 | Sprint đang chạy = list `kieu = sprint`, chưa lưu trữ, có tên bắt đầu bằng `Sprint ` (bỏ `[Test sprint] …`, `tech sprint`), có ngày chứa hôm nay. Nhiều list khớp, hoặc không có list nào → dừng, yêu cầu chọn bằng `--sprint-id`. Sprint trước = list cùng điều kiện, có đơn, kết thúc gần nhất trước ngày bắt đầu sprint đang chạy. | [ ] | [ ] |
| K7 | "Còn việc" từ sprint trước vẫn theo **tên** trạng thái của D8, không theo `kieu` của hệ thống (hệ thống xếp `đã ro` và `ready to release` vào nhóm xong). | [ ] | [ ] |
| K8 | Rủi ro 10 "kẹt trạng thái" tính từ `/lich-su` với ngưỡng A49; đơn cũ từ ClickUp không có lịch sử thì dùng `ngay_cap_nhat`. Rủi ro 11 dùng mặc định của O12 (≥ 2 lần `qa - need fix`, hoặc ≥ 5 bug, hoặc còn bug mở khi còn ≤ 3 ngày làm việc tới hạn), đếm bug từ `bug_mo` / `bug_tong`. | [ ] | [ ] |
| K9 | Rủi ro 9 khớp đơn giữa hai lần chạy theo `id` (thay cho App + tên + ngày tạo). Theo dõi đổi `han`, `uu_tien` và tên đơn; đổi mô tả chỉ theo dõi được khi API có `mo_ta` (Q2). | [ ] | [ ] |
| K10 | `eval/` và `--backtest` vẫn chạy trên file export như hiện nay, để thước đo không đổi khi đổi nguồn. Backtest trên dữ liệu API (34 sprint thay vì Sprint 6–10) làm sau. | [ ] | [ ] |
| K11 | Chuyển `doc_api.md` vào `docs/api-doc-he-thong.md` và commit (không chứa bí mật), ghi chú thêm lỗi User-Agent ở trên. | [ ] | [ ] |

Trả lời (13/10): để trống, tức đồng ý K1–K11. K10 bị thay bởi lưu ý về test bên dưới.

**Lưu ý thêm của user (13/10, chat):** Có thể chạy test bằng cách là scan toàn bộ các task cũ trong thời gian trước
sau đó clear hết người được assign ở task đó rồi bạn tự assign người theo luật và quản trị khả năng rủi ro (không được
clear data ở api, có thể clone data rồi tự build một nơi để lưu data cho bot test => Data không bị ảnh hưởng). Confirm
với tôi các điều chưa clear trước khi triển khai.

Các điểm còn chưa rõ: [`261013-cau-hoi-lam-ro-dot-2-api-dev.md`](261013-cau-hoi-lam-ro-dot-2-api-dev.md).

---

## E. Cần bạn hỏi Tech Manager

Không chặn việc code, nhưng chặn chất lượng hoặc giai đoạn sau:

1. **Dev hay production:** dev dùng chung CSDL với production hay là bản sao, đồng bộ lúc nào; khi nào bật
   `/api/doc/` trên production (Q1).
2. **Thêm `mo_ta`** (đã bỏ link) vào mỗi đơn của `/api/doc/don` (Q2).
3. **Ví dụ Python trong tài liệu** chạy nguyên văn bị Cloudflare chặn (403, mã 1010) vì User-Agent mặc định của
   `urllib`. Thêm `"User-Agent": "..."` vào header của ví dụ, hoặc cho `/api/doc/` qua Browser Integrity Check.
4. **(GĐ 3, chưa cần ngay)** API ghi W1–W3: gán người làm, comment, chuyển sprint.
