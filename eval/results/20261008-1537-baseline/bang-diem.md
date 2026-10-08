# Bảng điểm eval 20261008-1537-baseline

Commit: `3057c78 (src/ có thay đổi chưa commit)` · AI: `gemini` × 3 lần · đáp án và cách chấm: `confirm.md` A37, A40.

| Case | Lần chạy | PIC khớp TM | PIC theo spec | Dự phòng theo spec | Giữ đơn giao sẵn | Độ lớn cùng hạng | Lệch ≤ 1 hạng | Độ lớn mặc định | Cảnh báo thiếu / thừa | Giây | Độ lớn |
|---|---|---|---|---|---|---|---|---|---|---|---|
| case-1-sprint-9 | off | 8/11 | — | — | 1/1 | — | — | — | 0 / 0 | 0.3 | tắt AI (mọi đơn M) |
| case-1-sprint-9 | gemini-1 | 8/11 | — | — | 1/1 | 3/12 | 8/12 | 0 | — | 17.6 | AI (gemini, 12/12 đơn) |
| case-1-sprint-9 | gemini-2 | 8/11 | — | — | 1/1 | 3/12 | 8/12 | 0 | — | 20.1 | AI (gemini, 12/12 đơn) |
| case-1-sprint-9 | gemini-3 | 8/11 | — | — | 1/1 | 3/12 | 7/12 | 0 | — | 40.1 | AI (gemini, 12/12 đơn) |
| case-2-sprint-8 | off | 4/9 | — | — | 2/2 | — | — | — | 0 / 0 | 0.3 | tắt AI (mọi đơn M) |
| case-2-sprint-8 | gemini-1 | 4/9 | — | — | 2/2 | 5/8 | 6/8 | 0 | — | 48.2 | AI (gemini, 11/11 đơn) |
| case-2-sprint-8 | gemini-2 | 4/9 | — | — | 2/2 | 4/8 | 5/8 | 0 | — | 51.9 | AI (gemini, 11/11 đơn) |
| case-2-sprint-8 | gemini-3 | 4/9 | — | — | 2/2 | 4/8 | 4/8 | 0 | — | 18.1 | AI (gemini, 11/11 đơn) |
| case-3-giua-sprint | off | — | 5/5 | 5/5 | 5/5 | — | — | — | 0 / 0 | 0.3 | tắt AI (mọi đơn M) |
| case-3-giua-sprint | gemini-1 | — | — | — | 5/5 | — | — | 0 | — | 18.5 | AI (gemini, 10/10 đơn) |
| case-3-giua-sprint | gemini-2 | — | — | — | 5/5 | — | — | 0 | — | 24.5 | AI (gemini, 10/10 đơn) |
| case-3-giua-sprint | gemini-3 | — | — | — | 5/5 | — | — | 0 | — | 15.6 | AI (gemini, 10/10 đơn) |
| case-4-luat-tm | off | — | 10/10 | 10/10 | 2/2 | — | — | — | 0 / 0 | 0.3 | tắt AI (mọi đơn M) |
| case-4-luat-tm | gemini-1 | — | — | — | 2/2 | — | — | 0 | — | 15.7 | AI (gemini, 12/12 đơn) |
| case-4-luat-tm | gemini-2 | — | — | — | 2/2 | — | — | 0 | — | 28.6 | AI (gemini, 12/12 đơn) |
| case-4-luat-tm | gemini-3 | — | — | — | 2/2 | — | — | 0 | — | 28.8 | AI (gemini, 12/12 đơn) |
| case-5-du-lieu-ban | off | — | 9/9 | 9/9 | 3/3 | — | — | — | 0 / 0 | 0.4 | tắt AI (mọi đơn M) |
| case-5-du-lieu-ban | gemini-1 | — | — | — | 3/3 | — | — | 0 | — | 18.3 | AI (gemini, 12/12 đơn) |
| case-5-du-lieu-ban | gemini-2 | — | — | — | 3/3 | — | — | 0 | — | 14.4 | AI (gemini, 12/12 đơn) |
| case-5-du-lieu-ban | gemini-3 | — | — | — | 3/3 | — | — | 0 | — | 16.5 | AI (gemini, 12/12 đơn) |

## case-1-sprint-9: Sprint 9 dựng lại

| STT | App | Đơn | Đáp án | off | gemini-1 | gemini-2 | gemini-3 | Hạng thật / nhắm tới |
|---|---|---|---|---|---|---|---|---|
| 1 | PS Remote | 1.1.1 - Fix ads/FIx luồng/ fix policy | LinhNV, MinhNM | MinhNM [M*] | MinhNM [S] | MinhNM [S] | MinhNM [S] | XL |
| 28 | AR Dog | 1.1.1. Add New feature/ Add ads | LinhNV | LinhNV [M*] | LinhNV [XL] | LinhNV [XL] | LinhNV [XL] | M |
| 49 | Game Emulator | 1.0.5 Add fearture/Add tracking/Fix bug/Fix cras | AnTD | AnTD [M*] | AnTD [L] | AnTD [L] | AnTD [M] | XL |
| 62 | Speak2 | 1.0.6 - Fix ads/Edit luồng/Fix UI | MinhNM | TiếnBV [M*] | TiếnBV [S] | TiếnBV [M] | TiếnBV [S] | XL |
| 91 | Game mode 2 | 1.0.1 - Add ads/Add IAP/Add | TiếnBV | TiếnBV [M*] | TiếnBV [M] | TiếnBV [M] | TiếnBV [M] | XL |
| 142 | AR Dog | 1.1.0. Edit Flow/Fix ads | LinhNV, AnTD | LinhNV [M*] | LinhNV [M] | LinhNV [M] | LinhNV [M] | L |
| 160 | metal detector | 1.0.7 - Fix policy native too small | LinhNV | MinhNM [M*] | MinhNM [S] | MinhNM [S] | MinhNM [S] | S |
| 162 | Santa prank | 1.2.4. Fix crash | LinhNV | LinhNV [M*] | LinhNV [S] | LinhNV [S] | LinhNV [S] | S |
| 165 | Game Emulator | 1.0.3. Fix crash | AnTD | AnTD [M*] | AnTD [S] | AnTD [S] | AnTD [S] | M |
| 170 | SpeakerCleaner | 1.1.2 - Fix ads/Fix luồng/ Fix policy | LinhNV | MinhNM [M*] | MinhNM [S] | MinhNM [S] | MinhNM [S] | M |
| 182 | Game Emulator | Nghiên cứu kỹ thuật ứng dụnng game emutaltor | AnTD | AnTD [M*] | AnTD [M] | AnTD [M] | AnTD [M] | M |
| 183 | PS Remote | Nghiên cứu và demo tính năng interactive play vi | giao sẵn | — [M*] | — [XL] | — [XL] | — [XL] | L |

`*` = độ lớn mặc định (AI lỗi hoặc tắt). Hạng trong ngoặc là hạng mình nhắm tới khi viết mô tả, không phải giờ thật.

Dao động giữa 3 lần chạy AI: 2 đơn đổi độ lớn, 0 đơn đổi PIC.

Lệch ở lần `off`:

- STT 62 Speak2: tool TiếnBV, TM MinhNM
- STT 160 metal detector: tool MinhNM, TM LinhNV
- STT 170 SpeakerCleaner: tool MinhNM, TM LinhNV

Lệch ở lần `gemini-1`:

- STT 62 Speak2: tool TiếnBV, TM MinhNM
- STT 160 metal detector: tool MinhNM, TM LinhNV
- STT 170 SpeakerCleaner: tool MinhNM, TM LinhNV

Lệch ở lần `gemini-2`:

- STT 62 Speak2: tool TiếnBV, TM MinhNM
- STT 160 metal detector: tool MinhNM, TM LinhNV
- STT 170 SpeakerCleaner: tool MinhNM, TM LinhNV

Lệch ở lần `gemini-3`:

- STT 62 Speak2: tool TiếnBV, TM MinhNM
- STT 160 metal detector: tool MinhNM, TM LinhNV
- STT 170 SpeakerCleaner: tool MinhNM, TM LinhNV

## case-2-sprint-8: Sprint 8 dựng lại

| STT | App | Đơn | Đáp án | off | gemini-1 | gemini-2 | gemini-3 | Hạng thật / nhắm tới |
|---|---|---|---|---|---|---|---|---|
| 1 | Auto click | 1.0.8. Add tracking/Edit Flow/Edit UI/Add featur | AnTD | AnTD [M*] | AnTD [XL] | AnTD [S] | AnTD [S] | XL |
| 11 | Nhiều App | Fix lỗi quảng cáo native too small | LinhNV | MinhNM [M*] | MinhNM [M] | MinhNM [M] | MinhNM [M] |  |
| 16 | number tracker | 1.1.3 - Fix ads/FIx luồng | MinhNM | AnTD [M*] | TiếnBV [S] | AnTD [S] | AnTD [S] | L |
| 32 | AR Dog | 1.0.7.Check và fix bug/Edit model/Fix ads/Add tr | LinhNV, AnTD | TiếnBV [M*] | TiếnBV [M] | TiếnBV [M] | TiếnBV [S] | L |
| 45 | spin wheel 2 | [1.0.1] - Add ads | LinhNV | LinhNV [M*] | LinhNV [L] | LinhNV [L] | LinhNV [L] | L |
| 50 | Roblox skin | 1.0.1 - Add ads | AnTD | MinhNM [M*] | MinhNM [S] | MinhNM [S] | MinhNM [S] | L |
| 60 | camera detector | 1.1.5 - chuyển store | LinhNV | LinhNV [M*] | LinhNV [S] | LinhNV [S] | LinhNV [S] | S |
| 61 | AR Dog | 1.0.8. Fix crash/Tối ưu request data | LinhNV | LinhNV [M*] | LinhNV [S] | LinhNV [S] | LinhNV [S] | S |
| 64 | Roblox skin | 1.0.3. Fix policy Device and Network Abuse | giao sẵn | — [M*] | — [M] | — [S] | — [S] |  |
| 65 | WifiHotspot | 1.2.4- Fix policy | giao sẵn | — [M*] | — [S] | — [S] | — [S] |  |
| 66 | Game mode | 1.1.1 - Fix policy native too small | LinhNV | MinhNM [M*] | MinhNM [M] | MinhNM [M] | MinhNM [M] | M |

`*` = độ lớn mặc định (AI lỗi hoặc tắt). Hạng trong ngoặc là hạng mình nhắm tới khi viết mô tả, không phải giờ thật.

Dao động giữa 3 lần chạy AI: 3 đơn đổi độ lớn, 1 đơn đổi PIC.

Lệch ở lần `off`:

- STT 11 Nhiều App: tool MinhNM, TM LinhNV
- STT 16 number tracker: tool AnTD, TM MinhNM
- STT 32 AR Dog: tool TiếnBV, TM LinhNV, AnTD
- STT 50 Roblox skin: tool MinhNM, TM AnTD
- STT 66 Game mode: tool MinhNM, TM LinhNV

Lệch ở lần `gemini-1`:

- STT 11 Nhiều App: tool MinhNM, TM LinhNV
- STT 16 number tracker: tool TiếnBV, TM MinhNM
- STT 32 AR Dog: tool TiếnBV, TM LinhNV, AnTD
- STT 50 Roblox skin: tool MinhNM, TM AnTD
- STT 66 Game mode: tool MinhNM, TM LinhNV

Lệch ở lần `gemini-2`:

- STT 11 Nhiều App: tool MinhNM, TM LinhNV
- STT 16 number tracker: tool AnTD, TM MinhNM
- STT 32 AR Dog: tool TiếnBV, TM LinhNV, AnTD
- STT 50 Roblox skin: tool MinhNM, TM AnTD
- STT 66 Game mode: tool MinhNM, TM LinhNV

Lệch ở lần `gemini-3`:

- STT 11 Nhiều App: tool MinhNM, TM LinhNV
- STT 16 number tracker: tool AnTD, TM MinhNM
- STT 32 AR Dog: tool TiếnBV, TM LinhNV, AnTD
- STT 50 Roblox skin: tool MinhNM, TM AnTD
- STT 66 Game mode: tool MinhNM, TM LinhNV

## case-3-giua-sprint: Giữa sprint, nghỉ phép, việc dở

| STT | App | Đơn | Đáp án | off | gemini-1 | gemini-2 | gemini-3 | Hạng thật / nhắm tới |
|---|---|---|---|---|---|---|---|---|
| 1 | VPN | 1.1.8 - Fix IAP/Fix luồng | giao sẵn | LinhNV [M*] | LinhNV [M] | LinhNV [M] | LinhNV [L] | (L) |
| 3 | Phone Cleaner | 1.0.3 - Fix policy quyền thông báo | giao sẵn | TiếnBV [M*] | TiếnBV [S] | TiếnBV [S] | TiếnBV [S] | (S) |
| 4 | Speak2 | 1.0.7 - Add ads/Edit UI | giao sẵn | — [M*] | — [M] | — [M] | — [M] | (M) |
| 5 | Game Emulator | 1.0.7 - Add feature cloud save | giao sẵn | AnTD [M*] | AnTD [XL] | AnTD [XL] | AnTD [XL] | (XL) |
| 6 | AR Dog | 1.1.2 - Fix ads | giao sẵn | LinhNV [M*] | LinhNV [S] | LinhNV [S] | LinhNV [S] | (S) |
| 7 | QR Scanner | 1.0.0 - Init project/Add ads/Add IAP | LinhNV | LinhNV [M*] | LinhNV [XL] | LinhNV [XL] | LinhNV [XL] | (XL) |
| 8 | Game Emulator | 1.0.8 - Fix crash khi load ROM | AnTD | AnTD [M*] | AnTD [S] | AnTD [S] | AnTD [S] | (S) |
| 9 | PS Remote | 1.1.3 - Fix crash/Fix ANR | TiếnBV | TiếnBV [M*] | TiếnBV [M] | TiếnBV [M] | TiếnBV [M] | (M) |
| 10 | Auto click | 1.1.2 - Edit UI/Add tracking | AnTD | AnTD [M*] | AnTD [M] | AnTD [M] | AnTD [M] | (M) |
| 11 | live video 2 | 1.0.9 - Fix ads/Edit luồng | TiếnBV | TiếnBV [M*] | TiếnBV [L] | TiếnBV [M] | TiếnBV [L] | (L) |

`*` = độ lớn mặc định (AI lỗi hoặc tắt). Hạng trong ngoặc là hạng mình nhắm tới khi viết mô tả, không phải giờ thật.

Dao động giữa 3 lần chạy AI: 2 đơn đổi độ lớn, 0 đơn đổi PIC.

Cần quan sát:

- STT 4 giao sẵn cho MinhNM, người nghỉ cả sprint: spec giữ đơn (D10) và không cảnh báo gì.
- PS Remote: version gần nhất thật (1.1.2, Sprint 10) chỉ có MinhNM; MinhNM ra khỏi pool nên spec §6.1 bỏ đơn đó và coi 1.1.1 (LinhNV) là version gần nhất. Lý do của STT 9 sẽ ghi LinhNV 'quen app hơn' theo 1.1.1.
- AnTD nghỉ 3 ngày vẫn nhận đơn high (STT 8): nghỉ phép chỉ phá hoà (A12).
- STT 5 có người ngoài danh sách (tên giả) cùng AnTD: tên đó bị bỏ qua (D14).

## case-4-luat-tm: Luật TM

| STT | App | Đơn | Đáp án | off | gemini-1 | gemini-2 | gemini-3 | Hạng thật / nhắm tới |
|---|---|---|---|---|---|---|---|---|
| 1 | AR Dog | 1.1.2 - Fix crash màn camera | giao sẵn | TiếnBV [M*] | TiếnBV [S] | TiếnBV [S] | TiếnBV [S] | (S) |
| 2 | Speak2 | 1.0.7 - Add ads/Edit UI | giao sẵn | MinhNM [M*] | MinhNM [M] | MinhNM [M] | MinhNM [M] | (M) |
| 3 | PS Remote | 1.1.3 - Add feature/Add ads | TiếnBV | TiếnBV [M*] | TiếnBV [L] | TiếnBV [L] | TiếnBV [L] | (L) |
| 4 | AR Dog | 1.1.3 - Add New feature mini game/Add ads | LinhNV | LinhNV [M*] | LinhNV [XL] | LinhNV [XL] | LinhNV [XL] | (XL) |
| 5 | AR Dog | 1.1.4 - Fix ads/Fix luồng | LinhNV | LinhNV [M*] | LinhNV [S] | LinhNV [S] | LinhNV [S] | (M) |
| 6 | PS Remote | 1.1.4 - Fix policy | AnTD | AnTD [M*] | AnTD [S] | AnTD [S] | AnTD [S] | (S) |
| 7 | Game Emulator | 1.0.8 - Add feature cloud save | AnTD | AnTD [M*] | AnTD [L] | AnTD [L] | AnTD [XL] | (L) |
| 8 | Spin wheel | 1.2.0 - Fix ads/Edit UI | LinhNV | LinhNV [M*] | LinhNV [M] | LinhNV [M] | LinhNV [M] | (M) |
| 9 | Auto click | 1.1.2 - Add tracking/Fix luồng | LinhNV | LinhNV [M*] | LinhNV [M] | LinhNV [M] | LinhNV [M] | (M) |
| 10 | Lovetest | 1.0.8 - Fix ads/Fix luồng | MinhNM | MinhNM [M*] | MinhNM [S] | MinhNM [S] | MinhNM [S] | (M) |
| 11 | VPN | 1.1.8 - Fix IAP/Fix luồng | TiếnBV | TiếnBV [M*] | TiếnBV [M] | TiếnBV [M] | TiếnBV [L] | (L) |
| 12 | live video 2 | 1.0.9 - Edit UI | TiếnBV | TiếnBV [M*] | TiếnBV [S] | TiếnBV [S] | TiếnBV [M] | (S) |

`*` = độ lớn mặc định (AI lỗi hoặc tắt). Hạng trong ngoặc là hạng mình nhắm tới khi viết mô tả, không phải giờ thật.

Dao động giữa 3 lần chạy AI: 3 đơn đổi độ lớn, 0 đơn đổi PIC.

Cần quan sát:

- STT 1 giao sẵn AR Dog cho TiếnBV dù luật chỉ định LinhNV: giữ nguyên (D10).
- STT 10: luật loại hết dev, A31 giao như không có luật Không giao/Tối đa đơn, nên MinhNM nhận đơn dù TM ghi 'Minh làm MVP tuần đầu'. Xem cảnh báo có đủ rõ để TM sửa không.
- Luật 'Không giao AnTD · Game Emulator' hết hạn 17/10: có hiệu lực ngày chạy 16/10 nhưng không vào ngày áp luật 19/10 (A34).
- Dòng in ra phải là 8 luật, 7 có hiệu lực ngày 19/10/2026.

## case-5-du-lieu-ban: Dữ liệu bẩn, app mới

| STT | App | Đơn | Đáp án | off | gemini-1 | gemini-2 | gemini-3 | Hạng thật / nhắm tới |
|---|---|---|---|---|---|---|---|---|
| 1 | Phone Cleaner | 1.0.3 - Fix ANR màn dọn rác | giao sẵn | LinhNV [M*] | LinhNV [S] | LinhNV [S] | LinhNV [S] | (S) |
| 3 | Auto click | 1.1.2 - Add tracking/Edit UI | giao sẵn | AnTD [M*] | AnTD [M] | AnTD [M] | AnTD [S] | (M) |
| 4 | live video 2 | 1.0.9 - Fix ads | giao sẵn | — [M*] | — [S] | — [S] | — [S] | (S) |
| 5 | QR Scanner | 1.0.0 - Init project/Add ads/Add IAP | MinhNM | MinhNM [M*] | MinhNM [XL] | MinhNM [XL] | MinhNM [XL] | (XL) |
| 6 | Weather Live | 1.0.0 - Init project/Add widget/Add ads | LinhNV | LinhNV [M*] | LinhNV [XL] | LinhNV [XL] | LinhNV [XL] | (XL) |
| 7 | Fake GPS | 1.0.1 - Fix policy location permission | MinhNM | MinhNM [M*] | MinhNM [S] | MinhNM [S] | MinhNM [S] | (S) |
| 8 |  | Fix crash màn splash trên Android 14 | TiếnBV | TiếnBV [M*] | TiếnBV [S] | TiếnBV [S] | TiếnBV [S] | (S) |
| 9 | Speaker Cleaner | 1.1.3 - Fix ads/Fix luồng | LinhNV | LinhNV [M*] | LinhNV [S] | LinhNV [S] | LinhNV [S] | (M) |
| 10 | ps remote | 1.1.3 - Fix crash kết nối | MinhNM | MinhNM [M*] | MinhNM [S] | MinhNM [S] | MinhNM [S] | (S) |
| 11 | Nhiều App | Fix policy native too small cho 6 app | AnTD | AnTD [M*] | AnTD [M] | AnTD [M] | AnTD [M] | (M) |
| 12 | Game Emulator | 1.0.8 - Add feature save state/Add ads | AnTD | AnTD [M*] | AnTD [XL] | AnTD [XL] | AnTD [XL] | (XL) |
| 13 | VPN | 1.1.8 - Fix IAP | TiếnBV | TiếnBV [M*] | TiếnBV [S] | TiếnBV [S] | TiếnBV [S] | (M) |
| 14 | VPN | Crash khi xoay màn hình |  | bỏ qua | bỏ qua | bỏ qua | bỏ qua |  |

`*` = độ lớn mặc định (AI lỗi hoặc tắt). Hạng trong ngoặc là hạng mình nhắm tới khi viết mô tả, không phải giờ thật.

Dao động giữa 3 lần chạy AI: 1 đơn đổi độ lớn, 0 đơn đổi PIC.

Cần quan sát:

- STT 4 giao sẵn cho 'Bùi Văn Tiếng' (gõ sai tên TiếnBV): tool coi là người lạ, TiếnBV bị tính thiếu 1 đơn và không có cảnh báo nào (cái giá đã biết của D14).
- STT 1 tên dạng NFD có hai khoảng trắng, STT 3 viết thường: vẫn phải nhận ra LinhNV, AnTD (A10).
- STT 12 có mô tả khoảng 6.000 ký tự với 60 link: prompt phải cắt còn 600 ký tự và thay link bằng [link].
- Ba đơn urgent của app mới cùng lúc: hai middle+ nhận hai đơn, đơn thứ tư (high, không có app) rơi vào junior.
