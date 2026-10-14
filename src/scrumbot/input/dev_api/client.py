"""GET calls to the internal system's read-only API `/api/doc/` (bot spec §2.2, A55). The only module that does
HTTP. The token goes in one header and nowhere else: not in messages, logs or stored files."""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable

from scrumbot import __version__
from scrumbot.core.errors import AssignError
from scrumbot.input.dev_api.config import ApiConfig

TIMEOUT = 60
RETRY_WAIT = 30
RETRIES = 3
PAGE_ROOTS = "goc_moi_trang"
HISTORY_BATCH = 50

_LOGGER = logging.getLogger(__name__)


class ApiError(AssignError):
    """The API refused or failed a call (bot spec §2.2); exit code 2, no report."""


class ApiClient:
    def __init__(self, config: ApiConfig, *, sleep: Callable[[float], None] = time.sleep) -> None:
        self._config = config
        self._sleep = sleep

    @property
    def host(self) -> str:
        return self._config.host

    def get(self, path: str, **params: object) -> dict[str, object]:
        """One GET; `429` waits and retries (A55); any other failure raises ApiError with a Vietnamese message."""
        url = f"{self._config.base}/api/doc/{path}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self._config.token}",
                "User-Agent": f"scrumbot/{__version__}",
                "Accept": "application/json",
            },
        )
        for attempt in range(RETRIES + 1):
            _LOGGER.debug("GET /api/doc/%s %s", path, params)
            try:
                with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                    body = response.read()
            except urllib.error.HTTPError as error:
                if error.code == 429 and attempt < RETRIES:
                    self._sleep(RETRY_WAIT)
                    continue
                raise ApiError(_http_message(error.code, path)) from None
            except (urllib.error.URLError, TimeoutError, OSError) as error:
                reason = getattr(error, "reason", error)
                raise ApiError(f"Không gọi được API {self._config.host}: {reason}.") from None
            return _json(body, path)
        raise ApiError(_http_message(429, path))  # unreachable: the last attempt raises above

    def sprints(self, folder_id: str) -> dict[str, object]:
        return self.get("sprints", folder_id=folder_id)

    def orders(self, list_id: str) -> dict[str, object]:
        """Every page of `don` merged into one reply (bot spec §2.2)."""
        page = 1
        merged: dict[str, object] = {}
        while True:
            reply = self.get("don", list_id=list_id, trang=page)
            if not merged:
                merged = {**reply, "don": list(_list(reply, "don", path="don"))}
            else:
                merged["don"] = [*merged["don"], *_list(reply, "don", path="don")]  # type: ignore[misc]
                merged["trang_thai"] = _union(merged, reply, "trang_thai")
                merged["nguoi"] = _union(merged, reply, "nguoi")
            per_page, total = reply.get(PAGE_ROOTS), reply.get("tong_goc")
            if not isinstance(per_page, int) or not isinstance(total, int) or per_page <= 0 or page * per_page >= total:
                return merged
            page += 1

    def history(self, ids: list[str]) -> dict[str, object]:
        """The status changes of `lich-su`, in batches of 50 ids, merged (bot spec §2.2)."""
        changes: list[object] = []
        for start in range(0, len(ids), HISTORY_BATCH):
            reply = self.get("lich-su", task_id=",".join(ids[start : start + HISTORY_BATCH]))
            changes.extend(_list(reply, "doi_trang_thai", path="lich-su"))
        return {"doi_trang_thai": changes}


def _http_message(code: int, path: str) -> str:
    if code == 401:
        return "API từ chối token (401). Kiểm tra SCRUMBOT_API_TOKEN, hoặc xin TM token mới."
    if code == 404:
        return f"API trả 404 cho {path}: API đang tắt trên server hoặc id không còn trong phạm vi."
    if code == 429:
        return "API vẫn giới hạn tải (429) sau 3 lần thử; chạy lại sau ít phút."
    if 500 <= code < 600:
        return f"API lỗi phía server ({code}) ở {path}; thử lại sau."
    return f"API trả mã {code} ở {path}."


def _json(body: bytes, path: str) -> dict[str, object]:
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ApiError(f"API trả dữ liệu không đọc được ở {path}.") from None
    if not isinstance(value, dict) or value.get("ok") is False:
        raise ApiError(f"API trả dữ liệu không đọc được ở {path}.")
    return value


def _list(reply: dict[str, object], key: str, *, path: str) -> list[object]:
    value = reply.get(key, [])
    if not isinstance(value, list):
        raise ApiError(f"API trả dữ liệu không đọc được ở {path}.")
    return value


def _union(first: dict[str, object], second: dict[str, object], key: str) -> list[object]:
    """Lookup tables (`trang_thai`, `nguoi`) of two pages, each id once."""
    seen: dict[object, object] = {}
    for item in [*_list(first, key, path="don"), *_list(second, key, path="don")]:
        if isinstance(item, dict):
            seen.setdefault(item.get("id"), item)
    return list(seen.values())
