# Báo cáo đánh giá đợt 1: bộ 5 case

Ngày 2026-10-08. Bộ dữ liệu: [`eval/`](../../eval/README.md). Quyết định: `confirm.md` A35–A44, O10 (user giao
Claude quyết định toàn bộ, xem [`261008-cau-hoi-bo-du-lieu-danh-gia.md`](261008-cau-hoi-bo-du-lieu-danh-gia.md)).

## Kết luận ngắn

1. **Code làm đúng spec.** Ba case giả lập, chạy `--ai off`: PIC 24/24, dự phòng 24/24 đúng như đáp án tính tay;
   cảnh báo không thiếu, không thừa. Qua 3 lần chạy AI, PIC của 3 case này không đổi lần nào.
2. **Độ lớn do AI ước lượng là điểm yếu lớn nhất, và đã sửa.** Trên Sprint 9 thật, AI chỉ xếp đúng hạng 3/12 đơn và
   ước lượng thấp có hệ thống: đơn `1.1.1 - Fix ads/FIx luồng/ fix policy` mất 68h, AI cả 3 lần đều cho `S`. Nguyên
   nhân: prompt không có ví dụ giờ nào (file Tech manager không có cột giờ) và mô tả hạng `S` có chữ "a policy fix".
   Sau khi sửa: đo bằng `agy` trên cùng case, mỗi bản 3 lần: Sprint 9 đúng hạng 6/12
   cả 3 lần (code cũ 3–4/12), lệch ≤ 1 hạng 11/12 (code cũ 9/12). Tính chung 2 sprint thật: 57% đúng hạng, 95% lệch
   ≤ 1 hạng (code cũ 42% và 83%).
3. **Một lỗ hổng báo cáo, đã sửa:** đơn giao sẵn cho dev nghỉ cả sprint không có cảnh báo nào, nên TM không biết đơn
   đó không có ai làm. Nay có cảnh báo `PRE-ASSIGNED-ON-LEAVE` (A43).
4. **Khớp TM:** Sprint 9 khớp 8/11 đơn, Sprint 8 khớp 4/9. Phần lớn chỗ lệch đến từ giới hạn cân tải +1 đơn (D26):
   TM dồn việc cho LinhNV nhiều hơn mức giới hạn cho phép. Nới lên +2 thì backtest tăng từ 47% lên 55%. Đây là dòng D
   nên **cần bạn quyết định** (mục 5).

## 1. Bộ dữ liệu

| Case | Loại | Đơn | Kiểm tra |
|---|---|---|---|
| 1 · Sprint 9 dựng lại | Thật | 12 | PIC so với TM, độ lớn AI so với giờ thật (2h–83h) |
| 2 · Sprint 8 dựng lại | Thật | 11 | Cân tải so với TM (TM giao LinhNV 6/9 đơn) |
| 3 · Giữa sprint | Giả lập | 10 | Đơn giao sẵn, nghỉ cả sprint, nghỉ 3 ngày, việc dở, chạy ngày 22/10 |
| 4 · Luật TM | Giả lập | 12 | Đủ 4 loại luật, luật hết hạn, dev không nhận việc, luật loại hết ứng viên |
| 5 · Dữ liệu bẩn | Giả lập | 13 | Thiếu app, ưu tiên lạ, hạn trước ngày tạo, `Loại` lạ, tên NFD / viết thường / gõ sai, app viết khác, app mới |

Để chạy lại một sprint cũ mà không "nhìn thấy tương lai", tool có thêm cờ `--today` (A35).

## 2. Kết quả lượt baseline (trước khi sửa, gemini × 3)

`eval/results/20261008-1537-baseline/bang-diem.md`

| Case | PIC khớp TM | PIC / dự phòng theo spec | Độ lớn cùng hạng | Lệch ≤ 1 hạng | Đơn đổi PIC giữa 3 lần AI |
|---|---|---|---|---|---|
| 1 · Sprint 9 | 8/11 | — | 3/12, 3/12, 3/12 | 8, 8, 7 /12 | 0 |
| 2 · Sprint 8 | 4/9 | — | 5/8, 4/8, 4/8 | 6, 5, 4 /8 | 1 |
| 3 · Giữa sprint | — | 5/5 · 5/5 | — | — | 0 |
| 4 · Luật TM | — | 10/10 · 10/10 | — | — | 0 |
| 5 · Dữ liệu bẩn | — | 9/9 · 9/9 | — | — | 0 |

Mọi lần chạy đều ra báo cáo (exit 0); AI trả đủ độ lớn cho mọi đơn ở cả 15 lần gọi.

## 3. Phát hiện

### 3.1 Độ lớn AI ước lượng thấp có hệ thống

Sprint 9, giờ thật và hạng AI cho ở lượt baseline (3 lần):

| Đơn | Giờ thật | Hạng thật | AI |
|---|---|---|---|
| PS Remote 1.1.1 - Fix ads/FIx luồng/ fix policy | 68 | XL | S S S |
| Speak2 1.0.6 - Fix ads/Edit luồng/Fix UI | 57 | XL | S M S |
| Game mode 2 1.0.1 - Add ads/Add IAP/Add | 83 | XL | M M M |
| SpeakerCleaner 1.1.2 - Fix ads/Fix luồng/ Fix policy | 22 | M | S S S |
| AR Dog 1.1.1. Add New feature/ Add ads | 17 | M | XL XL XL |

Ở team này một đơn là cả một version app, và các đơn "Fix ads / Fix luồng" mất 22–68h. Prompt cũ mô tả `S` là "a
crash fix, a policy fix", và không có ví dụ giờ nào vì file Tech manager không có cột `Ước lượng (h)` (D25), nên AI
hiểu chữ "Fix" theo nghĩa đen.

Thí nghiệm (gemini, 3 lần mỗi biến thể, Sprint 9):

| Biến thể | Cùng hạng | Lệch ≤ 1 hạng |
|---|---|---|
| Prompt cũ, không ví dụ (baseline) | 3/12 | 7–8/12 |
| Prompt cũ + 22 ví dụ từ sheet Sprint 6–8 | 3–5/12 | 11/12 |
| Prompt mới, không ví dụ | 4–5/12 | 10–11/12 |
| Prompt mới + ví dụ | 4/12 | 11/12 |

Trên Sprint 8, biến thể có ví dụ đạt 8/8 lệch ≤ 1 hạng (baseline 4–6/8). Một phần các lần gọi trong thí nghiệm bị quá
thời gian vì gọi song song làm API key ngừng trả lời (mục 3.5), nên số lần đo ít hơn dự định.

Kết quả sau khi sửa, đo bằng `agy` cho cả code cũ và code mới (gemini không trả lời nữa sau thí nghiệm):

`eval/results/20261008-1610-agy-truoc-sua/` (code `e2b519b`) và `20261008-1610-agy-sau-sua/` (code mới):

| | Code cũ | Code mới |
|---|---|---|
| Sprint 9: đúng hạng | 4, 3, 4 /12 | **6, 6, 6 /12** |
| Sprint 9: lệch ≤ 1 hạng | 9, 9, 9 /12 | **11, 11, 11 /12** |
| Sprint 8: đúng hạng | 3, 5, 6 /8 | 6, 5, 5 /8 |
| Sprint 8: lệch ≤ 1 hạng | 7, 8, 8 /8 | 8, 8, 8 /8 |
| Chung 60 lần xếp hạng | 25 đúng (42%), 50 lệch ≤ 1 (83%) | **34 đúng (57%), 57 lệch ≤ 1 (95%)** |
| Khớp TM | Sprint 9: 8/11; Sprint 8: 5/9 | Sprint 9: 8/11; Sprint 8: 4/9 |

Đơn còn lệch 2 hạng ở Sprint 9 là AR Dog 1.1.1 (17h thật, AI cho `XL` vì tiêu đề có "Add New feature"). Sprint 8 khớp
TM ít hơn 1 đơn: number tracker, không ai trong tầm cân tải quen app, nên người nhận được chọn theo số giờ trong sprint
(tiêu chí 3); độ lớn đổi thì số giờ đổi. Không phải do luật chọn PIC thay đổi.

Lượt đo code mới dùng câu mở đầu prompt "a team of four Android developers"; bản commit đổi thành "an Android app
team" để không ghi cứng số dev. Smoke test với AI thật (`ASSIGNTOOL_TEST_AI=agy`) chạy trên bản commit.

### 3.2 Đơn giao sẵn cho dev nghỉ cả sprint không được báo

Case 3: đơn Speak2 giao sẵn cho MinhNM, người nghỉ cả 10 ngày làm việc. Báo cáo giữ đơn (đúng D10) nhưng không cảnh
báo gì: `Mã PIC` để trống, sheet `Tải dev` ghi MinhNM 0 đơn. Đã thêm cảnh báo `PRE-ASSIGNED-ON-LEAVE` (A43): chỉ bật
khi trên đơn không còn dev nào khác trong danh sách.

### 3.3 Lệch với TM ở hai sprint thật

| Nguyên nhân | Đơn (người TM giao) |
|---|---|
| Giới hạn cân tải +1 đơn (D26) loại đúng người TM chọn; lý do của tool ghi `LinhNV quen app hơn nhưng đang có 2 đơn (cân tải)` | Sprint 8: AR Dog 1.0.7 (LinhNV, AnTD), Game mode 1.1.1 (LinhNV) |
| TM chọn người không làm version gần nhất của app trước sprint đó | Sprint 9: Speak2 (MinhNM), metal detector (LinhNV), SpeakerCleaner (LinhNV); Sprint 8: Nhiều App (LinhNV), number tracker (MinhNM) |
| App chưa ai trong team làm, tool ưu tiên middle | Sprint 8: Roblox skin 1.0.1 (AnTD) |

Nhóm thứ hai không sửa được bằng lịch sử app. Có một dấu hiệu: TM giao 7/9 đơn có chữ "policy" và 3/4 đơn "native too
small" cho LinhNV. Nhưng LinhNV giữ tới 44% mọi đơn, và 9 đơn là quá ít để thêm một luật theo loại việc. Mình **không
đổi** luật chọn PIC vì chuyện này.

### 3.4 Những điểm đúng như spec nhưng nên biết

- Case 4: luật loại hết dev khỏi đơn Lovetest, nên theo A31 đơn được giao như khi không có luật, và rơi vào MinhNM,
  người TM vừa ghi "Minh làm MVP tuần đầu". Cảnh báo `RULE-NO-CANDIDATE` có hiện; TM cần đọc sheet `Cảnh báo`.
- Case 3: AnTD nghỉ 3/10 ngày vẫn nhận 3 đơn như hai dev còn lại, vì nghỉ một phần chỉ dùng để phá hoà (A12). Chưa có
  dữ liệu ngày nghỉ thật để đổi.
- Case 5: đơn giao sẵn cho "Bùi Văn Tiếng" (gõ sai tên TiếnBV) bị coi là người lạ, TiếnBV bị tính thiếu 1 đơn và không
  có cảnh báo nào. Đây là cái giá đã biết của D14.

### 3.5 Công cụ AI

- `gemini`: 15–50 giây mỗi lần với prompt đầy đủ. Sau khoảng 30 lần gọi trong một giờ (có lúc 3 lần song song), API
  key ngừng trả lời: tiến trình treo, không in lỗi, tới khi hết thời gian chờ. `run_eval.py` vì vậy chỉ gọi lần lượt.
- `agy`: khoảng 120 giây mỗi lần (17.000 token suy luận), quá mặc định 180 giây khi chạy hai lượt song song; cần
  `--ai-timeout 540`.

## 4. Đã sửa

| Commit | Thay đổi | Quyết định |
|---|---|---|
| `7f8261a`, `b331837` | Cờ `--today` | A35 |
| `46debf8` | Cảnh báo `PRE-ASSIGNED-ON-LEAVE` | A43 |
| `e2b519b` | Dòng terminal của đơn không có app ghi `(không có app)` thay vì để trống | — |
| `4a13c31`, `90ef6b5` | Ví dụ giờ lấy từ sheet sprint cũ khi file lịch sử không có giờ; viết lại mô tả hạng trong prompt | A19, A44 |

Sau mỗi thay đổi: `ruff check`, `ruff format --check`, `pytest` đều qua (161 test).

## 5. Cần bạn quyết định: giới hạn cân tải (D26)

D26 (bạn đã chốt): chỉ xét dev có số đơn ≤ (ít đơn nhất) + 1. Backtest trên 16 sprint Maintain, mọi đơn M, chỉ đổi
con số này:

| Giới hạn | Khớp TM | Sprint 1–10 (tháng 5–10) | Chênh số đơn trung bình mỗi sprint, tool | Của TM |
|---|---|---|---|---|
| +1 (hiện nay) | 43/92 (47%) | 40/76 (53%) | 1,38 | 2,56 |
| **+2** | **51/92 (55%)** | **47/76 (62%)** | 2,19 | 2,56 |
| +3 | 53/92 (58%) | 48/76 (63%) | 2,50 | 2,56 |
| Không giới hạn | 55/92 (60%) | 50/76 (66%) | 2,62 | 2,56 |

"Chênh số đơn" là số đơn của người nhiều nhất trừ người ít nhất trong sprint. Với +2, tool khớp TM nhiều hơn 8 đơn mà
vẫn chia đều hơn TM. Cái giá: dev quen nhiều app (LinhNV) được nhận nhiều đơn hơn trước khi tool chuyển sang người
khác. Đề xuất của mình: **+2**. Nếu bạn đồng ý, mình sửa D26, tính lại đáp án 3 case giả lập và spec §12, §13.

## 6. Dữ liệu nên crawl thêm (không gấp)

| Dữ liệu | Để làm gì |
|---|---|
| File Tech manager có thêm cột `Ước lượng (h)` và `Mô tả` (D25 nói người export thêm được) | Ví dụ giờ đi thẳng từ lịch sử 8 tháng thay vì vài sheet cũ; backtest dùng được độ lớn AI, chấm độ lớn trên khoảng 90 đơn thay vì 20 |
| File export theo sprint của các sprint cũ hơn (Sprint 1–5 và 14–19), có `Mô tả` và `Ước lượng (h)` | Thêm case dựng lại để chấm độ lớn và khớp TM trên nhiều sprint hơn |
| Ngày nghỉ thật của 4 dev trong vài sprint gần đây | Xem có nên tính ngày nghỉ vào tải không (A12 hiện chỉ dùng để phá hoà) |

## 7. Còn mở

- O10: chưa có TM điền đáp án cho 3 case giả lập (cột `TM điền` trong `dap-an.md`).
- Chữ trong prompt mới rút ra khi đọc Sprint 6–9, cũng là dữ liệu đánh giá, nên mức cải thiện đo được có phần lạc
  quan. Case dựng lại từ sprint mới (Sprint 10, 11 khi có giờ thật) sẽ là phép đo sạch hơn.
