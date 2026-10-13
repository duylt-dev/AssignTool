# Báo cáo triển khai `scrumbot` giai đoạn 1

Ngày 2026-10-13. Quyết định: `confirm.md` D49–D57, A54–A79 (từ form
[`261013-cau-hoi-lam-ro-dot-2-api-dev.md`](261013-cau-hoi-lam-ro-dot-2-api-dev.md), bạn chọn mọi phương án đề xuất).
Spec: [`docs/bot-spec.md`](../../docs/bot-spec.md) (bot) và [`docs/assignment-spec.md`](../../docs/assignment-spec.md)
(luật giao PIC). Bản đồ code: `LLM.md`.

## Kết luận ngắn

1. **GĐ 1 (D57) đã code xong và chạy được trên API dev.** `assigntool` đổi thành `scrumbot`, chia 4 lớp; mọi lần
   chạy đọc API `/api/doc/` của server dev (chỉ GET, từ chối production); sổ rủi ro 2–11; bộ nhớ giữa các lần chạy;
   sheet `Thay đổi`; `clone` + `replay` trên bản sao; báo cáo cuối sprint; script cài lịch chạy. 228 test qua (cộng 1
   test AI thật, chỉ chạy khi bật).
2. **Chạy thật trên Sprint 10 mất 18 giây** (lần đầu trong ngày, ~17 request); lần sau dùng cache, 5 request trong 4
   giây. Bot đề xuất 1 PIC cho đơn trống duy nhất, báo 1 rủi ro mức Cao (đơn urgent kẹt `in progress` 4,9 ngày làm
   việc) và cảnh báo đơn urgent chưa có hạn.
3. **Giao lại 29 sprint cũ trên bản sao: khớp TM 111/174 đơn (64%)**, năm 2025 là 81%, năm 2026 là 54%. Bản backtest
   cũ trên file Tech manager khớp 43/92 (47%).
4. **Sổ rủi ro: trên 4 sprint có lịch sử trạng thái, bot báo trước 14/17 đơn có kết cục xấu (82%), và 14/21 đơn bot
   báo mức Cao/Trung bình có kết cục xấu thật (67%).** Trên cả 28 sprint đã kết thúc, tỉ lệ báo đúng chỉ còn 29%, vì
   trước 09/2026 không có lịch sử trạng thái nên bot phải đoán việc dở theo ngày đóng.
5. **Dữ liệu dev không mới trong ngày.** Tới 13:36 ngày 13/10, bản ghi mới nhất trên dev vẫn là 12/10 22:27. Gần như
   chắc dev chỉ đồng bộ với production mỗi tối, nên các lần chạy 30 phút trong ngày sẽ không thấy đơn mới. Cần hỏi TM
   (mục 6).

## 1. Đã làm những gì

| Hạng mục (D57) | Trạng thái | Ở đâu |
|---|---|---|
| Đổi tên `scrumbot`, 4 lớp: nguồn · hiểu đơn · quyết định · hành động (D46) | Xong, 161 test cũ vẫn xanh sau khi đổi tên | `src/scrumbot/{sources,understanding,rules,actions,flows}` |
| Nguồn API dev, chỉ GET, từ chối `circle.datlt.site` (D49, A54–A59, A64) | Xong | `sources/api_client.py`, `env_config.py`, `api_reader.py` |
| Snapshot mỗi lần chạy, cache list cũ, chạy lại offline `--snapshot` (A57, A58) | Xong | `sources/raw_store.py`, `state/snapshots/` |
| AI hiểu đơn theo tiêu đề: độ lớn, loại đơn, hạng mục, rủi ro kỹ thuật; nhớ theo id + tên (D50, A67, A79) | Xong | `understanding/`, bảng `ai_answers` |
| Sổ rủi ro 2–11 (D45, A73–A75) | Xong | `rules/capacity.py`, `pic_risks.py`, `progress.py`, `risk_register.py` |
| Cảnh báo dữ liệu thay rủi ro 1: thiếu App, đơn urgent/high không có hạn (`DUE-MISSING`, D53) | Xong | `rules/validate.py` |
| Bộ nhớ SQLite: đề xuất giữ giữa các lần chạy, trạng thái đơn để so (A51, A62, A66) | Xong | `actions/state_store.py` |
| Sheet `Thay đổi`, rủi ro 9 `ORDER-CHANGED` | Xong | `rules/changes.py` |
| Báo cáo 6 sheet: `Tóm tắt`, `Phân công`, `Rủi ro`, `Thay đổi`, `Cảnh báo`, `Tải dev` (A76) | Xong | `actions/xlsx_report.py`, `workbook.py` |
| `clone` + `replay`, chấm giao người (D55) và chấm rủi ro theo kết cục thật ở 3 mốc (D56) | Xong, đã chạy trên 29 sprint | `flows/clone.py`, `rules/replay.py`, `replay_risks.py` |
| Báo cáo cuối sprint (A72) | Xong | `flows/sprint_end.py` |
| Chạy theo lịch: `scrumbot auto`, thông báo macOS, log 30 ngày (D54, A68, A78) | Code xong; **lịch chưa cài** (mục 6) | `flows/auto.py`, `actions/notify.py`, `scripts/lich-chay.sh` |
| Tài liệu | Viết mới `docs/bot-spec.md`; cập nhật `LLM.md`, best practices §12, assignment spec, `README.md`, `eval/README.md` | |

Lệnh `--backtest` cũ đã bỏ, thay bằng `replay` (D51). Phần đọc file export giữ nguyên để `eval/` chạy như cũ
(`scrumbot run --source file`).

## 2. Cách chạy

```bash
uv run scrumbot run                                # sprint đang chạy, AI mặc định gemini; --ai agy|off
uv run scrumbot clone                              # chụp dữ liệu vào state/clone/<giờ> (chỉ GET)
uv run scrumbot replay --clone state/clone/<giờ>   # không gọi API
uv run scrumbot sprint-end                         # báo cáo sprint vừa kết thúc
scripts/lich-chay.sh install|uninstall|status|run-now
```

`.env` cần `SCRUMBOT_API_TOKEN` và `SCRUMBOT_API_BASE=https://devclickup.datlt.site` (đã đổi, bot chạy được).

## 3. Chạy thật trên API dev (13/10)

| Lần | Kết quả |
|---|---|
| Lần đầu trong ngày, `--ai off` | 18 giây, ~17 request; lịch sử giao việc lấy từ API (374 đơn gốc) |
| Lần sau cùng bộ nhớ | 5 request, 4 giây; đề xuất PIC giữ nguyên (A66) |
| Lần 13:36 | Sprint 10 (6/10–17/10): 6 đơn, 5 đơn giao sẵn, bot đề xuất 1 (Roblox skin 1.0.5 → AnTD, dự phòng MinhNM, TiếnBV). Rủi ro: 1 Cao (`STATUS-STUCK`: đơn STT 6 ở `in progress` 4,9 ngày làm việc, 7 subtask kẹt), 2 Trung bình. Cảnh báo `DUE-MISSING`: đơn STT 6 urgent chưa có hạn |

Chạy với `agy` thì AI mất khoảng 2 phút cho một sprint; các lần sau lấy kết quả từ bộ nhớ, không gọi AI (A67).

## 4. Giao lại 29 sprint cũ (replay)

Bản sao `state/clone/20261013-111406`: 35 list, lịch sử trạng thái của 4.816 dòng, 133 request, chỉ GET.
Chạy `replay` không AI (mọi đơn `M`, A69). File: `output/replay_20261013-111613.xlsx`.

### 4.1 Giao người

| Nhóm | Sprint | Khớp TM |
|---|---|---|
| Pool 2 dev (08–10/2025) | 6 | 30/33 (91%) |
| Pool 3 dev (10/2025–06/2026) | 14 | 43/74 (58%) |
| Pool 4 dev (từ 06/2026) | 9 | 38/67 (57%) |
| **Tổng** | **29** | **111/174 (64%)** |

Khớp giảm khi pool đông lên: với 2 dev, gần như chỉ có một lựa chọn. Các sprint thấp nhất: Sprint 8 (9/2026) 2/9,
Sprint 16 (3/2026) 1/5, Sprint 17 (4/2026) 1/4. Như đánh giá đợt 1, phần lớn chỗ lệch là do giới hạn cân tải (D26):
TM dồn việc cho một người nhiều hơn mức bot cho phép. Bot không đặt ngưỡng đạt (D22).

### 4.2 Sổ rủi ro (mức Cao và Trung bình)

| Mã | 4 sprint có lịch sử trạng thái: báo đúng | báo đủ | 28 sprint đã kết thúc: báo đúng | báo đủ |
|---|---|---|---|---|
| `DUE-AT-RISK` | 13/15 (87%) | 13/17 (76%) | 38/131 (29%) | 38/57 (67%) |
| `CARRY-OVER` | 12/17 (71%) | 12/17 (71%) | 39/147 (27%) | 39/57 (68%) |
| `QA-RETURNS` | 10/11 (91%) | 10/17 (59%) | 23/38 (61%) | 23/57 (40%) |
| `CAPACITY-DEV` | 8/11 (73%) | 8/17 (47%) | 31/120 (26%) | 31/57 (54%) |
| `STATUS-STUCK` | 7/8 (88%) | 7/17 (41%) | 15/64 (23%) | 15/57 (26%) |
| `SCOPE-ADDED` | 2/2 | 2/17 | 4/22 (18%) | 4/57 (7%) |
| `CAPACITY-SPRINT` | 1/1 | 1/17 | 17/77 (22%) | 17/57 (30%) |
| `PIC-UNFAMILIAR` | — | — | 0/3 | 0/57 |
| **Mọi loại** | **14/21 (67%)** | **14/17 (82%)** | **47/164 (29%)** | **47/57 (82%)** |

**Báo đúng** = trong các đơn bot báo, bao nhiêu % có kết cục xấu. **Báo đủ** = trong các đơn có kết cục xấu, bao nhiêu
% được báo trước. Bot báo trước trung vị 8,5 ngày làm việc (4 sprint có lịch sử). `PIC-ABSENT` không bật lần nào;
`ORDER-CHANGED` không chấm được trên bản sao vì cần trạng thái lưu từ lần chạy trước.

Cách đọc: số của 4 sprint có lịch sử (Sprint 3, 6, 8, 9 năm 2026) là số đáng tin, nhưng mẫu nhỏ (17 đơn xấu). Số 28
sprint thấp vì thiếu lịch sử trạng thái: bot đếm việc dở theo ngày đóng (A70), nên báo quá nhiều. Hạn, ưu tiên và tên
đơn là giá trị hiện tại, có thể đã bị sửa sau mốc (D56).

## 5. Kiểm tra

| Kiểm | Kết quả |
|---|---|
| `ruff check`, `ruff format --check` | Sạch |
| `pytest` | 228 qua, 1 bỏ qua (test AI thật, chỉ chạy khi bật) |
| `eval/` `--ai off` (`eval/results/20261013-1122-off-scrumbot/`) | Giống hệt lần trước: khớp TM 8/11 và 4/9; theo spec 5/5, 10/10, 9/9; cảnh báo thiếu/thừa 0/0. Đáp án thêm `DUE-MISSING` (D53) |
| `scrumbot run --source file --ai off --today 2026-10-06` trên `input/` | Exit 0; khớp assignment spec §12 (`test_real_input` 5/5) |
| Ranh giới code (CLAUDE.md) | Chỉ `api_client` gọi HTTP, chỉ `state_store` dùng SQLite, chỉ `ai_cli` và `notify` mở tiến trình con (không `shell=True`), chỉ `cli.py` in ra; lớp quyết định không đọc đồng hồ, file hay biến môi trường |

Review lần hai: Codex đã hết hạn mức (tới 05/11), nên script chuyển sang Antigravity. Nó nêu 5 điểm, mình xét từng
điểm. Một điểm đúng: `AGENTS.md` (file Codex đọc đầu tiên) vẫn mô tả `assigntool`, layout và ranh giới import cũ. Đã
sửa. Bốn điểm còn lại bác bỏ: giữ lệnh `assigntool` làm alias trái với D46; `notify.py` được phép mở tiến trình con
(CLAUDE.md); `auto` vốn đã trả exit code; định dạng ngày theo vị trí cột ở sheet do chính bot ghi là cách
`replay_report.py` cũng dùng.

## 6. Việc cần bạn làm

1. **Cài lịch chạy (C3).** Chạy `scripts/lich-chay.sh run-now`; khi macOS hỏi có cho python của bot truy cập Desktop
   không, bấm **Allow**. Sau đó chạy `scripts/lich-chay.sh install`. Nếu macOS chặn mà không hỏi: System Settings ›
   Privacy & Security › Files and Folders (hoặc Full Disk Access), cấp quyền cho `.venv/bin/python` của repo. Mình
   chưa cài vì bước này cần bạn bấm Allow.
2. **Hỏi TM** (không chặn việc gì):
   - Dev đồng bộ với production lúc nào? Số đo trưa nay cho thấy dev chỉ có dữ liệu tới tối hôm trước. Nếu đúng là
     đồng bộ mỗi tối thì các lần chạy 30 phút không có ích, và bot giao đơn chậm tới một ngày.
   - Thêm trường `mo_ta` (không có link) vào `/api/doc/don`. Khi có, bot tự dùng mô tả, dòng log "chưa trả mô tả" tự
     mất, và mở được rủi ro 1, 12 ở GĐ 2 (D53).

## 7. Giả định và hạn chế

- **Lịch sử trạng thái chỉ có từ 09/2026** (D56): chấm rủi ro ở mục 4.2 chỉ đáng tin trên 4 sprint. Số sẽ tốt dần
  khi có thêm sprint.
- **O12** vẫn mở: `QA-RETURNS` bật theo số bug, vì team ghi QA trả về bằng bug chứ không bằng trạng thái.
- **Sai lệch V2** (`LLM.md` §11): 5 file trên ~200 dòng (`rules/board.py`, `model.py`, `actions/state_store.py`,
  `rules/progress.py`, `actions/replay_report.py`). Mỗi file giữ một chủ đề, tách khi một file lớn thêm.
- `state/` trên máy có 18 snapshot của các lần chạy thử sáng 13/10 (~10 MB). Không commit, xoá được bất cứ lúc nào.

## 8. GĐ 2

Ghi vào hệ thống theo D43 (comment, điền `Người làm`) khi có API ghi (O8); rủi ro 1, 12 và sheet `Phản hồi BA` khi API
có mô tả (D53).
