# Hướng dẫn dùng API chỉ đọc `/api/doc/`

> **Ghi chú của repo `scrumbot` (2026-10-13, `confirm.md` A63).** Tài liệu dưới đây là bản TM gửi, giữ nguyên văn.
> Điều đo được khi gọi thử, khác với tài liệu:
>
> - Token hiện chỉ chạy trên server **dev** `https://devclickup.datlt.site`; production trả `401` ở mọi đường dẫn
>   `/api/doc/`. Bot chỉ đọc dev và từ chối địa chỉ production (D49, A64).
> - Ví dụ Python ở mục 8 chạy nguyên văn sẽ bị Cloudflare chặn (`403`, mã `1010`) vì User-Agent mặc định của `urllib`.
>   Thêm `"User-Agent": "..."` vào header; bot gửi `User-Agent: scrumbot/<version>` (A55).
> - API không trả mô tả đơn; bot ước lượng theo tiêu đề (D50). Đã nhờ TM thêm trường `mo_ta`.
> - Trường `ngay_dong` gần như luôn trống (5/350 đơn gốc Tech manager); thời điểm xong lấy từ `/lich-su` (A74).
> - Cấu hình của bot: `SCRUMBOT_API_TOKEN`, `SCRUMBOT_API_BASE` trong `.env` (A54), không phải `DOC_TOKEN`, `DOC_BASE`.

Tài liệu cho người viết tool phân tích nhân sự gọi vào Dev Sprint. Phần thiết kế, ràng buộc
bảo mật và triển khai server nằm ở `KE_HOACH_API_DOC.md`.

## Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [Xác thực](#2-xác-thực)
3. [Quy ước chung](#3-quy-ước-chung)
4. [API `sprints`](#4-get-apidocsprints)
5. [API `don`](#5-get-apidocdon)
6. [API `lich-su`](#6-get-apidoclich-su)
7. [Mã lỗi](#7-mã-lỗi)
8. [Ví dụ Python đầy đủ](#8-ví-dụ-python-đầy-đủ)
9. [Gọi nhanh bằng curl](#9-gọi-nhanh-bằng-curl)
10. [Quản lý token](#10-quản-lý-token)
11. [Xử lý sự cố](#11-xử-lý-sự-cố)

---

## 1. Tổng quan

| Mục | Giá trị |
|---|---|
| Địa chỉ | `https://circle.datlt.site` (production), `https://devclickup.datlt.site` (dev) |
| Tiền tố | `/api/doc/` |
| Method | Chỉ `GET`. Mọi method khác trả `405` |
| Định dạng | JSON, UTF-8 |
| Quyền | **Chỉ đọc**. API không ghi, không sửa, không gửi thông báo, không gọi Jenkins |
| Phạm vi | Folder **Maintain update** (`90169740714`, kể cả folder con) và list **Tech manager** (`901609972453`) |
| Giới hạn | 120 request / phút |

Ba API:

| API | Dùng để |
|---|---|
| `GET /api/doc/sprints?folder_id=` | Danh sách sprint của một folder, ngày bắt đầu / kết thúc, tiến độ |
| `GET /api/doc/don?list_id=&trang=` | Đơn của một sprint / list kèm cây con (subtask, bug), người làm, trạng thái, App, hạn, ước lượng |
| `GET /api/doc/lich-su?task_id=` | Lịch sử đổi trạng thái và mốc comment (ai, lúc nào) của tối đa 50 đơn |

**API không trả**: mô tả đơn, nội dung comment, tên thread, email, ảnh đại diện, vai trò, link
(link trong tên đơn bị thay bằng `[link]`), thông tin build / Jenkins, chủ đề thảo luận, space
Dự án, đơn trong thùng rác.

---

## 2. Xác thực

Mọi request gửi token qua header:

```
Authorization: Bearer <token>
```

- Không nhận token qua query string, cookie hay form.
- Token **chỉ** dùng được cho `/api/doc/`. Gọi trang web hay API khác bằng token này vẫn bị đòi
  đăng nhập Google.
- Server chỉ giữ mã băm SHA-256 của token. Mất token thì không lấy lại được, phải tạo token mới
  (xem [mục 10](#10-quản-lý-token)).

**Giữ token an toàn ở phía tool:**

- Đọc token từ biến môi trường hoặc kho bí mật, không ghi thẳng vào code, không commit lên git.
- Không in token ra log, không gửi qua chat / email.
- Mỗi môi trường (dev, production) dùng token riêng.

---

## 3. Quy ước chung

**Thời gian** — chuỗi `"YYYY-MM-DD HH:MM:SS"`, theo giờ của máy chủ (cùng giờ hiển thị trên web).
Ví dụ `"2026-10-06 10:43:40"`. Đọc bằng Python: `datetime.strptime(s, "%Y-%m-%d %H:%M:%S")`.

**Giá trị trống** — trường không có dữ liệu trả `null` (không trả chuỗi rỗng).

**Id** — đơn, list, folder là **chuỗi** (`"86czu9h9w"`, `"n_663e74c178"`). Người dùng và trạng
thái là **số** (`55521140`, `684`). Id bắt đầu bằng `n_` là đơn / list tạo trong Dev Sprint; còn
lại là id cũ từ ClickUp.

**Bảng tra cứu** — `don` trả id trạng thái và id người; tên nằm ở mảng `trang_thai` và `nguoi` đi
kèm trong cùng phản hồi. Hai mảng này chỉ chứa những mục xuất hiện trong phản hồi đó.

**Ngoài phạm vi** — id không tồn tại, đã xoá hay nằm ngoài phạm vi đều cho cùng một kết quả
(`404` hoặc nằm trong `khong_thay`). API cố ý không phân biệt.

**Phản hồi lỗi** — `{"ok": false}`, không kèm lý do; xem mã HTTP để biết loại lỗi. Riêng đường
dẫn không tồn tại (`404`) và tham số sai kiểu (`422`) trả dạng mặc định `{"detail": ...}`.

---

## 4. `GET /api/doc/sprints`

Danh sách sprint / list nằm **thẳng** trong một folder (không gồm list trong folder con).

### Tham số

| Tham số | Bắt buộc | Mô tả |
|---|---|---|
| `folder_id` | Có | Id folder trong phạm vi, vd `90169740714` |

### Phản hồi

```json
{
  "ok": true,
  "sprints": [
    {
      "id": "n_663e74c178",
      "ten": "Sprint 10 (10/6 - 10/17)",
      "kieu": "sprint",
      "bat_dau": "2026-10-06 00:00:00",
      "ket_thuc": "2026-10-17 23:59:59",
      "luu_tru": false,
      "tong": 6,
      "xong": 0
    }
  ]
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | chuỗi | Id list, dùng cho `/don?list_id=` |
| `ten` | chuỗi | Tên sprint |
| `kieu` | chuỗi | `sprint` hoặc `list` |
| `bat_dau`, `ket_thuc` | thời gian / null | Ngày bắt đầu, kết thúc sprint |
| `luu_tru` | bool | Sprint đã lưu trữ |
| `tong` | số | Số **đơn gốc loại task** trong sprint (không tính subtask, bug) |
| `xong` | số | Trong `tong`, số đơn có trạng thái kiểu `done` / `closed` |

**Lưu ý**: thứ tự trả về theo thứ tự sắp xếp trên web, **không phải** theo thời gian. Muốn tìm
sprint mới nhất / đang chạy thì tự sắp theo `bat_dau`.

---

## 5. `GET /api/doc/don`

Đơn của một sprint / list, gồm cả đơn được kéo từ list khác vào (vd đơn của Tech manager kéo vào
sprint), kèm **toàn bộ cây con** ở mọi cấp: subtask và bug.

### Tham số

| Tham số | Bắt buộc | Mô tả |
|---|---|---|
| `list_id` | Có | Id sprint / list trong phạm vi (lấy từ `/sprints`, hoặc `901609972453` cho Tech manager) |
| `trang` | Không | Số trang, bắt đầu từ `1` (mặc định `1`) |

### Phân trang

Phân trang theo **đơn gốc**: mỗi trang tối đa `goc_moi_trang` (500) đơn gốc, cây con của gốc nào
đi cùng trang của gốc đó — nên số phần tử trong `don` có thể lớn hơn 500 nhiều.

Đọc hết: gọi `trang = 1, 2, 3...` cho tới khi `trang * goc_moi_trang >= tong_goc`. Gọi quá trang
cuối trả `don: []`.

Sprint thường chỉ có 1 trang. Tech manager hiện khoảng 350 gốc / 5.800 đơn, vẫn 1 trang (~2 MB).

### Phản hồi

```json
{
  "ok": true,
  "trang": 1,
  "goc_moi_trang": 500,
  "tong_goc": 6,
  "don": [
    {
      "id": "n_00d9cf6005",
      "ten": "1.0.2 - Add ads/Add SDK",
      "cha_id": null,
      "loai": "task",
      "trang_thai_id": 668,
      "nguoi_lam_ids": [88902387, 294737337],
      "uu_tien": null,
      "bat_dau": null,
      "han": null,
      "uoc_luong_gio": null,
      "app": "Phone Cleaner",
      "nguoi_tao_id": 89058510,
      "ngay_tao": "2026-10-05 11:58:14",
      "ngay_cap_nhat": "2026-10-06 10:36:31",
      "ngay_dong": null,
      "list_nha_id": "901609972453",
      "bug_mo": 0,
      "bug_tong": 0
    }
  ],
  "trang_thai": [
    {"id": 666, "ten": "all issue", "kieu": "open"},
    {"id": 668, "ten": "ready to progress", "kieu": "custom"},
    {"id": 669, "ten": "in progress", "kieu": "custom"}
  ],
  "nguoi": [
    {"id": 88902387, "ten": "..."}
  ]
}
```

### Trường của mỗi đơn

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | chuỗi | Id đơn, dùng cho `/lich-su` |
| `ten` | chuỗi | Tên đơn; link trong tên đã bị thay bằng `[link]` |
| `cha_id` | chuỗi / null | Đơn cha. `null` = đơn gốc. Có giá trị = subtask hoặc bug của đơn đó |
| `loai` | chuỗi | `task` (kể cả subtask) hoặc `bug` |
| `trang_thai_id` | số / null | Tra tên ở mảng `trang_thai` |
| `nguoi_lam_ids` | mảng số | Người được giao; tra tên ở mảng `nguoi`. Có thể rỗng |
| `uu_tien` | chuỗi / null | `urgent`, `high`, `normal`, `low` |
| `bat_dau` | thời gian / null | Ngày bắt đầu |
| `han` | thời gian / null | Hạn hoàn thành |
| `uoc_luong_gio` | số / null | Ước lượng, đơn vị **giờ** |
| `app` | chuỗi / null | Giá trị field App Name |
| `nguoi_tao_id` | số / null | Người tạo đơn |
| `ngay_tao`, `ngay_cap_nhat`, `ngay_dong` | thời gian / null | Ngày tạo, cập nhật gần nhất, đóng |
| `list_nha_id` | chuỗi | List gốc của đơn. Khác `list_id` đang hỏi = đơn được kéo từ list khác vào |
| `bug_mo` | số | Số bug **chưa xong** trong cả cây con của đơn |
| `bug_tong` | số | Tổng số bug trong cả cây con |

### Trạng thái

| Trường | Mô tả |
|---|---|
| `id` | Id trạng thái |
| `ten` | Tên hiển thị trên web, vd `in progress`, `qa - testing` |
| `kieu` | `open` (mới), `custom` (đang xử lý), `done` / `closed` (đã xong) |

Coi một đơn **đã xong** khi `kieu` là `done` hoặc `closed` — cùng cách web tính tiến độ.

### Lưu ý

- Đơn gốc trong một sprint có thể có `cha_id` khác `null` nếu cha của nó không nằm trong sprint
  đó; khi ấy cha **không** có trong `don`.
- Một đơn có thể nằm ở nhiều sprint (kéo vào nhiều nơi); gọi nhiều sprint thì gộp theo `id`.

---

## 6. `GET /api/doc/lich-su`

Lịch sử đổi trạng thái và mốc comment của nhiều đơn trong một lần gọi.

### Tham số

| Tham số | Bắt buộc | Mô tả |
|---|---|---|
| `task_id` | Có | Id đơn, cách nhau dấu phẩy, **tối đa 50** id. Id trùng được gộp |

### Phản hồi

```json
{
  "ok": true,
  "khong_thay": [],
  "doi_trang_thai": [
    {
      "task_id": "n_e9b9a11e69",
      "tu": "ready to progress",
      "den": "in progress",
      "luc": "2026-10-06 10:43:40",
      "nguoi_id": 312627624
    }
  ],
  "comment": [
    {
      "task_id": "n_1fe10ee69f",
      "nguoi_id": 55521140,
      "luc": "2026-09-27 19:13:51",
      "trong_thread": false
    }
  ],
  "nguoi": [
    {"id": 55521140, "ten": "..."}
  ]
}
```

| Trường | Mô tả |
|---|---|
| `khong_thay` | Id không có, đã xoá hoặc ngoài phạm vi |
| `doi_trang_thai[].tu` | Trạng thái cũ (**tên**). `null` = lúc tạo đơn |
| `doi_trang_thai[].den` | Trạng thái mới (**tên**) |
| `doi_trang_thai[].luc` | Thời điểm đổi |
| `doi_trang_thai[].nguoi_id` | Người đổi; có thể `null` với dữ liệu cũ |
| `comment[].nguoi_id`, `luc` | Ai comment, lúc nào. **Không có nội dung comment** |
| `comment[].trong_thread` | `true` = tin trả lời trong một thread |
| `nguoi` | Tên của mọi người xuất hiện ở trên. Id `-1` là bot CI (`Beaver CI Bot`) |

Cả hai mảng sắp theo thứ tự xảy ra (cũ trước, mới sau). Lịch sử trạng thái ghi theo **tên**
trạng thái lúc đổi, nên tên có thể khác tên hiện tại nếu trạng thái từng bị đổi tên.

Đơn cũ nhập từ ClickUp có thể không có lịch sử trạng thái; khi đó dùng `ngay_tao` /
`ngay_cap_nhat` từ `/don`.

---

## 7. Mã lỗi

| Mã | Khi nào | Tool nên làm gì |
|---|---|---|
| `200` | Thành công | |
| `400` | `/lich-su` không có id hoặc quá 50 id | Chia lô 50 id |
| `401` | Thiếu token, sai token, sai dạng header | Kiểm tra token / header `Authorization: Bearer ...` |
| `404` | API đang tắt trên server, đường dẫn sai, id không có hoặc ngoài phạm vi | Kiểm tra id; nếu mọi API đều 404 thì API đang tắt |
| `405` | Dùng method khác `GET` | Chỉ dùng `GET` |
| `422` | Tham số sai kiểu, vd `trang=abc` | Sửa tham số |
| `429` | Quá 120 request / phút | Chờ 30–60 giây rồi gọi lại |
| `500` | Lỗi phía server | Thử lại sau; báo quản trị kèm thời điểm gọi |

---

## 8. Ví dụ Python đầy đủ

Chỉ dùng thư viện chuẩn (không cần `pip install`). Chạy:

```bash
DOC_TOKEN="<token>" DOC_BASE="https://circle.datlt.site" python3 vi_du_api_doc.py
```

```python
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

BASE = os.environ.get("DOC_BASE", "https://circle.datlt.site")
TOKEN = os.environ["DOC_TOKEN"]          # không ghi token thẳng vào code
FOLDER_MAINTAIN = "90169740714"
LIST_TECH_MANAGER = "901609972453"


def goi(duong_dan, **tham_so):
    """GET một API, trả JSON. Gặp 429 thì chờ rồi thử lại."""
    url = BASE + duong_dan + "?" + urllib.parse.urlencode(tham_so)
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + TOKEN})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(30)
                continue
            raise
    raise RuntimeError("Vẫn bị giới hạn tải sau 3 lần thử")


def tat_ca_don(list_id):
    """Gom mọi trang của /don thành một kết quả."""
    trang, don, trang_thai, nguoi = 1, [], {}, {}
    while True:
        d = goi("/api/doc/don", list_id=list_id, trang=trang)
        don += d["don"]
        trang_thai.update({s["id"]: s for s in d["trang_thai"]})
        nguoi.update({u["id"]: u["ten"] for u in d["nguoi"]})
        if trang * d["goc_moi_trang"] >= d["tong_goc"]:
            return don, trang_thai, nguoi
        trang += 1


def lich_su(task_ids):
    """Gọi /lich-su theo lô 50 id."""
    gop = {"doi_trang_thai": [], "comment": [], "nguoi": {}}
    for i in range(0, len(task_ids), 50):
        d = goi("/api/doc/lich-su", task_id=",".join(task_ids[i:i + 50]))
        gop["doi_trang_thai"] += d["doi_trang_thai"]
        gop["comment"] += d["comment"]
        gop["nguoi"].update({u["id"]: u["ten"] for u in d["nguoi"]})
    return gop


def sprint_hien_tai():
    bay_gio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ds = goi("/api/doc/sprints", folder_id=FOLDER_MAINTAIN)["sprints"]
    dang_chay = [s for s in ds if s["bat_dau"] and s["ket_thuc"]
                 and s["bat_dau"] <= bay_gio <= s["ket_thuc"]]
    if dang_chay:
        return dang_chay[0]
    # không sprint nào chứa hôm nay: lấy sprint bắt đầu gần nhất
    return max((s for s in ds if s["bat_dau"]), key=lambda s: s["bat_dau"])


if __name__ == "__main__":
    sp = sprint_hien_tai()
    print("Sprint:", sp["ten"], "- xong %d/%d" % (sp["xong"], sp["tong"]))

    don, trang_thai, nguoi = tat_ca_don(sp["id"])

    # 1) Mỗi người đang làm bao nhiêu đơn chưa xong
    dem = {}
    for d in don:
        kieu = trang_thai.get(d["trang_thai_id"], {}).get("kieu")
        if d["loai"] == "task" and kieu not in ("done", "closed"):
            for uid in d["nguoi_lam_ids"]:
                dem[nguoi.get(uid, uid)] = dem.get(nguoi.get(uid, uid), 0) + 1
    print("Đơn chưa xong theo người:", dem)

    # 2) Đơn chưa xong đứng yên một trạng thái quá 3 ngày
    chua_xong = [d for d in don if trang_thai.get(d["trang_thai_id"], {}).get("kieu")
                 not in ("done", "closed")]
    ls = lich_su([d["id"] for d in chua_xong])
    lan_cuoi = {}
    for h in ls["doi_trang_thai"]:
        lan_cuoi[h["task_id"]] = h["luc"]
    for d in chua_xong:
        moc = lan_cuoi.get(d["id"]) or d["ngay_tao"]
        so_ngay = (datetime.now() - datetime.strptime(moc, "%Y-%m-%d %H:%M:%S")).days
        if so_ngay > 3:
            print("Kẹt %d ngày: %s [%s]" % (so_ngay, d["ten"],
                                            trang_thai[d["trang_thai_id"]]["ten"]))

    # 3) Ai đã làm app nào (từ list Tech manager)
    tm, _, nguoi_tm = tat_ca_don(LIST_TECH_MANAGER)
    app_cua = {}
    for d in tm:
        if d["app"]:
            for uid in d["nguoi_lam_ids"]:
                app_cua.setdefault(nguoi_tm.get(uid, uid), set()).add(d["app"])
    print("Số app mỗi người từng làm:", {k: len(v) for k, v in app_cua.items()})
```

Kết quả mẫu:

```
Sprint: Sprint 10 (10/6 - 10/17) - xong 0/6
Đơn chưa xong theo người: {'Ngọc Văn Linh': 9, 'Bùi Văn Tiến': 4, 'Trần Đức An': 2, ...}
Kẹt 7 ngày: 1.0.2 - Add ads/Add SDK [ready to progress]
...
Số app mỗi người từng làm: {'Lục Tiến Đạt': 39, 'Trịnh Thị Thơ': 29, ...}
```

**Gợi ý cho tool:**

- Kiểm tra "BA đã trả lời chưa": so `luc` comment cuối của BA (theo `nguoi_id`) với comment cuối
  của dev trên cùng đơn.
- Đơn sắp trễ hạn: `han` gần hôm nay và trạng thái chưa `done` / `closed`.
- Gọi `/don` một lần cho mỗi sprint, gom id rồi gọi `/lich-su` theo lô 50 — đừng gọi từng đơn.
- Lưu kết quả vào bộ nhớ đệm của tool; không cần gọi lại nhiều lần trong vài phút.

---

## 9. Gọi nhanh bằng curl

Nhập token (zsh, không hiện ra màn hình) và địa chỉ:

```bash
read -s "DOC_TOKEN?Token: " && echo
```

```bash
B="https://circle.datlt.site"
```

Sprint của Maintain update:

```bash
curl -s -H "Authorization: Bearer $DOC_TOKEN" "$B/api/doc/sprints?folder_id=90169740714" | jq
```

Lấy sprint mới nhất có đơn:

```bash
SPRINT=$(curl -s -H "Authorization: Bearer $DOC_TOKEN" "$B/api/doc/sprints?folder_id=90169740714" | jq -r '.sprints | map(select(.tong > 0)) | sort_by(.bat_dau) | last | .id') && echo "$SPRINT"
```

Đơn của sprint đó:

```bash
curl -s -H "Authorization: Bearer $DOC_TOKEN" "$B/api/doc/don?list_id=$SPRINT" | jq
```

Số đơn theo người:

```bash
curl -s -H "Authorization: Bearer $DOC_TOKEN" "$B/api/doc/don?list_id=$SPRINT" | jq '(.nguoi | map({key: (.id | tostring), value: .ten}) | from_entries) as $ten | [.don[] | select(.loai == "task") | .nguoi_lam_ids[]] | group_by(.) | map({nguoi: $ten[.[0] | tostring], so_don: length}) | sort_by(-.so_don)'
```

Tech manager:

```bash
curl -s -H "Authorization: Bearer $DOC_TOKEN" "$B/api/doc/don?list_id=901609972453&trang=1" | jq '{tong_goc, goc_moi_trang, so_don: (.don | length)}'
```

Lịch sử của 10 đơn đầu trong sprint:

```bash
TASKS=$(curl -s -H "Authorization: Bearer $DOC_TOKEN" "$B/api/doc/don?list_id=$SPRINT" | jq -r '[.don[:10][].id] | join(",")')
```

```bash
curl -s -H "Authorization: Bearer $DOC_TOKEN" "$B/api/doc/lich-su?task_id=$TASKS" | jq
```

---

## 10. Quản lý token

Token cấu hình bằng biến môi trường trên server (cPanel › Setup Python App), không có trang quản
lý trên web.

| Việc | Cách làm |
|---|---|
| Tạo token | Trên máy cá nhân chạy lệnh dưới. Dòng 1 = token (cất vào tool), dòng 2 = mã băm |
| Đặt token cho server | Đặt dòng 2 vào biến `API_DOC_TOKEN_SHA256`, bấm Save rồi Restart app |
| Đổi token (nghi bị lộ, đổi định kỳ) | Tạo token mới, thay mã băm, Restart. Token cũ hết hiệu lực ngay |
| Tắt API | Xoá biến `API_DOC_TOKEN_SHA256`, Restart. Mọi `/api/doc/` trả `404` |
| Xem ai đang gọi | Log app (`stderr.log`): mỗi lượt một dòng `[api-doc] <IP> GET <đường dẫn> <mã> <thời gian>`. Token không bao giờ bị ghi vào log |

```bash
python3 -c "import secrets,hashlib;t=secrets.token_urlsafe(32);print(t);print(hashlib.sha256(t.encode()).hexdigest())"
```

Hiện mỗi server có **một** token.

---

## 11. Xử lý sự cố

| Hiện tượng | Nguyên nhân thường gặp | Cách xử lý |
|---|---|---|
| Mọi API đều `404` | API đang tắt (thiếu biến môi trường) | Quản trị xem log khởi động: `grep "api-doc" stderr.log` → dòng `tat (...)` ghi lý do |
| `401` dù token đúng | Mã băm trên server không khớp token; hoặc thiếu chữ `Bearer `; hoặc máy chủ web không chuyển header `Authorization` vào app | Tạo lại cặp token / mã băm; kiểm tra header; xem `KE_HOACH_API_DOC.md` mục xử lý sự cố |
| Mở link trên trình duyệt ra `{"ok": false}` | Trình duyệt không gửi header token | Bình thường — dùng curl, Postman hoặc code |
| `404` với một sprint / đơn cụ thể | Id sai hoặc nằm ngoài Maintain update / Tech manager | Lấy id từ `/sprints` và `/don` |
| Id nằm trong `khong_thay` | Đơn đã xoá, không tồn tại, hoặc ngoài phạm vi | Bỏ qua id đó |
| `429` | Gọi quá 120 lần / phút | Chờ rồi gọi lại; gom lô `/lich-su` 50 id |
| `500` | Lỗi phía server | Quản trị xem `grep "api-doc] loi" stderr.log` |
| Thiếu lịch sử trạng thái của đơn cũ | Đơn nhập từ ClickUp không có lịch sử | Dùng `ngay_tao` / `ngay_cap_nhat` |