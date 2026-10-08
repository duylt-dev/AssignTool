# Câu hỏi: luật động của Tech Manager

Ngày 2026-10-07. Mục tiêu: TM tự thêm luật giao việc (vd "AR Dog luôn giao Linh", "sprint này Minh không nhận đơn")
mà không phải sửa code, và tool vẫn giải thích được từng lựa chọn.

**Cách trả lời**

- Đánh `x` vào ô bạn chọn: `- [x]`.
- **Để trống cả câu nghĩa là đồng ý với phương án có ghi "(đề xuất)".** Chỉ cần điền chỗ không đồng ý hoặc cần nói thêm.
- Ghi chú thêm thì viết vào dòng `Trả lời:` của câu đó.

Sau khi bạn trả lời, mình ghi quyết định vào `confirm.md` (D/A/O), sửa spec rồi mới code.

---

## Vì sao cần: số liệu từ backtest hiện tại

`output/backtest_20261007-161821.xlsx`: tool khớp TM **43/92 đơn (47%)**. Trong 49 đơn lệch:

| Nhóm | Số đơn | Luật động nào xử lý được |
|---|---|---|
| Dev TM chọn bị loại vì cân tải (D26), tool đưa cho người khác | 12 | `Chỉ định` app → dev |
| Tool chọn người làm version gần nhất, TM lại chọn người khác (TM biết điều tool không biết: ai bận, ai cần học app) | 18 | `Không giao`, `Tối đa đơn`, `Ưu tiên` |
| Tool chọn người chưa làm app (18) hoặc chỉ làm bản cũ (1) | 19 | `Ưu tiên`, `Chỉ định` |

Ví dụ rõ nhất: **AR Dog** có 9 đơn, TM giao Linh cả 9, tool khớp 5/9. Một dòng `Chỉ định LinhNV · AR Dog` đưa
con số lên khoảng 9/9. **VPN**: TM giao Linh 6/7 đơn, tool khớp 3/7.

Lưu ý: luật rút ra từ chính lịch sử thì tất nhiên làm backtest khớp hơn. Khi đó tỉ lệ khớp đo "luật của TM + luật
của tool", không còn đo riêng luật của tool.

---

## Phương án đề xuất

**TM ghi luật vào một file `.md` trong `input/`, dưới dạng một bảng markdown có cột cố định, mỗi dòng một luật
(L1, L2 đã chốt). Tool đọc bảng, áp luật một cách xác định vào bước chọn PIC (spec §7), và ghi luật nào đã quyết
định vào cột `Lý do`.** AI vẫn chỉ ước lượng độ lớn, không đọc luật, không chọn người (`LLM.md` §12).

Ví dụ `input/luat.md`:

```markdown
# Luật giao việc

Ghi chú tự do ngoài bảng thì tool bỏ qua.

| Loại       | Dev    | App       | Số đơn | Từ ngày    | Đến ngày   | Ghi chú                 |
|------------|--------|-----------|--------|------------|------------|-------------------------|
| Chỉ định   | LinhNV | AR Dog    |        |            |            | Linh giữ AR Dog         |
| Không giao | MinhNM |           |        | 06/10/2026 | 17/10/2026 | Minh làm MVP sprint này |
| Tối đa đơn | AnTD   |           | 1      | 06/10/2026 | 17/10/2026 |                         |
| Ưu tiên    | TiếnBV | PS Remote |        |            |            | Cho Tiến học PS Remote  |
```

`Dev` là `Mã` trong `devs.xlsx`. Cột được nhận theo tên tiêu đề, không theo thứ tự (như các file khác).

Cách mỗi loại tác động lên §7 (chỉ với đơn còn trống; đơn đã giao sẵn giữ nguyên theo D10):

| Loại | Tác động | Câu trong `Lý do` (dự kiến) |
|---|---|---|
| `Chỉ định` | Dev đó là PIC của mọi đơn thuộc app, bỏ qua khoá §7. Dev nghỉ cả sprint hoặc bị `Không giao` thì luật bị bỏ qua và có cảnh báo. | `Luật TM: chỉ định LinhNV cho AR Dog (Linh giữ AR Dog)` |
| `Không giao` | Loại dev khỏi danh sách ứng viên của đơn thuộc app (App trống = mọi app). | `MinhNM không nhận đơn theo luật TM (Minh làm MVP sprint này)` |
| `Tối đa đơn` | Dev đã giữ đủ số đơn (kể cả đơn giao sẵn) thì không được chọn nữa. | `AnTD đã đủ 1 đơn theo luật TM` |
| `Ưu tiên` | Thêm một tiêu chí đứng trước "quen app" trong khoá §7: dev được ưu tiên cho app thắng. | `Luật TM: ưu tiên TiếnBV cho PS Remote (Cho Tiến học PS Remote)` |

Luật không đổi D26 (giới hạn chênh +1 đơn), không đổi D7 (chỉ dev `Nhận việc` = `Y`) và không đụng đơn đã giao sẵn
(D10).

---

## Câu hỏi

### L1. TM nhập luật bằng cách nào? (đã chốt 2026-10-07)

- [x] **Bảng có cột cố định, các loại luật cố định như bảng trên (đề xuất).** Kết quả lặp lại được, giải thích
      được, backtest được, có test cho từng loại luật.
- [ ] TM gõ câu tiếng Việt tự do; AI dịch câu thành các dòng của bảng luật, TM xem bảng dịch trong báo cáo. Làm
      được sau khi có bảng luật, vì bảng là đích dịch. Phải gửi mã dev cho AI, trái với "AI không nhận tên" (`LLM.md`
      §12), và câu dịch có thể khác nhau giữa các lần chạy.
- [ ] TM gõ câu tiếng Việt; AI đọc câu rồi tự chọn PIC. **Không đề xuất:** mất lý do kiểm được bằng mắt, mỗi lần
      chạy một kết quả, backtest không còn ý nghĩa.

Trả lời:

### L2. Bảng luật nằm ở đâu? (đã chốt 2026-10-07)

- [ ] Sheet `Luật` trong `devs.xlsx`.
- [x] **File `.md`** (user chọn): một bảng markdown như ví dụ trên.
- [ ] Cờ dòng lệnh.

Trả lời: rule là file `.md`; dạng bảng cố định (chọn trong câu hỏi trên chat).

### L2a. Tool tìm file `.md` thế nào?

- [ ] **File `.md` duy nhất trong `input/`; chỉ định rõ bằng `--rules FILE` (đề xuất).** Hiện tool chỉ xét `.xlsx`
      và `.csv` trong `input/`, nên file `.md` không lẫn với file nào. Không có file `.md` thì chạy không luật, như
      hiện nay; có từ hai file trở lên thì dừng và yêu cầu `--rules` (không đoán, như A2). File được commit cùng
      `input/` (D18).
- [ ] Chỉ dùng khi có `--rules FILE`; không tự tìm.

Trả lời:

### L3. Các loại luật cho bản đầu

Mỗi dòng chọn một ô.

| Loại | Đồng ý | Không đồng ý |
|---|---|---|
| `Chỉ định` dev cho app | [ ] | [ ] |
| `Không giao` (dev không nhận app, hoặc không nhận đơn nào) | [ ] | [ ] |
| `Tối đa đơn` cho một dev | [ ] | [ ] |
| `Ưu tiên` dev cho app (mềm, xem L5) | [ ] | [ ] |

Cần thêm loại nào khác (vd lọc theo `Ưu tiên` của đơn: "đơn urgent chỉ giao middle+")?

Trả lời:

### L4. `Chỉ định` có vượt giới hạn cân tải (D26) không?

- [ ] **Có (đề xuất).** Luật là quyết định của TM, giống đơn giao sẵn (D10). 12 đơn lệch trong backtest là do cân
      tải loại đúng dev TM chọn. Muốn giới hạn số đơn thì thêm dòng `Tối đa đơn`.
- [ ] Không. Dev chỉ định đã vượt giới hạn thì giao theo luật thường và có cảnh báo.

Trả lời:

### L5. `Ưu tiên` đứng ở đâu?

- [ ] **Tiêu chí đầu tiên của khoá §7, trước "quen app", nhưng vẫn trong giới hạn cân tải (đề xuất).** Dev được ưu
      tiên thắng nếu chưa giữ quá nhiều đơn; nếu đã quá thì giao theo luật thường và ghi lý do như cân tải hiện nay.
- [ ] Sau "quen app": chỉ phá hoà giữa những dev quen app như nhau.

Trả lời:

### L6. Một luật có hiệu lực trong bao lâu?

- [ ] **Cột `Từ ngày` / `Đến ngày`, để trống là luôn có hiệu lực (đề xuất).** Luật hết hạn tự tắt, TM không phải nhớ
      xoá. Một lần chạy dùng các luật có hiệu lực vào ngày chạy.
- [ ] Theo số sprint (cột `Sprint`, vd `10`).
- [ ] Không có thời hạn; TM tự thêm, tự xoá dòng.

Trả lời:

### L7. Backtest có áp luật không?

- [ ] **Có, theo `Từ ngày` / `Đến ngày` của từng luật so với ngày lên đơn (đề xuất).** TM thêm một luật rồi chạy
      `--backtest` để xem tỉ lệ khớp đổi thế nào trước khi dùng thật. Báo cáo backtest ghi rõ có bao nhiêu luật đã
      áp.
- [ ] Không. Backtest luôn đo riêng luật của tool.
- [ ] Có, kèm cờ `--no-rules` để chạy so sánh cả hai.

Trả lời:

### L8. Luật sai thì sao?

Đề xuất:

| Trường hợp | Xử lý |
|---|---|
| File `.md` không có bảng nào có cột `Loại` và `Dev`, hoặc thiếu cột bắt buộc | Lỗi input, dừng, báo tên file. |
| `Dev` không có trong `devs.xlsx`, `Loại` không hợp lệ, `Số đơn` không phải số nguyên dương, ngày không đọc được | Lỗi input, dừng với exit 2, báo tên file, số dòng và cột. |
| Hai luật mâu thuẫn: hai `Chỉ định` khác dev cho cùng app, hoặc `Chỉ định` và `Không giao` cùng dev cùng app | Lỗi input, dừng, báo hai dòng. Không đoán luật nào thắng. |
| Luật đúng nhưng không áp được: dev `Nhận việc` = `N` hoặc nghỉ cả sprint | Bỏ qua luật, cảnh báo WARN trong sheet `Cảnh báo`. |
| Luật không khớp đơn nào của sprint (vd sprint không có đơn AR Dog) | Không báo gì. Luật app luôn có hiệu lực thì sprint nào cũng sẽ "không khớp", báo ra chỉ gây nhiễu. |

- [ ] Đồng ý
- [ ] Không đồng ý

Trả lời:

---

## Phần việc sau khi chốt (để bạn ước lượng, không cần trả lời)

| Phần | File |
|---|---|
| Đọc bảng luật | reader mới `rules_reader.py` (file duy nhất đọc `.md`); kiểu `TeamRule` trong `model.py`; tìm file và cờ `--rules` trong `cli.py` |
| Chọn luật có hiệu lực, kiểm mâu thuẫn | module thuần mới `rules/team_rules.py` |
| Áp luật vào §7 | `rules/assign.py`; lý do trong `rules/reasons.py` |
| Backtest | `rules/backtest.py` (nếu L7 = có) |
| Tài liệu | spec §2 (cờ `--rules`), mục mới cho file luật, §7, §8, §9 (mã cảnh báo mới kèm câu tiếng Việt), §13; `confirm.md`; `LLM.md` §2, §3, §6 |
| Test | mỗi loại luật một ca quyết định PIC, mỗi mã cảnh báo một ca có và một ca không, backtest có luật |
