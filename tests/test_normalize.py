from __future__ import annotations

from datetime import date, datetime

import pytest

from scrumbot.model import Level
from scrumbot.normalize import clean, header_key, parse_date, parse_level, split_people, text_key


def test_text_helpers_normalize_nfc_and_headers() -> None:
    assert clean("  Ngo\u0323c  Va\u0306n  Linh ") == "Ngọc Văn Linh"
    assert text_key("  LINH  ") == "linh"
    assert header_key(" App Name. ") == "app name"
    assert split_people(" A,  B ,, ") == ("A", "B")


def test_parse_level_and_dates() -> None:
    assert parse_level("MIDDLE+") is Level.MIDDLE_PLUS
    assert parse_level("other") is None
    assert parse_date(datetime(2026, 10, 6, 12)) == date(2026, 10, 6)
    assert parse_date("06/10/2026") == date(2026, 10, 6)
    with pytest.raises(ValueError, match="không đọc được ngày"):
        parse_date("tomorrow")


def test_parse_sprint_labels_reads_every_label_and_dates_it_from_the_filing_day() -> None:
    from scrumbot.model import SprintLabel
    from scrumbot.normalize import parse_sprint_labels

    labels = parse_sprint_labels("Sprint 18 (4/17 - 4/29), Sprint 19 (5/6-5/20)", date(2026, 4, 16))
    assert labels == (
        SprintLabel(18, date(2026, 4, 17), date(2026, 4, 29)),
        SprintLabel(19, date(2026, 5, 6), date(2026, 5, 20)),
    )
    assert labels[0].name == "Sprint 18 (4/17 - 4/29)"
    # Across New Year: filed in January for a sprint that started in December, and the reverse.
    assert parse_sprint_labels("Sprint 1 (12/29 - 1/9)", date(2027, 1, 2)) == (
        SprintLabel(1, date(2026, 12, 29), date(2027, 1, 9)),
    )
    assert parse_sprint_labels("Sprint 2 (1/5 - 1/16)", date(2026, 12, 20))[0].start == date(2027, 1, 5)
    # The same number on two boards stays two different sprints (A21).
    assert SprintLabel(1, date(2026, 5, 22), date(2026, 6, 5)) != SprintLabel(1, date(2026, 5, 22), date(2026, 7, 15))
    assert parse_sprint_labels("", date(2026, 1, 1)) == ()
    assert parse_sprint_labels("Sprint 3 (2/30 - 3/10), Backlog", date(2026, 2, 1)) == ()
