"""The three synthetic cases of the evaluation set (confirm.md A39) and their expected results by spec (A37).

Expected PICs and backups were worked out by hand from spec §7 before the tool was run on these files, for the
`--ai off` run (every order M). Each comment gives the deciding step, so a disagreement with the tool can be traced to
the spec or to the code. Synthetic people outside the pool have invented names (A39).
"""

from __future__ import annotations

import unicodedata
from datetime import datetime

LINH, MINH, AN, TIEN = "Ngọc Văn Linh", "Nguyễn Nhật Minh", "Trần Đức An", "Bùi Văn Tiến"
BA = "BA Nguyễn Thị Hoa"
SPRINT_11 = ("Sprint 11", "Sprint 11 (10/19 - 10/30)", "2026-10-19", "2026-10-30")
SPRINT_10 = ("Sprint 10", "Sprint 10 (10/6 - 10/17)", "2026-10-06", "2026-10-17")
HISTORY = "input/Tech_manager_T2-T10_2026.xlsx"


def d(day: str) -> datetime:
    return datetime.strptime(day, "%Y-%m-%d")


def task(stt, app, title, *, pic=None, pri=None, due=None, created, desc=None, status="ready to progress", kind="Task"):
    return {
        "STT": stt,
        "Nhóm trạng thái": status,
        "Task": title,
        "Loại": kind,
        "App Name.": app,
        "Trạng thái": status,
        "Người làm": pic,
        "Ưu tiên": pri,
        "Hạn": d(due) if due else None,
        "Người tạo": BA,
        "Ngày tạo": d(created) if isinstance(created, str) and "-" in created else created,
        "Mô tả": desc,
    }


def sub(stt, parent, title, pic, status="all issue", created="2026-10-12"):
    row = task(stt, None, title, pic=pic, created=created, status=status, kind="Subtask")
    return {**row, "Task cha": parent}


def links(slug: str) -> str:
    return (
        f"- Link SRS https://docs.google.com/document/d/eval-{slug}/edit\n"
        f"- Link UI https://www.figma.com/design/eval-{slug}/UI?node-id=1-2\n"
        f"- Tracking https://docs.google.com/spreadsheets/d/eval-{slug}-tracking/edit"
    )


# ---------------------------------------------------------------------------------------------------------------
# Case 3: mid-sprint run, leave, carry-over. Run day Thursday 22/10, MinhNM off the whole sprint, AnTD off 3 days.
# Loads after the pre-assigned orders: LinhNV 2 orders, AnTD 1, TiếnBV 1 (MinhNM is out of the pool, D7/A12).
# Carry-over from the synthetic Sprint 10: LinhNV 3, TiếnBV 1, AnTD 0 (MinhNM 2, irrelevant).
# ---------------------------------------------------------------------------------------------------------------

CASE_3 = {
    "slug": "case-3-giua-sprint",
    "title": "Giữa sprint, nghỉ phép, việc dở",
    "today": "2026-10-22",
    "sprint": SPRINT_11,
    "prev": SPRINT_10,
    "devs": {
        MINH: "19/10/2026, 20/10/2026, 21/10/2026, 22/10/2026, 23/10/2026, 26/10/2026, 27/10/2026, "
        "28/10/2026, 29/10/2026, 30/10/2026",
        AN: "22/10/2026, 23/10/2026, 26/10/2026",
        TIEN: "16/10/2026",
    },
    "rows": [
        task(
            1,
            "VPN",
            "1.1.8 - Fix IAP/Fix luồng",
            pic=LINH,
            created="2026-10-15",
            desc=(
                "Chi tiết đơn liên hệ BA: Hoa\n1. Fix IAP: user mua gói tuần bị trả về gói free sau "
                "khi khởi động lại app, "
                "kiểm tra lại luồng restore purchase và acknowledge.\n2. Fix luồng: bỏ màn intro thứ 2, chuyển paywall "
                "lên sau màn chọn server.\n3. Cập nhật thư viện billing lên bản 7.\n" + links("vpn-118")
            ),
        ),
        sub(2, "1.1.8 - Fix IAP/Fix luồng", "Fix IAP restore", LINH),
        task(
            3,
            "Phone Cleaner",
            "1.0.3 - Fix policy quyền thông báo",
            pic=TIEN,
            created="2026-10-15",
            desc=(
                "Google Play cảnh báo quyền POST_NOTIFICATIONS: chỉ xin quyền khi user bật nhắc dọn rác, thêm một màn "
                "giải thích trước khi xin quyền.\nChi tiết: https://app.clickup.com/t/eval-pc-103"
            ),
        ),
        task(
            4,
            "Speak2",
            "1.0.7 - Add ads/Edit UI",
            pic=MINH,
            created="2026-10-14",
            desc=(
                "1. Gắn thêm 2 vị trí native ở màn kết quả và màn lịch sử.\n2. Edit UI màn home theo figma mới.\n"
                + links("speak2-107")
            ),
        ),
        task(
            5,
            "Game Emulator",
            "1.0.7 - Add feature cloud save",
            pic=f"{AN}, Nguyễn Văn Kiểm",
            created="2026-10-14",
            desc=(
                "Bổ sung tính năng cloud save: đăng nhập Google, đồng bộ save state lên Drive, chọn bản save khi mở "
                "game, xử lý xung đột khi hai máy cùng lưu.\nThêm màn quản lý bản save, 6 event tracking mới, gắn "
                "inter khi load save.\n" + links("emu-107")
            ),
        ),
        task(
            6,
            "AR Dog",
            "1.1.2 - Fix ads",
            pic=LINH,
            created="2026-10-16",
            desc="Fix native màn camera bị đè lên nút chụp trên màn hình nhỏ. https://app.clickup.com/t/eval-ardog",
        ),
        task(
            7,
            "QR Scanner",
            "1.0.0 - Init project/Add ads/Add IAP",
            pri="urgent",
            created="2026-10-20",
            desc=(
                "App mới. Dựng project từ base, các màn: splash, onboarding 3 màn, quét QR/barcode "
                "bằng camera, lịch sử "
                "quét, tạo QR, setting.\nGắn đủ bộ ads (open, inter, native, banner) theo file ads, IAP gói tuần/năm, "
                "tracking theo file.\n" + links("qr-100")
            ),
        ),
        task(
            8,
            "Game Emulator",
            "1.0.8 - Fix crash khi load ROM",
            pri="high",
            due="2026-10-24",
            created="2026-10-21",
            desc="Fix crash top 1 Crashlytics: NullPointerException khi load ROM từ thẻ nhớ ngoài.\n"
            "https://console.firebase.google.com/u/0/project/eval-emu/crashlytics",
        ),
        task(
            9,
            "PS Remote",
            "1.1.3 - Fix crash/Fix ANR",
            pri="high",
            created="2026-10-20",
            desc=(
                "Fix 3 crash và 1 ANR top của bản 1.1.2: crash khi mất wifi giữa chừng, crash màn remote play trên "
                "Android 9, ANR khi tìm thiết bị.\nhttps://console.firebase.google.com/u/0/project/eval-psremote"
            ),
        ),
        task(
            10,
            "Auto click",
            "1.1.2 - Edit UI/Add tracking",
            created="2026-10-20",
            desc=(
                "1. Edit UI màn setting và màn tạo kịch bản theo figma mới.\n2. Thêm 8 event tracking theo file.\n"
                + links("autoclick-112")
            ),
        ),
        task(
            11,
            "live video 2",
            "1.0.9 - Fix ads/Edit luồng",
            created="2026-10-21",
            desc=(
                "1. Fix ads: đổi native full sang inter ở luồng xem video, thêm remote bật/tắt từng "
                "vị trí.\n2. Edit luồng: "
                "thêm màn chọn chủ đề sau onboarding, đổi thứ tự tab.\n3. Fix UI màn player trên tablet.\n"
                + links("livevideo2-109")
            ),
        ),
    ],
    "prev_rows": [
        task(
            1,
            "Phone Cleaner",
            "1.0.2 - Add ads/Add SDK",
            pic=f"{LINH}, {TIEN}",
            created="2026-10-05",
            status="qa - need fix",
        ),
        sub(2, "1.0.2 - Add ads/Add SDK", "Add IAP sdk + placement", LINH, "internal - need fix", "2026-10-05"),
        sub(3, "1.0.2 - Add ads/Add SDK", "Add tracking", TIEN, "done", "2026-10-06"),
        task(4, "PS Remote", "1.1.2 - Add feature/ Add ads", pic=MINH, created="2026-10-05", status="in progress"),
        sub(5, "1.1.2 - Add feature/ Add ads", "Add remote config", MINH, "all issue", "2026-10-06"),
        task(6, "Auto click", "1.1.1 - Add Ads/Fix luồng", pic=AN, created="2026-09-17", status="ready to release"),
        task(
            7,
            "spin wheel 2",
            "1.0.2. Edit Flow/Add tracking/ Add ads",
            pic=LINH,
            created="2026-10-05",
            status="need to be clean",
        ),
        task(
            8,
            "Game Emulator",
            "Edit flow download/add flow auto scan game",
            pic=AN,
            created="2026-10-05",
            status="done",
        ),
        task(9, "Roblox skin", "1.0.4 - Fix luồng/Add Ads/Fix UI", pic=AN, created="2026-09-22", status="pending"),
    ],
    "size_target": {1: "L", 3: "S", 4: "M", 5: "XL", 6: "S", 7: "XL", 8: "S", 9: "M", 10: "M", 11: "L"},
    # Processing order (A5): 7 urgent; 8 high with a due date; 9 high; 10, 11 normal by creation date.
    "expect": {
        7: ("LinhNV", ("AnTD", "TiếnBV")),  # new app, urgent: only LinhNV is middle+ (MinhNM on leave); cap 2 ≤ 1+1
        8: ("AnTD", ("LinhNV", "TiếnBV")),  # LinhNV capped (3 > 1+1); AnTD on the latest Game Emulator
        9: ("TiếnBV", ("LinhNV", "AnTD")),  # LinhNV capped; AnTD and TiếnBV unfamiliar, TiếnBV 16h < AnTD 32h
        10: ("AnTD", ("LinhNV", "TiếnBV")),  # cap 2+1 lets everyone in; AnTD on the latest Auto click
        11: ("TiếnBV", ("LinhNV", "AnTD")),  # TiếnBV on the latest live video 2
    },
    # A43 added after the baseline run; DUE-MISSING (urgent/high without Hạn) added 2026-10-13 by D53
    "findings": [("DEV-ON-LEAVE", None), ("PRE-ASSIGNED-ON-LEAVE", 4), ("DUE-MISSING", 7), ("DUE-MISSING", 9)],
    "watch": [
        "STT 4 giao sẵn cho MinhNM, người nghỉ cả sprint: đơn được giữ (D10). Lượt baseline không có cảnh báo nào; "
        "từ A43 có `PRE-ASSIGNED-ON-LEAVE`.",
        "PS Remote: version gần nhất thật (1.1.2, Sprint 10) chỉ có MinhNM; MinhNM ra khỏi pool nên spec §6.1 bỏ đơn "
        "đó và coi 1.1.1 (LinhNV) là version gần nhất. Lý do của STT 9 sẽ ghi LinhNV 'quen app hơn' theo 1.1.1.",
        "AnTD nghỉ 3 ngày vẫn nhận đơn high (STT 8): nghỉ phép chỉ phá hoà (A12).",
        "STT 5 có người ngoài danh sách (tên giả) cùng AnTD: tên đó bị bỏ qua (D14).",
    ],
}

# ---------------------------------------------------------------------------------------------------------------
# Case 4: TM rules. Run day Friday 16/10, the rules day is the sprint's first day 19/10 (A34), so the rule that ends
# 17/10 is not in force and the rules dated 19/10 are. Nobody has carry-over or leave.
# Loads after the pre-assigned orders: TiếnBV 1, MinhNM 1 (MinhNM is kept off every order by a rule).
# ---------------------------------------------------------------------------------------------------------------

RULES_4 = """# Luật giao việc Sprint 11

Ghi chú của TM: Minh làm MVP tuần đầu sprint. Bảng cuối file là lịch họp, không phải luật.

## Luật cố định

| Loại       | Dev    | App        | Số đơn | Từ ngày | Đến ngày | Ghi chú                                   |
|------------|--------|------------|--------|---------|----------|-------------------------------------------|
| Chỉ định   | LinhNV | AR Dog     |        |         |          | Linh giữ AR Dog                           |
| Ưu tiên    | TiếnBV | PS Remote  |        |         |          | Cho Tiến học PS Remote                    |
| Ưu tiên    | NamPV  | Spin wheel |        |         |          | Nam học Spin wheel khi bắt đầu nhận việc  |
| Không giao | LinhNV | Lovetest   |        |         |          |                                           |
| Không giao | TiếnBV | Lovetest   |        |         |          |                                           |

## Luật Sprint 11

| Loại       | Dev    | App           | Số đơn | Từ ngày    | Đến ngày   | Ghi chú              |
|------------|--------|---------------|--------|------------|------------|----------------------|
| Không giao | MinhNM |               |        | 19/10/2026 | 23/10/2026 | Minh làm MVP tuần đầu |
| Tối đa đơn | AnTD   |               | 2      | 19/10/2026 | 30/10/2026 | An onboard dự án mới |
| Không giao | AnTD   | Game Emulator |        | 12/10/2026 | 17/10/2026 | Hết hạn trước sprint |

## Lịch họp

| Ngày  | Nội dung |
|-------|----------|
| 19/10 | Planning |
"""

CASE_4 = {
    "slug": "case-4-luat-tm",
    "title": "Luật TM",
    "today": "2026-10-16",
    "sprint": SPRINT_11,
    "prev": SPRINT_10,
    "devs": {},
    "extra_devs": [("Phạm Văn Nam", "NamPV", "junior", "N", None)],
    "rules": RULES_4,
    "rows": [
        task(
            1,
            "AR Dog",
            "1.1.2 - Fix crash màn camera",
            pic=TIEN,
            created="2026-10-12",
            desc="Fix crash khi mở camera filter lần đầu trên Android 13. https://console.firebase.google.com/eval",
        ),
        task(
            2,
            "Speak2",
            "1.0.7 - Add ads/Edit UI",
            pic=MINH,
            created="2026-10-12",
            desc="Gắn 2 vị trí native, sửa UI màn home theo figma.\n" + links("speak2-107"),
        ),
        task(
            3,
            "PS Remote",
            "1.1.3 - Add feature/Add ads",
            pri="urgent",
            created="2026-10-13",
            desc=(
                "1. Thêm tính năng điều khiển bằng giọng nói (bật/tắt, chuyển kênh).\n2. Gắn inter khi kết nối thành "
                "công.\n" + links("psremote-113")
            ),
        ),
        task(
            4,
            "AR Dog",
            "1.1.3 - Add New feature mini game/Add ads",
            pri="high",
            created="2026-10-13",
            desc=(
                "Mục tiêu: thêm mini game cho thú cưng trên màn camera AR (3 trò), bảng điểm, chia "
                "sẻ ảnh.\nGắn ads theo "
                "file mới, tracking 10 event.\n" + links("ardog-113")
            ),
        ),
        task(
            5,
            "AR Dog",
            "1.1.4 - Fix ads/Fix luồng",
            created="2026-10-13",
            desc="Fix native too small màn kết quả, chuyển paywall sau onboarding.\n" + links("ardog-114"),
        ),
        task(
            6,
            "PS Remote",
            "1.1.4 - Fix policy",
            created="2026-10-13",
            desc="Fix policy native too small theo template: https://docs.google.com/spreadsheets/d/eval-policy",
        ),
        task(
            7,
            "Game Emulator",
            "1.0.8 - Add feature cloud save",
            created="2026-10-14",
            desc=(
                "Đồng bộ save state lên Drive, chọn bản save khi mở game, màn quản lý bản save.\n" + links("emu-108")
            ),
        ),
        task(
            8,
            "Spin wheel",
            "1.2.0 - Fix ads/Edit UI",
            created="2026-10-14",
            desc="Fix ads theo file mới, edit UI màn quay và màn kết quả.\n" + links("spinwheel-120"),
        ),
        task(
            9,
            "Auto click",
            "1.1.2 - Add tracking/Fix luồng",
            created="2026-10-15",
            desc="Thêm 8 event tracking, sửa luồng tạo kịch bản.\n" + links("autoclick-112"),
        ),
        task(
            10,
            "Lovetest",
            "1.0.8 - Fix ads/Fix luồng",
            created="2026-10-15",
            desc="Fix ads màn kết quả, đổi luồng onboarding 2 màn.\n" + links("lovetest-108"),
        ),
        task(
            11,
            "VPN",
            "1.1.8 - Fix IAP/Fix luồng",
            created="2026-10-16",
            desc="Fix restore purchase, bỏ màn intro thứ 2, cập nhật billing 7.\n" + links("vpn-118"),
        ),
        task(
            12,
            "live video 2",
            "1.0.9 - Edit UI",
            pri="low",
            created="2026-10-16",
            desc="Edit UI màn player trên tablet theo figma. https://www.figma.com/design/eval-lv2",
        ),
    ],
    "prev_rows": [
        task(1, "Phone Cleaner", "1.0.2 - Add ads/Add SDK", pic=f"{LINH}, {TIEN}", created="2026-10-05", status="done"),
        task(2, "PS Remote", "1.1.2 - Add feature/ Add ads", pic=MINH, created="2026-10-05", status="ready to release"),
        task(
            3,
            "Game Emulator",
            "Edit flow download/add flow auto scan game",
            pic=AN,
            created="2026-10-05",
            status="done",
        ),
    ],
    "size_target": {1: "S", 2: "M", 3: "L", 4: "XL", 5: "M", 6: "S", 7: "L", 8: "M", 9: "M", 10: "M", 11: "L", 12: "S"},
    # Processing order: 3 urgent, 4 high, then 5–11 by creation date and STT, 12 low. MinhNM is blocked throughout.
    "expect": {
        3: ("TiếnBV", ("LinhNV", "AnTD")),  # preference first (D32); cap 0+1 lets everyone in
        4: ("LinhNV", ("AnTD", "TiếnBV")),  # pin (D31)
        5: ("LinhNV", ("AnTD", "TiếnBV")),  # pin, beyond the cap
        6: ("AnTD", ("TiếnBV", "LinhNV")),  # cap 0+1 leaves only AnTD: TiếnBV preferred but capped, LinhNV capped
        7: ("AnTD", ("LinhNV", "TiếnBV")),  # expired rule does not block AnTD; AnTD on the latest Game Emulator
        8: ("LinhNV", ("TiếnBV",)),  # AnTD at 2 (max), MinhNM off; NamPV's preference cannot act
        9: ("LinhNV", ("TiếnBV",)),  # AnTD at max, MinhNM off; LinhNV built an older Auto click
        10: ("MinhNM", ("AnTD", "TiếnBV")),  # the rules leave nobody: relaxed (A31); MinhNM on the latest Lovetest
        11: ("TiếnBV", ("LinhNV",)),  # LinhNV capped (4 > 2+1); TiếnBV built an older VPN
        12: ("TiếnBV", ("LinhNV",)),  # TiếnBV on the latest live video 2
    },
    "findings": [  # DUE-MISSING added 2026-10-13 by D53
        ("RULE-DEV-UNAVAILABLE", None),
        ("RULE-NO-CANDIDATE", 10),
        ("DUE-MISSING", 3),
        ("DUE-MISSING", 4),
    ],
    "watch": [
        "STT 1 giao sẵn AR Dog cho TiếnBV dù luật chỉ định LinhNV: giữ nguyên (D10).",
        "STT 10: luật loại hết dev, A31 giao như không có luật Không giao/Tối đa đơn, nên MinhNM nhận đơn dù TM ghi "
        "'Minh làm MVP tuần đầu'. Xem cảnh báo có đủ rõ để TM sửa không.",
        "Luật 'Không giao AnTD · Game Emulator' hết hạn 17/10: có hiệu lực ngày chạy 16/10 nhưng không vào ngày áp "
        "luật 19/10 (A34).",
        "Dòng in ra phải là 8 luật, 7 có hiệu lực ngày 19/10/2026.",
    ],
}

# ---------------------------------------------------------------------------------------------------------------
# Case 5: dirty data and new apps. Header `App Name` without the dot, no previous sheet, names in NFD, lowercase,
# with double spaces and one typo, an unknown priority, a due date before creation, a `Bug` row, a text date.
# Loads after the pre-assigned orders: LinhNV 1, AnTD 1 (the typo'd TiếnBV order counts for nobody, D14).
# ---------------------------------------------------------------------------------------------------------------

LONG_DESC = "Chi tiết đơn liên hệ BA: Hoa\n" + "".join(
    f"{i}. Màn {i}: thêm nút lưu nhanh, hiển thị danh sách save state theo thời gian, cho phép đổi tên và xoá bản "
    f"save; đồng bộ khi có mạng. UI https://www.figma.com/design/eval-emu-save?node-id={i}-1 · SRS "
    f"https://docs.google.com/document/d/eval-emu-save-{i}/edit · Tracking "
    f"https://docs.google.com/spreadsheets/d/eval-emu-save-{i}/edit\n"
    for i in range(1, 21)
)

CASE_5 = {
    "slug": "case-5-du-lieu-ban",
    "title": "Dữ liệu bẩn, app mới",
    "today": "2026-10-16",
    "sprint": SPRINT_11,
    "prev": None,
    "app_header": "App Name",
    "devs": {},
    "rows": [
        task(
            1,
            "Phone Cleaner",
            "1.0.3 - Fix ANR màn dọn rác",
            created="2026-10-12",
            pic=unicodedata.normalize("NFD", "Ngọc  Văn Linh"),
            desc="Fix ANR khi quét thư mục lớn. https://console.firebase.google.com/u/0/project/eval-pc",
        ),
        sub(2, "1.0.3 - Fix ANR màn dọn rác", "Fix ANR", LINH),
        task(
            3,
            "Auto click",
            "1.1.2 - Add tracking/Edit UI",
            pic="trần đức an",
            created="2026-10-12",
            desc="Thêm 8 event tracking, edit UI màn setting.\n" + links("autoclick-112"),
        ),
        task(
            4,
            "live video 2",
            "1.0.9 - Fix ads",
            pic="Bùi Văn Tiếng",
            created="2026-10-12",
            desc="Đổi native full sang inter ở luồng xem video.",
        ),
        task(
            5,
            "QR Scanner",
            "1.0.0 - Init project/Add ads/Add IAP",
            pri="urgent",
            created="2026-10-13",
            desc=(
                "App mới. Splash, onboarding 3 màn, quét QR/barcode, lịch sử, tạo QR, setting; đủ bộ "
                "ads, IAP tuần/năm, "
                "tracking theo file.\n" + links("qr-100")
            ),
        ),
        task(
            6,
            "Weather Live",
            "1.0.0 - Init project/Add widget/Add ads",
            pri="Urgent",
            created="2026-10-13",
            desc=(
                "App mới. Màn thời tiết hiện tại, dự báo 7 ngày, bản đồ mưa, 3 widget màn hình chính, thông báo sáng; "
                "đủ bộ ads.\n" + links("weather-100")
            ),
        ),
        task(
            7,
            "Fake GPS",
            "1.0.1 - Fix policy location permission",
            pri="urgent",
            created="2026-10-13",
            desc="Google Play từ chối vì quyền vị trí nền: bỏ ACCESS_BACKGROUND_LOCATION, cập nhật privacy policy.",
        ),
        task(
            8,
            None,
            "Fix crash màn splash trên Android 14",
            pri="high",
            created="2026-10-14",
            desc="Crash khi mở app lần đầu trên Android 14 (ForegroundServiceStartNotAllowedException).",
        ),
        task(
            9,
            "Speaker Cleaner",
            "1.1.3 - Fix ads/Fix luồng",
            created="2026-10-14",
            desc="Fix ads màn kết quả, chuyển paywall sau màn dọn loa.\n" + links("speaker-113"),
        ),
        task(
            10,
            "ps remote",
            "1.1.3 - Fix crash kết nối",
            pri="gấp",
            created="2026-10-15",
            desc="Fix crash khi mất kết nối wifi giữa chừng. https://console.firebase.google.com/eval-psremote",
        ),
        task(
            11,
            "Nhiều App",
            "Fix policy native too small cho 6 app",
            created="2026-10-15",
            desc="Cố định template native cho 6 app theo file: https://docs.google.com/spreadsheets/d/eval-policy-6",
        ),
        task(
            12,
            "Game Emulator",
            "1.0.8 - Add feature save state/Add ads",
            due="2026-10-10",
            created="2026-10-15",
            desc=LONG_DESC,
        ),
        task(
            13,
            "VPN",
            "1.1.8 - Fix IAP",
            created="16/10/2026",
            desc="Fix restore purchase gói tuần sau khi khởi động lại app.",
        ),
        task(14, "VPN", "Crash khi xoay màn hình", created="2026-10-16", kind="Bug"),
    ],
    "size_target": {
        1: "S",
        3: "M",
        4: "S",
        5: "XL",
        6: "XL",
        7: "S",
        8: "S",
        9: "M",
        10: "S",
        11: "M",
        12: "XL",
        13: "M",
    },
    # Processing order: 5, 6, 7 urgent ("Urgent" is urgent); 8 high; 12 (due date) then 9, 10, 11, 13 normal.
    "expect": {
        5: ("MinhNM", ("LinhNV", "TiếnBV")),  # new app: LinhNV and MinhNM are middle+, MinhNM 0h < 16h
        6: ("LinhNV", ("MinhNM", "TiếnBV")),  # same seniority and load: higher level first
        7: ("MinhNM", ("LinhNV", "TiếnBV")),  # LinhNV capped (2 > 0+1); MinhNM is middle
        8: ("TiếnBV", ("LinhNV", "MinhNM")),  # no app = new app; middle+ devs capped; TiếnBV 0h < AnTD 16h
        12: ("AnTD", ("TiếnBV", "LinhNV")),  # AnTD on the latest Game Emulator
        9: ("LinhNV", ("MinhNM", "TiếnBV")),  # "Speaker Cleaner" is SpeakerCleaner (A10); LinhNV on the latest
        10: ("MinhNM", ("LinhNV", "TiếnBV")),  # "ps remote" is PS Remote; LinhNV capped; MinhNM on the latest
        11: ("AnTD", ("LinhNV", "MinhNM")),  # LinhNV, MinhNM capped (3 > 1+1); AnTD built an older Nhiều App
        13: ("TiếnBV", ("LinhNV", "MinhNM")),  # only TiếnBV under the cap; built an older VPN
    },
    "findings": [
        ("APP-MISSING", 8),
        ("PRIORITY-UNKNOWN", 10),
        ("DUE-BEFORE-CREATED", 12),
        ("TYPE-UNKNOWN", 14),
        ("PREV-SPRINT-MISSING", None),
        ("DUE-MISSING", 5),  # D53 (2026-10-13): urgent or high without Hạn
        ("DUE-MISSING", 6),
        ("DUE-MISSING", 7),
        ("DUE-MISSING", 8),
    ],
    "watch": [
        "STT 4 giao sẵn cho 'Bùi Văn Tiếng' (gõ sai tên TiếnBV): tool coi là người lạ, TiếnBV bị tính thiếu 1 đơn và "
        "không có cảnh báo nào (cái giá đã biết của D14).",
        "STT 1 tên dạng NFD có hai khoảng trắng, STT 3 viết thường: vẫn phải nhận ra LinhNV, AnTD (A10).",
        "STT 12 có mô tả khoảng 6.000 ký tự với 60 link: prompt phải cắt còn 600 ký tự và thay link bằng [link].",
        "Ba đơn urgent của app mới cùng lúc: hai middle+ nhận hai đơn, đơn thứ tư (high, không có app) rơi vào junior.",
    ],
}

SYNTHETIC = (CASE_3, CASE_4, CASE_5)
