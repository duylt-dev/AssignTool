# Bảng điểm eval 20261008-1601-off-sau-sua

Commit: `e2b519b (src/ có thay đổi chưa commit)` · AI: `gemini` × 0 lần · đáp án và cách chấm: `confirm.md` A37, A40.

| Case | Lần chạy | PIC khớp TM | PIC theo spec | Dự phòng theo spec | Giữ đơn giao sẵn | Độ lớn cùng hạng | Lệch ≤ 1 hạng | Độ lớn mặc định | Cảnh báo thiếu / thừa | Giây | Độ lớn |
|---|---|---|---|---|---|---|---|---|---|---|---|
| case-1-sprint-9 | off | 8/11 | — | — | 1/1 | — | — | — | 0 / 0 | 0.3 | tắt AI (mọi đơn M) |
| case-2-sprint-8 | off | 4/9 | — | — | 2/2 | — | — | — | 0 / 0 | 0.3 | tắt AI (mọi đơn M) |
| case-3-giua-sprint | off | — | 5/5 | 5/5 | 5/5 | — | — | — | 0 / 0 | 0.3 | tắt AI (mọi đơn M) |
| case-4-luat-tm | off | — | 10/10 | 10/10 | 2/2 | — | — | — | 0 / 0 | 0.3 | tắt AI (mọi đơn M) |
| case-5-du-lieu-ban | off | — | 9/9 | 9/9 | 3/3 | — | — | — | 0 / 0 | 0.3 | tắt AI (mọi đơn M) |

## case-1-sprint-9: Sprint 9 dựng lại

| STT | App | Đơn | Đáp án | off | Hạng thật / nhắm tới |
|---|---|---|---|---|---|
| 1 | PS Remote | 1.1.1 - Fix ads/FIx luồng/ fix policy | LinhNV, MinhNM | MinhNM [M*] | XL |
| 28 | AR Dog | 1.1.1. Add New feature/ Add ads | LinhNV | LinhNV [M*] | M |
| 49 | Game Emulator | 1.0.5 Add fearture/Add tracking/Fix bug/Fix cras | AnTD | AnTD [M*] | XL |
| 62 | Speak2 | 1.0.6 - Fix ads/Edit luồng/Fix UI | MinhNM | TiếnBV [M*] | XL |
| 91 | Game mode 2 | 1.0.1 - Add ads/Add IAP/Add | TiếnBV | TiếnBV [M*] | XL |
| 142 | AR Dog | 1.1.0. Edit Flow/Fix ads | LinhNV, AnTD | LinhNV [M*] | L |
| 160 | metal detector | 1.0.7 - Fix policy native too small | LinhNV | MinhNM [M*] | S |
| 162 | Santa prank | 1.2.4. Fix crash | LinhNV | LinhNV [M*] | S |
| 165 | Game Emulator | 1.0.3. Fix crash | AnTD | AnTD [M*] | M |
| 170 | SpeakerCleaner | 1.1.2 - Fix ads/Fix luồng/ Fix policy | LinhNV | MinhNM [M*] | M |
| 182 | Game Emulator | Nghiên cứu kỹ thuật ứng dụnng game emutaltor | AnTD | AnTD [M*] | M |
| 183 | PS Remote | Nghiên cứu và demo tính năng interactive play vi | giao sẵn | — [M*] | L |

`*` = độ lớn mặc định (AI lỗi hoặc tắt). Hạng trong ngoặc là hạng mình nhắm tới khi viết mô tả, không phải giờ thật.

Lệch ở lần `off`:

- STT 62 Speak2: tool TiếnBV, TM MinhNM
- STT 160 metal detector: tool MinhNM, TM LinhNV
- STT 170 SpeakerCleaner: tool MinhNM, TM LinhNV

## case-2-sprint-8: Sprint 8 dựng lại

| STT | App | Đơn | Đáp án | off | Hạng thật / nhắm tới |
|---|---|---|---|---|---|
| 1 | Auto click | 1.0.8. Add tracking/Edit Flow/Edit UI/Add featur | AnTD | AnTD [M*] | XL |
| 11 | Nhiều App | Fix lỗi quảng cáo native too small | LinhNV | MinhNM [M*] |  |
| 16 | number tracker | 1.1.3 - Fix ads/FIx luồng | MinhNM | AnTD [M*] | L |
| 32 | AR Dog | 1.0.7.Check và fix bug/Edit model/Fix ads/Add tr | LinhNV, AnTD | TiếnBV [M*] | L |
| 45 | spin wheel 2 | [1.0.1] - Add ads | LinhNV | LinhNV [M*] | L |
| 50 | Roblox skin | 1.0.1 - Add ads | AnTD | MinhNM [M*] | L |
| 60 | camera detector | 1.1.5 - chuyển store | LinhNV | LinhNV [M*] | S |
| 61 | AR Dog | 1.0.8. Fix crash/Tối ưu request data | LinhNV | LinhNV [M*] | S |
| 64 | Roblox skin | 1.0.3. Fix policy Device and Network Abuse | giao sẵn | — [M*] |  |
| 65 | WifiHotspot | 1.2.4- Fix policy | giao sẵn | — [M*] |  |
| 66 | Game mode | 1.1.1 - Fix policy native too small | LinhNV | MinhNM [M*] | M |

`*` = độ lớn mặc định (AI lỗi hoặc tắt). Hạng trong ngoặc là hạng mình nhắm tới khi viết mô tả, không phải giờ thật.

Lệch ở lần `off`:

- STT 11 Nhiều App: tool MinhNM, TM LinhNV
- STT 16 number tracker: tool AnTD, TM MinhNM
- STT 32 AR Dog: tool TiếnBV, TM LinhNV, AnTD
- STT 50 Roblox skin: tool MinhNM, TM AnTD
- STT 66 Game mode: tool MinhNM, TM LinhNV

## case-3-giua-sprint: Giữa sprint, nghỉ phép, việc dở

| STT | App | Đơn | Đáp án | off | Hạng thật / nhắm tới |
|---|---|---|---|---|---|
| 1 | VPN | 1.1.8 - Fix IAP/Fix luồng | giao sẵn | LinhNV [M*] | (L) |
| 3 | Phone Cleaner | 1.0.3 - Fix policy quyền thông báo | giao sẵn | TiếnBV [M*] | (S) |
| 4 | Speak2 | 1.0.7 - Add ads/Edit UI | giao sẵn | — [M*] | (M) |
| 5 | Game Emulator | 1.0.7 - Add feature cloud save | giao sẵn | AnTD [M*] | (XL) |
| 6 | AR Dog | 1.1.2 - Fix ads | giao sẵn | LinhNV [M*] | (S) |
| 7 | QR Scanner | 1.0.0 - Init project/Add ads/Add IAP | LinhNV | LinhNV [M*] | (XL) |
| 8 | Game Emulator | 1.0.8 - Fix crash khi load ROM | AnTD | AnTD [M*] | (S) |
| 9 | PS Remote | 1.1.3 - Fix crash/Fix ANR | TiếnBV | TiếnBV [M*] | (M) |
| 10 | Auto click | 1.1.2 - Edit UI/Add tracking | AnTD | AnTD [M*] | (M) |
| 11 | live video 2 | 1.0.9 - Fix ads/Edit luồng | TiếnBV | TiếnBV [M*] | (L) |

`*` = độ lớn mặc định (AI lỗi hoặc tắt). Hạng trong ngoặc là hạng mình nhắm tới khi viết mô tả, không phải giờ thật.

Cần quan sát:

- STT 4 giao sẵn cho MinhNM, người nghỉ cả sprint: đơn được giữ (D10). Lượt baseline không có cảnh báo nào; từ A43 có `PRE-ASSIGNED-ON-LEAVE`.
- PS Remote: version gần nhất thật (1.1.2, Sprint 10) chỉ có MinhNM; MinhNM ra khỏi pool nên spec §6.1 bỏ đơn đó và coi 1.1.1 (LinhNV) là version gần nhất. Lý do của STT 9 sẽ ghi LinhNV 'quen app hơn' theo 1.1.1.
- AnTD nghỉ 3 ngày vẫn nhận đơn high (STT 8): nghỉ phép chỉ phá hoà (A12).
- STT 5 có người ngoài danh sách (tên giả) cùng AnTD: tên đó bị bỏ qua (D14).

## case-4-luat-tm: Luật TM

| STT | App | Đơn | Đáp án | off | Hạng thật / nhắm tới |
|---|---|---|---|---|---|
| 1 | AR Dog | 1.1.2 - Fix crash màn camera | giao sẵn | TiếnBV [M*] | (S) |
| 2 | Speak2 | 1.0.7 - Add ads/Edit UI | giao sẵn | MinhNM [M*] | (M) |
| 3 | PS Remote | 1.1.3 - Add feature/Add ads | TiếnBV | TiếnBV [M*] | (L) |
| 4 | AR Dog | 1.1.3 - Add New feature mini game/Add ads | LinhNV | LinhNV [M*] | (XL) |
| 5 | AR Dog | 1.1.4 - Fix ads/Fix luồng | LinhNV | LinhNV [M*] | (M) |
| 6 | PS Remote | 1.1.4 - Fix policy | AnTD | AnTD [M*] | (S) |
| 7 | Game Emulator | 1.0.8 - Add feature cloud save | AnTD | AnTD [M*] | (L) |
| 8 | Spin wheel | 1.2.0 - Fix ads/Edit UI | LinhNV | LinhNV [M*] | (M) |
| 9 | Auto click | 1.1.2 - Add tracking/Fix luồng | LinhNV | LinhNV [M*] | (M) |
| 10 | Lovetest | 1.0.8 - Fix ads/Fix luồng | MinhNM | MinhNM [M*] | (M) |
| 11 | VPN | 1.1.8 - Fix IAP/Fix luồng | TiếnBV | TiếnBV [M*] | (L) |
| 12 | live video 2 | 1.0.9 - Edit UI | TiếnBV | TiếnBV [M*] | (S) |

`*` = độ lớn mặc định (AI lỗi hoặc tắt). Hạng trong ngoặc là hạng mình nhắm tới khi viết mô tả, không phải giờ thật.

Cần quan sát:

- STT 1 giao sẵn AR Dog cho TiếnBV dù luật chỉ định LinhNV: giữ nguyên (D10).
- STT 10: luật loại hết dev, A31 giao như không có luật Không giao/Tối đa đơn, nên MinhNM nhận đơn dù TM ghi 'Minh làm MVP tuần đầu'. Xem cảnh báo có đủ rõ để TM sửa không.
- Luật 'Không giao AnTD · Game Emulator' hết hạn 17/10: có hiệu lực ngày chạy 16/10 nhưng không vào ngày áp luật 19/10 (A34).
- Dòng in ra phải là 8 luật, 7 có hiệu lực ngày 19/10/2026.

## case-5-du-lieu-ban: Dữ liệu bẩn, app mới

| STT | App | Đơn | Đáp án | off | Hạng thật / nhắm tới |
|---|---|---|---|---|---|
| 1 | Phone Cleaner | 1.0.3 - Fix ANR màn dọn rác | giao sẵn | LinhNV [M*] | (S) |
| 3 | Auto click | 1.1.2 - Add tracking/Edit UI | giao sẵn | AnTD [M*] | (M) |
| 4 | live video 2 | 1.0.9 - Fix ads | giao sẵn | — [M*] | (S) |
| 5 | QR Scanner | 1.0.0 - Init project/Add ads/Add IAP | MinhNM | MinhNM [M*] | (XL) |
| 6 | Weather Live | 1.0.0 - Init project/Add widget/Add ads | LinhNV | LinhNV [M*] | (XL) |
| 7 | Fake GPS | 1.0.1 - Fix policy location permission | MinhNM | MinhNM [M*] | (S) |
| 8 |  | Fix crash màn splash trên Android 14 | TiếnBV | TiếnBV [M*] | (S) |
| 9 | Speaker Cleaner | 1.1.3 - Fix ads/Fix luồng | LinhNV | LinhNV [M*] | (M) |
| 10 | ps remote | 1.1.3 - Fix crash kết nối | MinhNM | MinhNM [M*] | (S) |
| 11 | Nhiều App | Fix policy native too small cho 6 app | AnTD | AnTD [M*] | (M) |
| 12 | Game Emulator | 1.0.8 - Add feature save state/Add ads | AnTD | AnTD [M*] | (XL) |
| 13 | VPN | 1.1.8 - Fix IAP | TiếnBV | TiếnBV [M*] | (M) |
| 14 | VPN | Crash khi xoay màn hình |  | bỏ qua |  |

`*` = độ lớn mặc định (AI lỗi hoặc tắt). Hạng trong ngoặc là hạng mình nhắm tới khi viết mô tả, không phải giờ thật.

Cần quan sát:

- STT 4 giao sẵn cho 'Bùi Văn Tiếng' (gõ sai tên TiếnBV): tool coi là người lạ, TiếnBV bị tính thiếu 1 đơn và không có cảnh báo nào (cái giá đã biết của D14).
- STT 1 tên dạng NFD có hai khoảng trắng, STT 3 viết thường: vẫn phải nhận ra LinhNV, AnTD (A10).
- STT 12 có mô tả khoảng 6.000 ký tự với 60 link: prompt phải cắt còn 600 ký tự và thay link bằng [link].
- Ba đơn urgent của app mới cùng lúc: hai middle+ nhận hai đơn, đơn thứ tư (high, không có app) rơi vào junior.
