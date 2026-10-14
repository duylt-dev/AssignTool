"""The dev API's configuration (bot spec §2.1, A54, A64): the token and the base from the environment and `.env`,
and the ids of board Maintain on the system. Never logs the token."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from scrumbot.core.errors import InputError

TOKEN_KEY = "SCRUMBOT_API_TOKEN"
BASE_KEY = "SCRUMBOT_API_BASE"
PRODUCTION_HOST = "circle.datlt.site"
MAINTAIN_FOLDER = "90169740714"  # folder "Maintain update": its lists are the sprints (docs/api-doc-he-thong.md §1)
TECH_MANAGER_LIST = "901609972453"  # list "Tech manager": history only (bot spec §2.5)


@dataclass(frozen=True, slots=True)
class ApiConfig:
    base: str  # "https://devclickup.datlt.site", no trailing slash
    token: str = field(repr=False)  # never printed, even in a traceback of the dataclass

    @property
    def host(self) -> str:
        return urlparse(self.base).hostname or self.base


def load_config(environ: Mapping[str, str], env_file: Path) -> ApiConfig:
    """The environment wins over `.env`; spaces around `=` and quotes around the value are accepted (A54)."""
    values = {**_read_env_file(env_file), **{key: environ[key] for key in (TOKEN_KEY, BASE_KEY) if key in environ}}
    token = values.get(TOKEN_KEY, "").strip()
    base = values.get(BASE_KEY, "").strip().rstrip("/")
    if not token:
        raise InputError(f"Thiếu {TOKEN_KEY} (trong .env hoặc biến môi trường).")
    if not base:
        raise InputError(f"Thiếu {BASE_KEY} (trong .env hoặc biến môi trường), ví dụ https://devclickup.datlt.site.")
    host = (urlparse(base).hostname or "").casefold()
    if host == PRODUCTION_HOST or host.endswith("." + PRODUCTION_HOST):
        raise InputError(f"{BASE_KEY} trỏ tới production ({PRODUCTION_HOST}); bot chỉ đọc server dev (confirm.md D49).")
    return ApiConfig(base, token)


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as error:
        raise InputError(f"Không đọc được file '{path}': {error}") from error
    values: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values
