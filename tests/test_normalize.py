from __future__ import annotations

from datetime import date, datetime

import pytest

from scrumbot.model import Level
from scrumbot.normalize import clean, header_key, parse_date, parse_level, text_key


def test_text_helpers_normalize_nfc_and_headers() -> None:
    assert clean("  Ngo\u0323c  Va\u0306n  Linh ") == "Ngọc Văn Linh"
    assert text_key("  LINH  ") == "linh"
    assert header_key(" App Name. ") == "app name"


def test_parse_level_and_dates() -> None:
    assert parse_level("MIDDLE+") is Level.MIDDLE_PLUS
    assert parse_level("other") is None
    assert parse_date(datetime(2026, 10, 6, 12)) == date(2026, 10, 6)
    assert parse_date("06/10/2026") == date(2026, 10, 6)
    with pytest.raises(ValueError, match="không đọc được ngày"):
        parse_date("tomorrow")
