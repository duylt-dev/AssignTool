# Assigntool – Cách lấy dữ liệu, chọn Dev và kết quả

**Ngày:** 08/10/2026
**Gửi:** MD + TM

## 1. Mục đích

Tài liệu này dùng để thống nhất 3 vấn đề của Assigntool:

1. Tool cần những dữ liệu gì để phân công.
2. Tool dựa vào đâu để chọn Dev cho từng đơn.
3. Sau khi chọn xong, tool trả về những thông tin gì.

Mỗi phần được mô tả ở 2 giai đoạn:

* **Bản demo hiện tại:** Tool đọc dữ liệu từ các file Excel.
* **Khi tích hợp vào hệ thống:** Tool đọc và cập nhật dữ liệu trực tiếp trong hệ thống nội bộ.

> **Đơn** = Task gốc do BA tạo trên board Maintain, tương ứng với một version của app.
> Ví dụ: `Phone Cleaner 1.0.2 - Add ads/Add SDK`
>
> **PIC** = Dev chịu trách nhiệm chính cho cả đơn. PIC sẽ tự chia nhỏ thành các subtask nếu cần.

---

# 2. Tóm tắt cách Assigntool hoạt động

Có thể hiểu đơn giản như sau:

**Dữ liệu đơn → kiểm tra Dev có thể nhận việc → xem ai quen app → cân tải → chọn PIC → đưa ra lý do**

### Bản demo hiện tại

Tool đọc:

* Danh sách đơn của sprint.
* Lịch sử Dev đã từng làm app nào.
* Danh sách Dev được phép nhận việc.
* Các luật riêng của Tech Manager nếu có.

Sau đó tool:

1. Xác định những đơn chưa có người làm.
2. Ước lượng độ lớn của từng đơn bằng AI.
3. Tìm các Dev có thể nhận đơn.
4. Chọn PIC theo một bộ luật cố định.
5. Đưa ra lý do tại sao chọn người đó.
6. Xuất kết quả thành file Excel.

### Khi tích hợp vào hệ thống

Luật chọn Dev **không thay đổi**.

Chỉ thay đổi cách lấy dữ liệu:

**Hiện tại:**

`Excel → Assigntool → Excel`

**Sau khi tích hợp:**

`Hệ thống → Assigntool → Hệ thống`

Khi đó tool có thể tự ghi PIC vào đơn thông qua API.

---

# 3. Tool cần những dữ liệu gì?

## 3.1. Bản demo

Hiện tại tool cần 4 loại dữ liệu:

| Dữ liệu              | Nguồn                    | Mục đích                                    |
| -------------------- | ------------------------ | ------------------------------------------- |
| Đơn của sprint       | Excel export từ hệ thống | Biết những đơn nào cần giao                 |
| Lịch sử Tech Manager | Excel/CSV                | Biết Dev nào từng làm app nào               |
| Danh sách Dev        | `devs.xlsx`              | Biết ai được phép nhận việc                 |
| Luật của TM          | File `.md`               | Cho phép TM chỉ định hoặc hạn chế việc giao |

### Thông tin của đơn cần dùng

Tool cần:

* Task
* Loại
* App Name
* Người làm
* Ưu tiên
* Hạn
* Ngày tạo
* Mô tả

`Ước lượng (h)` của đơn mới **không được sử dụng**, vì tại thời điểm phân công đơn chưa có estimate.

Thay vào đó, tool sẽ dùng AI để ước lượng độ lớn.

---

## 3.2. Khi tích hợp vào hệ thống

Khi tích hợp, không cần export Excel nữa.

Tool sẽ đọc trực tiếp:

* Đơn đang cần giao.
* Việc còn dở của sprint trước.
* Lịch sử các đơn đã làm.
* Giờ thực tế của các đơn cũ.
* Danh sách Dev.
* Luật phân công của TM.

Điểm quan trọng là:

> **Luật chọn Dev giữ nguyên. Chỉ thay đổi nguồn dữ liệu từ Excel sang hệ thống.**

---

# 4. Tool chọn Dev như thế nào?

Tool hiện chỉ phân công cho 4 Dev Android:

| Dev    | Level   |
| ------ | ------- |
| LinhNV | Middle+ |
| MinhNM | Middle  |
| AnTD   | Junior+ |
| TiếnBV | Junior  |

QA và TM không nằm trong danh sách có thể được đề xuất.

## 4.1. Những đơn nào được giao?

Tool chỉ tự giao:

* Task gốc.
* Board Maintain.
* Chưa có người làm.

Tool **không tự giao**:

* Subtask.
* Bug.
* Task của MVP / Research.
* Task đã có người làm.

Nếu một đơn đã có người làm thì **giữ nguyên**, tool chỉ tính đơn đó vào tải của Dev.

---

# 5. AI dùng để làm gì?

AI **không chọn Dev**.

AI chỉ trả lời một câu hỏi:

> “Đơn này có độ lớn khoảng bao nhiêu?”

Tool quy đổi thành 4 mức:

| Mức | Giờ | Hiểu đơn giản            |
| --- | --: | ------------------------ |
| S   |  4h | Việc nhỏ, khoảng vài giờ |
| M   | 16h | Việc khoảng 2–3 ngày     |
| L   | 32h | Việc khoảng 1 tuần       |
| XL  | 64h | Việc lớn, hơn 1 tuần     |

Ví dụ:

* Sửa text/config → S
* Một tính năng nhỏ → M
* Ads/IAP kèm thay đổi flow hoặc UI → L
* Tính năng lớn hoặc tích hợp SDK mới → XL

Nếu AI lỗi hoặc timeout:

> Tool mặc định đơn đó là **M = 16h** và ghi cảnh báo.

Điều quan trọng:

> **AI chỉ ước lượng độ lớn. AI không được quyết định Dev nào nhận đơn.**

---

# 6. Tool chọn PIC theo nguyên tắc nào?

Mỗi đơn sẽ được xử lý lần lượt theo thứ tự ưu tiên.

## Bước 1 – Loại những người không thể nhận

Ví dụ:

* Dev đang bị luật `Không giao`.
* Dev đã đạt giới hạn `Tối đa đơn`.
* Dev không nhận việc.
* Dev nghỉ toàn bộ sprint.

Những người này không được chọn.

---

## Bước 2 – Kiểm tra luật của TM

Nếu TM đã chỉ định:

> App `AR Dog` → LinhNV

và LinhNV vẫn có thể nhận việc thì:

**→ Giao luôn cho LinhNV.**

Không cần xét các bước tiếp theo.

---

## Bước 3 – Cân số lượng đơn

Tool không để một Dev nhận quá nhiều đơn so với người khác.

Nguyên tắc:

> Một Dev chỉ được xét nếu số đơn đang giữ ≤ số đơn ít nhất + 1.

Ví dụ:

| Dev    | Đang có |
| ------ | ------: |
| LinhNV |       3 |
| MinhNM |       3 |
| AnTD   |       2 |
| TiếnBV |       2 |

Số ít nhất là **2**.

Vì vậy ở đơn tiếp theo, chỉ những người có tối đa:

**2 + 1 = 3 đơn**

được xét.

Mục đích là tránh trường hợp một Dev quá quen app nên nhận gần như toàn bộ đơn.

---

# 7. Nếu có nhiều Dev cùng đủ điều kiện thì chọn ai?

Sau khi lọc, tool so từng Dev theo thứ tự:

### 1. Luật ưu tiên của TM

Nếu TM nói:

> App PS Remote ưu tiên TiếnBV

thì TiếnBV được ưu tiên.

---

### 2. Ai quen app hơn?

Ưu tiên:

**Đã làm version gần nhất → đã từng làm app → chưa từng làm**

Ví dụ:

* LinhNV từng làm `Phone Cleaner 1.0.1`
* MinhNM từng làm `Phone Cleaner 1.0.0`
* AnTD chưa từng làm

→ LinhNV được ưu tiên.

---

### 3. Đơn có cần Dev vững hơn không?

Nếu:

* Đơn `urgent` / `high`, hoặc
* App chưa có Dev nào trong team từng làm

thì ưu tiên Dev **Middle trở lên**.

---

### 4. Ai đang ít tải giờ hơn?

So tổng số giờ của các đơn đang giữ.

Ví dụ:

* LinhNV: 32h
* MinhNM: 16h

→ MinhNM được ưu tiên.

---

### 5. Ai còn ít việc dở hơn từ sprint trước?

Dev nào có ít việc chưa hoàn thành hơn được ưu tiên.

---

### 6. Ai nghỉ ít ngày hơn trong sprint?

Nếu các tiêu chí trên vẫn bằng nhau thì ưu tiên Dev nghỉ ít ngày hơn.

---

### 7. Level cao hơn

Nếu vẫn bằng nhau:

**Middle+ → Middle → Junior+ → Junior**

---

### 8. Mã Dev

Nếu tất cả vẫn bằng nhau, dùng mã Dev theo alphabet để đảm bảo:

> Cùng dữ liệu → luôn ra cùng một kết quả.

---

# 8. Tại sao không để AI tự chọn Dev?

Assigntool cố tình **không dùng AI để quyết định người nhận việc**.

Lý do:

Mỗi quyết định của tool đều phải giải thích được bằng một luật cụ thể.

Ví dụ:

> `Làm version gần nhất của Roblox Skin (Sprint 8) · Tải sprint này: 32h (2 đơn) · Việc dở Sprint 9: 0`

TM có thể nhìn vào và hiểu ngay:

* Dev này từng làm app.
* Hiện đang có bao nhiêu tải.
* Có bao nhiêu việc dở.

Vì vậy:

> **AI dùng để ước lượng độ lớn, còn luật cố định quyết định PIC.**

Điều này giúp kết quả dễ kiểm tra và không phụ thuộc vào việc AI “suy nghĩ” thế nào.

---

# 9. Luật riêng của Tech Manager

TM có thể điều chỉnh cách giao mà **không cần sửa code**.

Có 4 loại luật:

| Luật       | Ý nghĩa                   | Ví dụ                 |
| ---------- | ------------------------- | --------------------- |
| Chỉ định   | Luôn giao app cho một Dev | AR Dog → LinhNV       |
| Không giao | Dev không nhận app này    | MinhNM không nhận MVP |
| Tối đa đơn | Giới hạn số đơn           | AnTD tối đa 1 đơn     |
| Ưu tiên    | Ưu tiên Dev cho app       | PS Remote → TiếnBV    |

Luật có thể có thời gian áp dụng:

* Từ ngày
* Đến ngày

Nếu luật bị sai hoặc mâu thuẫn, tool **không tự đoán** mà dừng và báo lỗi để TM sửa.

---

# 10. Kết quả tool trả ra là gì?

## Bản demo

Tool tạo một file Excel gồm 3 sheet:

### Phân công

Mỗi đơn có:

* Độ lớn
* Giờ ước tính
* Lý do độ lớn
* PIC
* Mã PIC
* Đơn đã giao sẵn hay do tool đề xuất
* Lý do chọn PIC
* Dự phòng 1
* Dự phòng 2

### Cảnh báo

Hiển thị các vấn đề như:

* Thiếu App Name.
* Ưu tiên không hợp lệ.
* AI lỗi.
* Dev nghỉ cả sprint.
* Đơn giao cho Dev đang nghỉ cả sprint.
* Luật TM không áp dụng được.

Nếu không có lỗi:

> `Không có cảnh báo`

### Tải Dev

Cho biết:

* Việc dở sprint trước.
* Ngày nghỉ.
* Số đơn có sẵn.
* Số đơn tool giao.
* Tổng số đơn.
* Tổng giờ.
* Các đơn đang giữ.
* Các app đã từng làm.

---

# 11. Khi tích hợp vào hệ thống thì sao?

Mục tiêu cuối cùng là:

> **Tool tự ghi PIC vào trường `Người làm` của đơn thông qua API. Không cần TM duyệt lại.**

Tool **không ghi đè** những đơn đã có người làm.

Ví dụ:

```text
BA tạo đơn
   ↓
Assigntool chạy
   ↓
Kiểm tra Dev có thể nhận
   ↓
Chọn PIC
   ↓
Ghi PIC vào "Người làm"
```

Tuy nhiên, hiện còn một vấn đề:

Ngoài PIC, tool còn tạo ra:

* Độ lớn
* Lý do
* 2 Dev dự phòng
* Cảnh báo
* Thông tin tải

Hệ thống hiện chưa có chỗ để hiển thị các thông tin này.

---

# 12. Những điểm cần PO quyết định

Hiện tại có 7 vấn đề cần PO xác nhận:

| # | Cần xác nhận                                                     | Mục đích                             |
| - | ---------------------------------------------------------------- | ------------------------------------ |
| 1 | Tool lấy dữ liệu qua API hay đọc trực tiếp CSDL?                 | Xác định cách tích hợp               |
| 2 | Level, trạng thái nhận việc và ngày nghỉ của Dev đang nằm ở đâu? | Xác định nguồn dữ liệu Dev           |
| 3 | Luật của TM giữ bằng file hay làm màn hình cấu hình?             | Xác định nơi quản lý luật            |
| 4 | Lý do, độ lớn, dự phòng và cảnh báo hiển thị ở đâu?              | Để TM kiểm tra kết quả               |
| 5 | Tool chạy khi TM bấm hay tự chạy khi BA tạo đơn?                 | Xác định cách trigger                |
| 6 | Hệ thống có sẵn board, ngày sprint và giờ thực tế không?         | Loại bỏ các phần tool đang phải đoán |
| 7 | Khi chạy server sẽ dùng AI nào và API key nào?                   | Xác định cách chạy AI                |

---

# 13. Một số kết quả đã kiểm tra

Tool đã được chạy thử trên dữ liệu thực tế.

### Độ chính xác của AI

Chạy trên 2 sprint thật, mỗi sprint 3 lần:

* **57%** đơn được xếp đúng hạng.
* **95%** đơn lệch không quá 1 hạng.

AI chỉ ảnh hưởng đến **số giờ tải**, không quyết định Dev có được nhận đơn hay không.

### So sánh với cách TM đã giao

Tool đã chạy lại:

* 92 đơn
* 16 sprint Maintain
* Từ cuối tháng 1 đến tháng 10/2026

Kết quả:

* Khớp **43/92 đơn = 47%**
* Riêng Sprint 1–10: **55%**
* Sprint 9: **8/11 đơn**

Phần lệch chủ yếu đến từ nguyên tắc cân tải.

Ví dụ Sprint 8:

> TM giao 6/9 đơn cho LinhNV.

Trong khi tool giới hạn số đơn để tránh một Dev nhận quá nhiều việc.

Vì vậy:

> **Khác với cách TM đã giao trước đây không đồng nghĩa tool sai.**
> Tool đang áp dụng thêm nguyên tắc cân tải đã thống nhất.

---

# 14. Điều kiện cần để bắt đầu tích hợp

Để chuyển từ bản demo sang hệ thống thật, hiện cần:

1. **API đọc dữ liệu đơn và lịch sử.**
2. **API ghi `Người làm`.**
3. **Tài liệu API.**
4. **Token / tài khoản để tool gọi API.**
5. Xác định nguồn dữ liệu:

   * Level Dev
   * Trạng thái nhận việc
   * Ngày nghỉ
6. Xác định nơi lưu **luật của TM**.
7. Xác định nơi hiển thị:

   * Lý do
   * Độ lớn
   * Dự phòng
   * Cảnh báo
   * Tải Dev

Chi tiết kỹ thuật được ghi tại:

* `docs/assignment-spec.md`
* `confirm.md`
