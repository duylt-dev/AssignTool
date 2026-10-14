"""Raw `/api/doc/` replies into standard-input values (bot spec §2.5): names and statuses looked up, NFC text, times,
bugs, status history."""

from __future__ import annotations

import unicodedata
from datetime import date, datetime

import pytest

from scrumbot.core.errors import InputError
from scrumbot.input.dev_api.reader import read_changes, read_sprints, read_tasks
from tests.api_builders import LINH, OUTSIDER, history, item, orders, sprint, sprints


def test_tasks_carry_names_statuses_kinds_and_times() -> None:
    raw = orders(
        item(
            "r1",
            unicodedata.normalize("NFD", "1.0.1 - Thêm ads"),
            people=(LINH, OUTSIDER),
            priority="urgent",
            due=date(2026, 10, 10),
            hours=12,
            closed=datetime(2026, 10, 9, 18, 0),
        ),
        item("b1", parent="r1", bug=True, status="done"),
    )

    root, bug = read_tasks(raw, "L1")

    assert root.title == "1.0.1 - Thêm ads" and unicodedata.is_normalized("NFC", root.title)
    assert (root.assignees, root.status, root.status_kind, root.priority_raw) == (
        (LINH, OUTSIDER),
        "in progress",
        "custom",
        "urgent",
    )
    assert (root.due, root.hours, root.closed, root.is_bug, root.parent_id) == (
        date(2026, 10, 10),
        12.0,
        datetime(2026, 10, 9, 18, 0),
        False,
        "",
    )
    assert (bug.is_bug, bug.parent_id, bug.status_kind) == (True, "r1", "done")


def test_sprints_and_the_status_history_are_read_oldest_change_first() -> None:
    (found,) = read_sprints(sprints(sprint("S1", "Sprint 1 (10/6 - 10/17)", date(2026, 10, 6), date(2026, 10, 17))))
    changes = read_changes(
        history(
            ("a", "in progress", "release", datetime(2026, 10, 8, 9)),
            ("a", None, "in progress", datetime(2026, 10, 6, 9)),
        )
    )

    assert (found.id, found.kind, found.start, found.end, found.total) == (
        "S1",
        "sprint",
        date(2026, 10, 6),
        date(2026, 10, 17),
        1,
    )
    assert [(change.task_id, change.new) for change in changes] == [("a", "in progress"), ("a", "release")]


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        ({"ok": True, "sprints": "x"}, "Dữ liệu API không đúng dạng (sprints): 'sprints' không phải danh sách."),
        ({"ok": True, "sprints": [{"ten": "Sprint 1"}]}, "Dữ liệu API không đúng dạng (sprints): thiếu 'id'."),
        (
            {"ok": True, "sprints": [{"id": "a", "bat_dau": "06/10/2026"}]},
            "Dữ liệu API không đúng dạng (sprints): không đọc được thời gian '06/10/2026'.",
        ),
    ],
)
def test_a_reply_in_the_wrong_shape_is_an_input_error(raw: dict, message: str) -> None:
    with pytest.raises(InputError) as caught:
        read_sprints(raw)
    assert str(caught.value) == message


def test_an_item_without_a_creation_time_is_an_input_error() -> None:
    raw = orders(item("x"))
    raw["don"][0]["ngay_tao"] = None
    with pytest.raises(InputError, match="đơn 'x' thiếu 'ngay_tao'"):
        read_tasks(raw, "L1")
