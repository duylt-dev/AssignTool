# case-4-luat-tm: Luật TM

Sinh bởi `eval/build_cases.py`; sửa ở đó, không sửa tay.

Chạy: `uv run scrumbot run --source file --input eval/case-4-luat-tm/input --today 2026-10-16 --history input/Tech_manager_T2-T10_2026.xlsx`

Đáp án theo spec, tính tay cho lần `--ai off` (A37). Cột `TM điền` để trống cho TM (O10).

| STT | App | Đơn | Ưu tiên | Giao sẵn | PIC theo spec | Dự phòng theo spec | Hạng nhắm tới | TM điền |
|---|---|---|---|---|---|---|---|---|
| 1 | AR Dog | 1.1.2 - Fix crash màn camera |  | ✓ |  |  | S | |
| 2 | Speak2 | 1.0.7 - Add ads/Edit UI |  | ✓ |  |  | M | |
| 3 | PS Remote | 1.1.3 - Add feature/Add ads | urgent |  | TiếnBV | LinhNV, AnTD | L | |
| 4 | AR Dog | 1.1.3 - Add New feature mini game/Add ads | high |  | LinhNV | AnTD, TiếnBV | XL | |
| 5 | AR Dog | 1.1.4 - Fix ads/Fix luồng |  |  | LinhNV | AnTD, TiếnBV | M | |
| 6 | PS Remote | 1.1.4 - Fix policy |  |  | AnTD | TiếnBV, LinhNV | S | |
| 7 | Game Emulator | 1.0.8 - Add feature cloud save |  |  | AnTD | LinhNV, TiếnBV | L | |
| 8 | Spin wheel | 1.2.0 - Fix ads/Edit UI |  |  | LinhNV | TiếnBV | M | |
| 9 | Auto click | 1.1.2 - Add tracking/Fix luồng |  |  | LinhNV | TiếnBV | M | |
| 10 | Lovetest | 1.0.8 - Fix ads/Fix luồng |  |  | MinhNM | AnTD, TiếnBV | M | |
| 11 | VPN | 1.1.8 - Fix IAP/Fix luồng |  |  | TiếnBV | LinhNV | L | |
| 12 | live video 2 | 1.0.9 - Edit UI | low |  | TiếnBV | LinhNV | S | |

Cảnh báo theo spec: `RULE-DEV-UNAVAILABLE`, `RULE-NO-CANDIDATE` (STT 10), `DUE-MISSING` (STT 3), `DUE-MISSING` (STT 4)

Cần quan sát (không chấm):

- STT 1 giao sẵn AR Dog cho TiếnBV dù luật chỉ định LinhNV: giữ nguyên (D10).
- STT 10: luật loại hết dev, A31 giao như không có luật Không giao/Tối đa đơn, nên MinhNM nhận đơn dù TM ghi 'Minh làm MVP tuần đầu'. Xem cảnh báo có đủ rõ để TM sửa không.
- Luật 'Không giao AnTD · Game Emulator' hết hạn 17/10: có hiệu lực ngày chạy 16/10 nhưng không vào ngày áp luật 19/10 (A34).
- Dòng in ra phải là 8 luật, 7 có hiệu lực ngày 19/10/2026.
