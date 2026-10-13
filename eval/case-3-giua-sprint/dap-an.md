# case-3-giua-sprint: Giữa sprint, nghỉ phép, việc dở

Sinh bởi `eval/build_cases.py`; sửa ở đó, không sửa tay.

Chạy: `uv run scrumbot run --source file --input eval/case-3-giua-sprint/input --today 2026-10-22 --history input/Tech_manager_T2-T10_2026.xlsx`

Đáp án theo spec, tính tay cho lần `--ai off` (A37). Cột `TM điền` để trống cho TM (O10).

| STT | App | Đơn | Ưu tiên | Giao sẵn | PIC theo spec | Dự phòng theo spec | Hạng nhắm tới | TM điền |
|---|---|---|---|---|---|---|---|---|
| 1 | VPN | 1.1.8 - Fix IAP/Fix luồng |  | ✓ |  |  | L | |
| 3 | Phone Cleaner | 1.0.3 - Fix policy quyền thông báo |  | ✓ |  |  | S | |
| 4 | Speak2 | 1.0.7 - Add ads/Edit UI |  | ✓ |  |  | M | |
| 5 | Game Emulator | 1.0.7 - Add feature cloud save |  | ✓ |  |  | XL | |
| 6 | AR Dog | 1.1.2 - Fix ads |  | ✓ |  |  | S | |
| 7 | QR Scanner | 1.0.0 - Init project/Add ads/Add IAP | urgent |  | LinhNV | AnTD, TiếnBV | XL | |
| 8 | Game Emulator | 1.0.8 - Fix crash khi load ROM | high |  | AnTD | LinhNV, TiếnBV | S | |
| 9 | PS Remote | 1.1.3 - Fix crash/Fix ANR | high |  | TiếnBV | LinhNV, AnTD | M | |
| 10 | Auto click | 1.1.2 - Edit UI/Add tracking |  |  | AnTD | LinhNV, TiếnBV | M | |
| 11 | live video 2 | 1.0.9 - Fix ads/Edit luồng |  |  | TiếnBV | LinhNV, AnTD | L | |

Cảnh báo theo spec: `DEV-ON-LEAVE`, `PRE-ASSIGNED-ON-LEAVE` (STT 4), `DUE-MISSING` (STT 7), `DUE-MISSING` (STT 9)

Cần quan sát (không chấm):

- STT 4 giao sẵn cho MinhNM, người nghỉ cả sprint: đơn được giữ (D10). Lượt baseline không có cảnh báo nào; từ A43 có `PRE-ASSIGNED-ON-LEAVE`.
- PS Remote: version gần nhất thật (1.1.2, Sprint 10) chỉ có MinhNM; MinhNM ra khỏi pool nên spec §6.1 bỏ đơn đó và coi 1.1.1 (LinhNV) là version gần nhất. Lý do của STT 9 sẽ ghi LinhNV 'quen app hơn' theo 1.1.1.
- AnTD nghỉ 3 ngày vẫn nhận đơn high (STT 8): nghỉ phép chỉ phá hoà (A12).
- STT 5 có người ngoài danh sách (tên giả) cùng AnTD: tên đó bị bỏ qua (D14).
