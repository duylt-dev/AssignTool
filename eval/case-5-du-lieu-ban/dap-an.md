# case-5-du-lieu-ban: Dữ liệu bẩn, app mới

Sinh bởi `eval/build_cases.py`; sửa ở đó, không sửa tay.

Chạy: `uv run assigntool --input eval/case-5-du-lieu-ban/input --today 2026-10-16 --history input/Tech_manager_T2-T10_2026.xlsx`

Đáp án theo spec, tính tay cho lần `--ai off` (A37). Cột `TM điền` để trống cho TM (O10).

| STT | App | Đơn | Ưu tiên | Giao sẵn | PIC theo spec | Dự phòng theo spec | Hạng nhắm tới | TM điền |
|---|---|---|---|---|---|---|---|---|
| 1 | Phone Cleaner | 1.0.3 - Fix ANR màn dọn rác |  | ✓ |  |  | S | |
| 3 | Auto click | 1.1.2 - Add tracking/Edit UI |  | ✓ |  |  | M | |
| 4 | live video 2 | 1.0.9 - Fix ads |  | ✓ |  |  | S | |
| 5 | QR Scanner | 1.0.0 - Init project/Add ads/Add IAP | urgent |  | MinhNM | LinhNV, TiếnBV | XL | |
| 6 | Weather Live | 1.0.0 - Init project/Add widget/Add ads | Urgent |  | LinhNV | MinhNM, TiếnBV | XL | |
| 7 | Fake GPS | 1.0.1 - Fix policy location permission | urgent |  | MinhNM | LinhNV, TiếnBV | S | |
| 8 |  | Fix crash màn splash trên Android 14 | high |  | TiếnBV | LinhNV, MinhNM | S | |
| 9 | Speaker Cleaner | 1.1.3 - Fix ads/Fix luồng |  |  | LinhNV | MinhNM, TiếnBV | M | |
| 10 | ps remote | 1.1.3 - Fix crash kết nối | gấp |  | MinhNM | LinhNV, TiếnBV | S | |
| 11 | Nhiều App | Fix policy native too small cho 6 app |  |  | AnTD | LinhNV, MinhNM | M | |
| 12 | Game Emulator | 1.0.8 - Add feature save state/Add ads |  |  | AnTD | TiếnBV, LinhNV | XL | |
| 13 | VPN | 1.1.8 - Fix IAP |  |  | TiếnBV | LinhNV, MinhNM | M | |
| 14 | VPN | Crash khi xoay màn hình |  |  |  |  |  | |

Cảnh báo theo spec: `APP-MISSING` (STT 8), `PRIORITY-UNKNOWN` (STT 10), `DUE-BEFORE-CREATED` (STT 12), `TYPE-UNKNOWN` (STT 14), `PREV-SPRINT-MISSING`

Cần quan sát (không chấm):

- STT 4 giao sẵn cho 'Bùi Văn Tiếng' (gõ sai tên TiếnBV): tool coi là người lạ, TiếnBV bị tính thiếu 1 đơn và không có cảnh báo nào (cái giá đã biết của D14).
- STT 1 tên dạng NFD có hai khoảng trắng, STT 3 viết thường: vẫn phải nhận ra LinhNV, AnTD (A10).
- STT 12 có mô tả khoảng 6.000 ký tự với 60 link: prompt phải cắt còn 600 ký tự và thay link bằng [link].
- Ba đơn urgent của app mới cùng lúc: hai middle+ nhận hai đơn, đơn thứ tư (high, không có app) rơi vào junior.
