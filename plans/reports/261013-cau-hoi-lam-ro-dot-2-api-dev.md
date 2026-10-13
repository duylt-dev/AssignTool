# Câu hỏi đợt 2: làm rõ trước khi triển khai scrumbot trên API dev

Ngày 2026-10-13. Tiếp theo form [`261013-cau-hoi-trien-khai-bot-qua-api.md`](261013-cau-hoi-trien-khai-bot-qua-api.md)
(câu trả lời trong chat của bạn đã được chép vào đó). Liên quan: `confirm.md` D36–D48, A45–A53.

**Cách trả lời** giống form trước:

- Đánh `x` vào ô bạn chọn: `- [x]`.
- **Để trống cả câu nghĩa là đồng ý với phương án "(đề xuất)".**
- Bảng K: mỗi dòng đánh một ô `Đồng ý` / `Không đồng ý`; không đồng ý thì ghi lý do ở `Trả lời:`.
- Trả lời ngắn trong chat cũng được ("C2: b; K14 không đồng ý vì …").

Sau đợt này mình ghi tất cả vào `confirm.md`, viết spec, sửa plan, rồi mới code.

---

## 1. Mình hiểu câu trả lời của bạn như sau

| Câu | Bạn trả lời | Mình sẽ làm | Dòng bị đổi |
|---|---|---|---|
| Q1 | Không đọc production; chạy trên dev; TM xác nhận dev có đủ dữ liệu | Bot chỉ gọi `devclickup.datlt.site` (K12) | D41, O11 |
| Q2 | Thiếu mô tả: xử lý bằng notification (log) | Xem C4 | D45 (rủi ro 1) |
| Q3 | Nguồn API vào ngay GĐ 1 | GĐ 1 đọc API; file export dùng vào việc gì: C6 | D41, D47 |
| Q4 | Chỉ giao đơn trống trong sprint đang chạy | Đơn gốc trống của sprint đang chạy; 9 đơn trống ngoài sprint: K13 | giữ D5, D39 |
| Q5 | Bản hiện tại mặc định BA đã xác minh | Bỏ những gì: C5 | D44, D45, D48 |
| Q6 | Đặt lịch chạy trên máy Mac này | `launchd`: C1–C3 | D36, D42 |
| Test | Giao lại các đơn cũ trên bản sao dữ liệu, không đụng API | C7, C8 | D22, K10 cũ |
| K1–K11 | Để trống | Đồng ý; K10 bị thay bởi mục test | thành dòng A |

**GĐ 1 mới** (đổi D47): đổi tên `scrumbot` và tổ chức 4 lớp; nguồn API dev và bản sao để test; AI hiểu đơn theo
tiêu đề; sổ rủi ro **2–11** (rủi ro 1 và 12: C5); báo cáo Excel kèm sheet `Thay đổi`; test giao lại trên dữ liệu cũ;
chạy theo lịch trên máy Mac. **GĐ 2:** ghi vào hệ thống (D43) khi có API ghi.

**Việc bạn cần làm (K1):** `.env` vẫn có dòng `BearerToken = …`. Đổi thành hai dòng:

```
SCRUMBOT_API_TOKEN=<token>
SCRUMBOT_API_BASE=https://devclickup.datlt.site
```

Sáng nay mình chỉ đọc token từ `.env` để gọi thử, không in ra và không sửa file.

---

## 2. Số đo sáng nay (13/10, 09:54, chỉ gọi GET trên dev)

| Điều | Kết quả |
|---|---|
| **Độ mới dữ liệu dev** | Bản ghi mới nhất lúc **12/10 22:27** (lần đổi trạng thái cuối 17:22, comment cuối 18:08). Tới 09:54 thứ Ba **chưa có thay đổi nào của hôm nay**, trong khi thứ Hai có 52 dòng Tech manager được cập nhật. Có thể dev là bản sao đồng bộ mỗi tối; chưa chắc. "Đủ dữ liệu" chưa chắc đã là "dữ liệu mới" (E1) |
| Sprint có trên dev | 34 list: **29 sprint thật có đơn** (08/2025–10/2026), 3 list test (`[Test sprint] …` và 2 bản sao sprint 03/12/2025), 2 list rỗng |
| Đơn gốc để giao lại | Khoảng 320 lượt đơn gốc trong 29 sprint (một đơn có thể nằm ở nhiều sprint), 208 lượt có dev trong pool làm PIC. Năm 2025: 52% đơn có dev pool; năm 2026: 74% |
| Dev pool lần đầu làm PIC | LinhNV, MinhNM: 08/2025. TiếnBV: 10/2025. **AnTD: 06/2026** |
| Lịch sử trạng thái | Chỉ có từ 09/2026 (Sprint 9–10). Trước đó chỉ có ngày tạo, ngày cập nhật cuối và ngày đóng |

---

## 3. Câu hỏi

### A. Chạy theo lịch trên máy Mac (Q6)

#### C1. Lịch chạy

- [x] **(đề xuất)** Như D36: **8h30 T2–T6 chạy đầy đủ** (giao đơn trống, sổ rủi ro, tóm tắt buổi sáng); **9h00–17h30
  cứ 30 phút chạy lại**, nhưng chỉ ghi báo cáo mới khi có thay đổi (có đơn mới được giao, hoặc sổ rủi ro đổi), không
  đổi thì chỉ ghi một dòng log. Nếu dev chỉ đồng bộ mỗi tối thì các lần 30 phút không thấy gì mới, không gây hại. Máy
  tắt thì bỏ lượt đó; máy ngủ thì chạy bù một lần khi máy thức.
- [ ] Chỉ chạy lúc 8h30 mỗi ngày làm việc.
- [ ] Giờ khác (ghi ở `Trả lời:`).

Trả lời:

#### C2. Kết quả chạy theo lịch nằm ở đâu, ai xem?

- [x] **(đề xuất)** Báo cáo Excel ghi vào `state/bao-cao/`, log ghi vào `state/log/` (không commit, như A51). Khi một
  lần chạy có đơn được giao hoặc có rủi ro mức Cao mới, máy Mac hiện **thông báo** ở góc màn hình kèm tên file. Bạn mở
  file rồi chuyển cho TM (D44: TM nhận tóm tắt bằng Excel). `output/` (được commit, D18) chỉ dùng cho lần chạy tay.
- [ ] Ghi vào `output/` như khi chạy tay; không hiện thông báo.
- [ ] Khác (ghi ở `Trả lời:`).

Trả lời:

#### C3. macOS chặn tiến trình chạy nền đọc `~/Desktop`

macOS không cho tiến trình chạy nền (`launchd`) đọc thư mục Desktop khi chưa được cấp quyền, mà repo đang nằm ở
`~/Desktop/AssignTools`.

- [x] **(đề xuất)** Giữ repo ở Desktop. Khi cài lịch, mình chạy thử job một lần: macOS sẽ hỏi có cho python của bot
  truy cập Desktop không, bạn bấm **Allow**. Nếu macOS không hỏi mà chặn luôn, bạn cấp quyền trong System Settings ›
  Privacy & Security (mình ghi từng bước).
- [ ] Chuyển repo ra khỏi Desktop (ví dụ `~/Code/AssignTools`). Không cần cấp quyền, nhưng VSCode và bộ nhớ của
  Claude cho dự án này phải trỏ sang đường dẫn mới.

Trả lời:

### B. Mô tả đơn (Q2) và "BA đã xác minh" (Q5)

#### C4. "Notification (log)" khi đơn thiếu mô tả nghĩa là gì?

API không trả mô tả cho **bất kỳ** đơn nào, nên đơn nào cũng "thiếu mô tả".

- [x] **(đề xuất)** AI hiểu đơn và ước lượng độ lớn chỉ từ tiêu đề, App và ưu tiên. Mỗi lần chạy ghi **một** dòng vào
  log và lên đầu báo cáo: "Hệ thống chưa trả mô tả: 6 đơn được ước lượng chỉ theo tiêu đề". Không bật cờ, không vào sổ
  rủi ro, không hỏi BA, không lấy mô tả từ file export. Vẫn nhờ TM thêm `mo_ta` vào API (E2); khi API có mô tả, bot
  tự dùng và dòng log tự mất.
- [ ] Như trên, nhưng ghi một dòng log cho **từng đơn**.
- [ ] Như đề xuất, nhưng không xin TM thêm `mo_ta`.

Trả lời:

#### C5. "Mặc định BA đã xác minh" bỏ những gì?

- [x] **(đề xuất)** Bot coi mọi đơn BA lên là đủ rõ.
  - **Bỏ ở bản này:** rủi ro 1 "đơn chưa rõ" (cờ `Cần làm rõ`, checklist theo loại đơn, câu hỏi cho BA, hạn bổ sung),
    sheet `Phản hồi BA`, rủi ro 12 "BA chưa trả lời".
  - **Giữ:** hai kiểm tra không cần mô tả (thiếu App; đơn urgent/high không có hạn), báo thành cảnh báo dữ liệu trong
    báo cáo, không thành câu hỏi cho BA. AI vẫn trả loại đơn và rủi ro kỹ thuật nhìn thấy từ tiêu đề (SDK mới, hạn
    store).
  - Phần bỏ làm ở bản sau, khi API có mô tả và bot comment được.
- [ ] Chỉ bỏ rủi ro 12; rủi ro 1 và `Phản hồi BA` giữ như D45, D48. Lưu ý: checklist chỉ đọc được tiêu đề, nên sẽ báo
  thiếu ở gần như mọi đơn.

Trả lời:

### C. Nguồn dữ liệu (Q3)

#### C6. File export còn dùng vào việc gì?

- [x] **(đề xuất)** API là nguồn của mọi lần chạy: chạy tay, chạy theo lịch và test. Phần đọc file export **giữ nguyên,
  không thêm tính năng**, chỉ để `eval/` (5 case, thước đo mỗi khi đổi §6.4, §7, §14) chạy như cũ. Lệnh `--backtest`
  trên file export được thay bằng test giao lại trên bản sao API (C7).
- [ ] Bỏ hẳn file export: chuyển 5 case của `eval/` sang dạng dữ liệu API (thêm khoảng 1 ngày việc), xoá phần đọc
  file export (giữ `devs.xlsx` và file luật TM).

Trả lời:

### D. Test bằng dữ liệu cũ (lưu ý của bạn)

Cách làm mình đề xuất:

1. **`scrumbot clone`**: gọi GET lấy cả 34 list Maintain, list Tech manager và lịch sử trạng thái, ghi nguyên JSON vào
   `state/clone/<ngày giờ>/` (không commit vì có tên người). Khoảng 170 request, 2–4 phút (giới hạn 120 request/phút).
2. **`scrumbot replay --clone <thư mục>`**: với mỗi sprint, xoá người làm của đơn gốc **trong bộ nhớ**, cho bot giao lại
   theo ngày lên đơn (như backtest §13) và lập sổ rủi ro, rồi so với những gì đã xảy ra thật.

Bản sao trên đĩa không bị sửa. API chỉ nhận GET, nên bot không có cách nào ghi hay xoá dữ liệu trên hệ thống.

#### C7. Chấm phần giao người

- [x] **(đề xuất)** Như backtest §13: một đơn **khớp** khi PIC bot chọn là một trong các dev pool mà TM đã giao. Đơn
  không có dev pool nào thì bỏ qua. Mỗi dev chỉ vào pool từ sprint đầu tiên họ làm PIC (AnTD từ 06/2026, TiếnBV từ
  10/2025), để bot không giao đơn năm 2025 cho người chưa vào team. "Quen app" và việc dở lấy theo người TM đã giao
  thật, vì thực tế đã diễn ra theo lựa chọn của TM. Chạy cả 29 sprint, báo kết quả theo từng sprint, không đặt ngưỡng
  (D22).
- [ ] Chỉ chạy từ 06/2026, khi đã đủ 4 dev (9 sprint).
- [ ] Khác (ghi ở `Trả lời:`).

Trả lời:

#### C8. Chấm phần quản trị rủi ro

Hệ thống không có "đáp án" cho rủi ro, nên cần chọn một thước đo.

- [x] **(đề xuất)** So cảnh báo của bot với **kết cục thật** của từng đơn.
  - Đơn có **kết cục xấu** khi: chưa xong lúc hết sprint (`ngay_dong` trống hoặc sau ngày kết thúc, hoặc đơn có mặt ở
    sprint sau), hoặc đóng sau `han`, hoặc có từ 5 bug (P80, O12).
  - Bot lập sổ rủi ro ở **3 mốc** mỗi sprint: ngày đầu, ngày làm việc thứ 5, và lúc còn 3 ngày làm việc. Ở mỗi mốc bot
    chỉ thấy dữ liệu có trước mốc đó (đơn theo ngày tạo, subtask và bug mở theo ngày tạo / ngày đóng, trạng thái theo
    lịch sử).
  - Báo theo từng loại rủi ro: trong các đơn bot báo mức Cao hoặc Trung bình, bao nhiêu % có kết cục xấu (**báo
    đúng**); trong các đơn có kết cục xấu, bao nhiêu % được bot báo trước (**báo đủ**); và báo trước bao nhiêu ngày.
  - Giới hạn: lịch sử trạng thái chỉ có từ 09/2026, nên rủi ro "kẹt trạng thái" chỉ chấm được trên Sprint 9–10; hạn,
    ưu tiên và tên đơn là giá trị hiện tại, có thể đã bị sửa sau mốc.
- [ ] Chỉ chấm phần giao người; sổ rủi ro của từng sprint thì bạn đọc tay.
- [ ] Đồng ý cách chấm, nhưng "kết cục xấu" định nghĩa khác (ghi ở `Trả lời:`).

Trả lời:

---

## 4. Mặc định kỹ thuật mới (Claude chọn, ghi thành dòng A)

| # | Mặc định | Đồng ý | Không đồng ý |
|---|---|---|---|
| K12 | Bot **từ chối địa chỉ production** `circle.datlt.site` (dừng với exit 2, thông báo tiếng Việt) cho tới khi bạn đổi Q1. Lý do: ví dụ trong `doc_api.md` mặc định gọi production, chép nhầm là đọc sai server. | [x] | [ ] |
| K13 | (Q4) Các đơn trống ở list Tech manager chưa vào sprint nào (sáng nay: 9 đơn) chỉ được **đếm** thành một dòng trong tóm tắt; không giao, không vào sổ rủi ro. | [x] | [ ] |
| K14 | Đề xuất PIC của bot được **giữ nguyên giữa các lần chạy** (nhớ trong `state/`) cho tới khi đơn có người làm thật trên hệ thống. Chỉ tính lại khi dev đó nghỉ hết phần còn lại của sprint hoặc không còn `Nhận việc` = `Y`. Đề xuất vẫn được tính vào tải của dev. Không có điều này, lần chạy 30 phút sau có thể đề xuất người khác cho cùng một đơn. | [x] | [ ] |
| K15 | Kết quả AI được nhớ theo id đơn + tên đơn; AI chỉ chạy cho đơn mới hoặc đơn đổi tên. Các lần chạy 30 phút thường không gọi AI. | [x] | [ ] |
| K16 | Chạy theo lịch dùng `agy` trên máy này (đường dẫn đầy đủ `~/.gemini/bin/agy`, không cần key). AI lỗi thì mọi đơn là `M`, lần chạy vẫn thành công và báo cáo ghi rõ (như hiện nay). | [x] | [ ] |
| K17 | Test giao lại mặc định chạy không có AI (mọi đơn `M`, như backtest §13), có cờ để bật AI; kết quả AI nhớ theo K15. | [x] | [ ] |
| K18 | Khi giao lại sprint cũ, việc dở lúc đầu sprint = đơn của sprint trước **chưa đóng** tại ngày bắt đầu (`ngay_dong` trống hoặc sau ngày đó), vì trước 09/2026 không có lịch sử trạng thái. Từ 09/2026 dùng tên trạng thái như D8 và K7. | [x] | [ ] |
| K19 | Thêm `state/` (bản sao, snapshot, báo cáo theo lịch, log, SQLite) vào `.gitignore`. Log giữ 30 ngày; bản sao giữ tới khi bạn xoá. Token không bao giờ được ghi vào log. | [x] | [ ] |
| K20 | Cài và gỡ lịch bằng một script (`launchctl`); gỡ xong là bot không chạy nền nữa. | [x] | [ ] |
| K21 | Báo cáo cuối sprint (D44) làm luôn trong GĐ 1, dùng cùng cách chấm với C8 cho sprint vừa kết thúc. | [x] | [ ] |

Trả lời:

---

## 5. Nhờ bạn hỏi Tech Manager (không chặn việc code)

1. **Dev đồng bộ với production thế nào:** liên tục, hay mỗi tối, vào mấy giờ? Số đo ở mục 2 cho thấy dev chưa có
   thay đổi nào của sáng 13/10. Nếu dev chỉ đồng bộ mỗi tối, bot sẽ giao đơn chậm tới một ngày so với lúc BA lên đơn.
2. **Thêm trường `mo_ta`** (đã bỏ link) vào mỗi đơn của `/api/doc/don`, nếu C4 giữ phương án đề xuất.
3. (Từ form trước) Ví dụ Python trong tài liệu API chạy nguyên văn sẽ bị Cloudflare chặn (403, mã 1010) vì
   User-Agent mặc định của `urllib`.
