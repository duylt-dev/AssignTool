# Bảng điểm eval 20261008-1610-agy-sau-sua

Commit: `e2b519b (src/ có thay đổi chưa commit)` · AI: `agy` × 3 lần · đáp án và cách chấm: `confirm.md` A37, A40.

| Case | Lần chạy | PIC khớp TM | PIC theo spec | Dự phòng theo spec | Giữ đơn giao sẵn | Độ lớn cùng hạng | Lệch ≤ 1 hạng | Độ lớn mặc định | Cảnh báo thiếu / thừa | Giây | Độ lớn |
|---|---|---|---|---|---|---|---|---|---|---|---|
| case-1-sprint-9 | off | 8/11 | — | — | 1/1 | — | — | — | 0 / 0 | 0.3 | tắt AI (mọi đơn M) |
| case-1-sprint-9 | agy-1 | 8/11 | — | — | 1/1 | 6/12 | 11/12 | 0 | — | 176.1 | AI (agy, 12/12 đơn) |
| case-1-sprint-9 | agy-2 | 8/11 | — | — | 1/1 | 6/12 | 11/12 | 0 | — | 128.0 | AI (agy, 12/12 đơn) |
| case-1-sprint-9 | agy-3 | 8/11 | — | — | 1/1 | 6/12 | 11/12 | 0 | — | 136.3 | AI (agy, 12/12 đơn) |
| case-2-sprint-8 | off | 4/9 | — | — | 2/2 | — | — | — | 0 / 0 | 0.3 | tắt AI (mọi đơn M) |
| case-2-sprint-8 | agy-1 | 4/9 | — | — | 2/2 | 6/8 | 8/8 | 0 | — | 329.2 | AI (agy, 11/11 đơn) |
| case-2-sprint-8 | agy-2 | 4/9 | — | — | 2/2 | 5/8 | 8/8 | 0 | — | 124.6 | AI (agy, 11/11 đơn) |
| case-2-sprint-8 | agy-3 | 4/9 | — | — | 2/2 | 5/8 | 8/8 | 0 | — | 254.2 | AI (agy, 11/11 đơn) |

## case-1-sprint-9: Sprint 9 dựng lại

| STT | App | Đơn | Đáp án | off | agy-1 | agy-2 | agy-3 | Hạng thật / nhắm tới |
|---|---|---|---|---|---|---|---|---|
| 1 | PS Remote | 1.1.1 - Fix ads/FIx luồng/ fix policy | LinhNV, MinhNM | MinhNM [M*] | MinhNM [L] | MinhNM [L] | MinhNM [L] | XL |
| 28 | AR Dog | 1.1.1. Add New feature/ Add ads | LinhNV | LinhNV [M*] | LinhNV [XL] | LinhNV [XL] | LinhNV [XL] | M |
| 49 | Game Emulator | 1.0.5 Add fearture/Add tracking/Fix bug/Fix cras | AnTD | AnTD [M*] | AnTD [XL] | AnTD [XL] | AnTD [XL] | XL |
| 62 | Speak2 | 1.0.6 - Fix ads/Edit luồng/Fix UI | MinhNM | TiếnBV [M*] | TiếnBV [L] | TiếnBV [L] | TiếnBV [L] | XL |
| 91 | Game mode 2 | 1.0.1 - Add ads/Add IAP/Add | TiếnBV | TiếnBV [M*] | TiếnBV [XL] | TiếnBV [XL] | TiếnBV [XL] | XL |
| 142 | AR Dog | 1.1.0. Edit Flow/Fix ads | LinhNV, AnTD | LinhNV [M*] | LinhNV [L] | LinhNV [L] | LinhNV [L] | L |
| 160 | metal detector | 1.0.7 - Fix policy native too small | LinhNV | MinhNM [M*] | MinhNM [S] | MinhNM [S] | MinhNM [S] | S |
| 162 | Santa prank | 1.2.4. Fix crash | LinhNV | LinhNV [M*] | LinhNV [S] | LinhNV [S] | LinhNV [S] | S |
| 165 | Game Emulator | 1.0.3. Fix crash | AnTD | AnTD [M*] | AnTD [S] | AnTD [S] | AnTD [S] | M |
| 170 | SpeakerCleaner | 1.1.2 - Fix ads/Fix luồng/ Fix policy | LinhNV | MinhNM [M*] | MinhNM [L] | MinhNM [L] | MinhNM [L] | M |
| 182 | Game Emulator | Nghiên cứu kỹ thuật ứng dụnng game emutaltor | AnTD | AnTD [M*] | AnTD [M] | AnTD [M] | AnTD [M] | M |
| 183 | PS Remote | Nghiên cứu và demo tính năng interactive play vi | giao sẵn | — [M*] | — [XL] | — [XL] | — [XL] | L |

`*` = độ lớn mặc định (AI lỗi hoặc tắt). Hạng trong ngoặc là hạng mình nhắm tới khi viết mô tả, không phải giờ thật.

Dao động giữa 3 lần chạy AI: 0 đơn đổi độ lớn, 0 đơn đổi PIC.

Lệch ở lần `off`:

- STT 62 Speak2: tool TiếnBV, TM MinhNM
- STT 160 metal detector: tool MinhNM, TM LinhNV
- STT 170 SpeakerCleaner: tool MinhNM, TM LinhNV

Lệch ở lần `agy-1`:

- STT 62 Speak2: tool TiếnBV, TM MinhNM
- STT 160 metal detector: tool MinhNM, TM LinhNV
- STT 170 SpeakerCleaner: tool MinhNM, TM LinhNV

Lệch ở lần `agy-2`:

- STT 62 Speak2: tool TiếnBV, TM MinhNM
- STT 160 metal detector: tool MinhNM, TM LinhNV
- STT 170 SpeakerCleaner: tool MinhNM, TM LinhNV

Lệch ở lần `agy-3`:

- STT 62 Speak2: tool TiếnBV, TM MinhNM
- STT 160 metal detector: tool MinhNM, TM LinhNV
- STT 170 SpeakerCleaner: tool MinhNM, TM LinhNV

## case-2-sprint-8: Sprint 8 dựng lại

| STT | App | Đơn | Đáp án | off | agy-1 | agy-2 | agy-3 | Hạng thật / nhắm tới |
|---|---|---|---|---|---|---|---|---|
| 1 | Auto click | 1.0.8. Add tracking/Edit Flow/Edit UI/Add featur | AnTD | AnTD [M*] | AnTD [XL] | AnTD [XL] | AnTD [XL] | XL |
| 11 | Nhiều App | Fix lỗi quảng cáo native too small | LinhNV | MinhNM [M*] | MinhNM [XL] | MinhNM [XL] | MinhNM [XL] |  |
| 16 | number tracker | 1.1.3 - Fix ads/FIx luồng | MinhNM | AnTD [M*] | TiếnBV [L] | TiếnBV [L] | TiếnBV [L] | L |
| 32 | AR Dog | 1.0.7.Check và fix bug/Edit model/Fix ads/Add tr | LinhNV, AnTD | TiếnBV [M*] | TiếnBV [L] | TiếnBV [L] | TiếnBV [L] | L |
| 45 | spin wheel 2 | [1.0.1] - Add ads | LinhNV | LinhNV [M*] | LinhNV [L] | LinhNV [L] | LinhNV [XL] | L |
| 50 | Roblox skin | 1.0.1 - Add ads | AnTD | MinhNM [M*] | MinhNM [M] | MinhNM [M] | MinhNM [M] | L |
| 60 | camera detector | 1.1.5 - chuyển store | LinhNV | LinhNV [M*] | LinhNV [S] | LinhNV [S] | LinhNV [S] | S |
| 61 | AR Dog | 1.0.8. Fix crash/Tối ưu request data | LinhNV | LinhNV [M*] | LinhNV [M] | LinhNV [M] | LinhNV [M] | S |
| 64 | Roblox skin | 1.0.3. Fix policy Device and Network Abuse | giao sẵn | — [M*] | — [S] | — [S] | — [S] |  |
| 65 | WifiHotspot | 1.2.4- Fix policy | giao sẵn | — [M*] | — [M] | — [M] | — [M] |  |
| 66 | Game mode | 1.1.1 - Fix policy native too small | LinhNV | MinhNM [M*] | MinhNM [M] | MinhNM [L] | MinhNM [M] | M |

`*` = độ lớn mặc định (AI lỗi hoặc tắt). Hạng trong ngoặc là hạng mình nhắm tới khi viết mô tả, không phải giờ thật.

Dao động giữa 3 lần chạy AI: 2 đơn đổi độ lớn, 0 đơn đổi PIC.

Lệch ở lần `off`:

- STT 11 Nhiều App: tool MinhNM, TM LinhNV
- STT 16 number tracker: tool AnTD, TM MinhNM
- STT 32 AR Dog: tool TiếnBV, TM LinhNV, AnTD
- STT 50 Roblox skin: tool MinhNM, TM AnTD
- STT 66 Game mode: tool MinhNM, TM LinhNV

Lệch ở lần `agy-1`:

- STT 11 Nhiều App: tool MinhNM, TM LinhNV
- STT 16 number tracker: tool TiếnBV, TM MinhNM
- STT 32 AR Dog: tool TiếnBV, TM LinhNV, AnTD
- STT 50 Roblox skin: tool MinhNM, TM AnTD
- STT 66 Game mode: tool MinhNM, TM LinhNV

Lệch ở lần `agy-2`:

- STT 11 Nhiều App: tool MinhNM, TM LinhNV
- STT 16 number tracker: tool TiếnBV, TM MinhNM
- STT 32 AR Dog: tool TiếnBV, TM LinhNV, AnTD
- STT 50 Roblox skin: tool MinhNM, TM AnTD
- STT 66 Game mode: tool MinhNM, TM LinhNV

Lệch ở lần `agy-3`:

- STT 11 Nhiều App: tool MinhNM, TM LinhNV
- STT 16 number tracker: tool TiếnBV, TM MinhNM
- STT 32 AR Dog: tool TiếnBV, TM LinhNV, AnTD
- STT 50 Roblox skin: tool MinhNM, TM AnTD
- STT 66 Game mode: tool MinhNM, TM LinhNV
