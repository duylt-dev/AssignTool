# Bộ đánh giá `eval/`

Năm bộ input để chạy `scrumbot run --source file` (đọc file export, `confirm.md` D51), chấm output so với đáp án, rồi cải thiện tool theo kết quả. Các quyết định nằm
trong `confirm.md` A35–A42 và O10. Đây không phải test: lệch với TM là một con số trong bảng điểm, không làm `pytest`
đỏ.

## Năm case

| Case | Loại | Kiểm tra | Đáp án |
|---|---|---|---|
| `case-1-sprint-9` | Sprint 9 thật, dựng lại | Chọn PIC so với TM; độ lớn AI so với giờ thật (12 đơn, 2h đến 83h) | Dev TM đã giao, giờ thật |
| `case-2-sprint-8` | Sprint 8 thật, dựng lại | Cân tải so với TM (TM giao LinhNV 6/9 đơn) | Dev TM đã giao, giờ thật |
| `case-3-giua-sprint` | Giả lập, Sprint 11 | Chạy giữa sprint, đơn giao sẵn, dev nghỉ cả sprint, nghỉ 3 ngày, việc dở | Theo spec, tính tay |
| `case-4-luat-tm` | Giả lập, Sprint 11 | Đủ 4 loại luật TM, luật hết hạn, luật cho dev không nhận việc, luật loại hết ứng viên | Theo spec, tính tay |
| `case-5-du-lieu-ban` | Giả lập, Sprint 11 | Thiếu app, ưu tiên lạ, hạn trước ngày tạo, `Loại` lạ, tên NFD/viết thường/gõ sai, tên app viết khác, app mới | Theo spec, tính tay |

Case dựng lại: chỉ giữ đơn gốc, xoá `Người làm` của đơn có dev trong danh sách và xoá `Ước lượng (h)` (đó là đáp án);
giữ các sheet sprint cũ để AI có ví dụ giờ, nhưng sheet sprint trước có mọi trạng thái là `done` (việc dở bằng 0);
`--today` là ngày đầu sprint (A38). Case giả lập dùng app và lịch sử thật, người ngoài
danh sách mang tên giả (A39).

Mỗi case có:

- `input/`: đúng những gì tool đọc (file sprint, `devs.xlsx`, `luat.md` nếu có). Lịch sử là
  `input/Tech_manager_T2-T10_2026.xlsx` của repo, truyền bằng `--history`.
- `dap-an.md`: đáp án cho người đọc, lệnh chạy, các điểm cần quan sát. Case giả lập có cột `TM điền` để trống (O10).
- `dap-an.json`: cùng đáp án, cho `run_eval.py`.

## Chạy

```bash
uv run python eval/build_cases.py                 # sinh lại input/ và dap-an của 5 case
uv run python eval/run_eval.py                    # 1 lần --ai off + 3 lần --ai gemini mỗi case
uv run python eval/run_eval.py --cases 1,2 --ai agy --ai-timeout 540 --label thu   # agy mất ~2 phút mỗi lần
```

Kết quả nằm trong `eval/results/<YYYYMMDD-HHMM>[-label]/`: mỗi case và mỗi lần chạy một thư mục (báo cáo Excel của
tool, `terminal.txt`), cùng `scores.json` và `bang-diem.md`.

## Đọc bảng điểm

| Cột | Ý nghĩa |
|---|---|
| PIC khớp TM | Case dựng lại: PIC của tool là một trong các dev TM đã giao. |
| PIC / Dự phòng theo spec | Case giả lập, lần `off`: đúng như đáp án tính tay. Lệch ở đây là lỗi code hoặc lỗi đáp án, phải xem ngay. |
| Giữ đơn giao sẵn | Đơn đã có người vẫn ghi `Đã giao sẵn` (D10). |
| Độ lớn cùng hạng / lệch ≤ 1 hạng | Lần chạy AI, case dựng lại: so với giờ thật đổi ra hạng (≤ 8h S, ≤ 24h M, ≤ 48h L, > 48h XL; A40). |
| Độ lớn mặc định | Số đơn AI không trả độ lớn, tính là M. |
| Cảnh báo thiếu / thừa | Lần `off`: so với các mã cảnh báo theo spec. |

Lần chạy AI có thể chọn PIC khác lần `off`, vì độ lớn đổi tiêu chí giờ (spec §7 phần 3). Vì vậy đáp án theo spec chỉ
chấm lần `off`. Phần "Dao động" đếm số đơn đổi độ lớn hoặc đổi PIC giữa các lần chạy AI (D27).

## Thêm hoặc sửa case

Sửa `scenarios.py` (case giả lập: dòng của file sprint, ngày nghỉ, luật, đáp án theo spec kèm chú thích bước quyết
định) hoặc `build_cases.py` (case dựng lại từ một sheet của `input/`), chạy lại `build_cases.py`, rồi commit cả input
sinh ra. Đáp án theo spec phải tính tay trước khi chạy tool, không chép từ output.
