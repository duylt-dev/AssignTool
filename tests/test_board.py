"""From API values to the rules' inputs (bot spec §2.3, §2.5): which sprint runs, its orders, history, backlog."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from scrumbot.errors import InputError, NoRunningSprint
from scrumbot.model_board import TECH_MANAGER_LIST, Board
from scrumbot.rules.board import (
    API_HEADERS,
    empty_backlog,
    history_orders,
    maintain_sprints,
    newest_update,
    previous_of,
    select_current,
    sprint_sheet,
)
from scrumbot.sources.api_reader import read_board, read_sprints
from tests.api_builders import AN, LINH, item, orders, sprint, sprints

S9 = sprint("S9", "Sprint 9 (9/21 - 10/2)", date(2026, 9, 21), date(2026, 10, 2), archived=True)
S10 = sprint("S10", "Sprint 10 (10/6 - 10/17)", date(2026, 10, 6), date(2026, 10, 17))
TEST = sprint("T10", "[Test sprint] Sprint 10 - sắp xếp lại (10/6 - 10/17)", date(2026, 10, 6), date(2026, 10, 17))
TECH = sprint("TS", "tech sprint", date(2026, 10, 6), date(2026, 10, 17))
EMPTY = sprint("E10", "Sprint 20 (10/6 - 10/17)", date(2026, 10, 6), date(2026, 10, 17), total=0)


def _board(lists: dict, *, extra: tuple = ()) -> Board:
    return read_board(sprints(S9, S10, TEST, TECH, *extra), lists, None, datetime(2026, 10, 13, 9), "test")


def test_maintain_sprints_drop_test_lists_and_empty_ones_oldest_first() -> None:
    found = maintain_sprints(read_sprints(sprints(S10, TEST, TECH, EMPTY, S9)))

    assert [sprint.id for sprint in found] == ["S9", "S10"]


def test_the_running_sprint_ignores_test_lists_and_prefers_the_one_with_orders() -> None:
    listed = read_sprints(sprints(S9, S10, TEST, TECH, EMPTY))

    assert select_current(listed, date(2026, 10, 13), None).id == "S10"
    assert select_current(listed, date(2026, 10, 13), "S9").id == "S9"


def test_no_running_sprint_and_several_are_input_errors() -> None:
    listed = read_sprints(sprints(S9, S10))
    with pytest.raises(NoRunningSprint, match="Không có sprint Maintain nào đang chạy ngày 05/10/2026"):
        select_current(listed, date(2026, 10, 5), None)
    twin = sprint("S10b", "Sprint 10 (10/6 - 10/17)", date(2026, 10, 6), date(2026, 10, 17))
    with pytest.raises(InputError, match=r"Có nhiều sprint đang chạy ngày 13/10/2026: Sprint 10 .*\(S10\), .*\(S10b\)"):
        select_current(read_sprints(sprints(S10, twin)), date(2026, 10, 13), None)
    with pytest.raises(InputError, match="Không có sprint id 'nope' trong folder Maintain."):
        select_current(listed, date(2026, 10, 13), "nope")


def test_the_previous_sprint_is_the_latest_that_ended_before_and_may_be_archived() -> None:
    listed = read_sprints(sprints(S9, S10, TECH))

    current = next(s for s in listed if s.id == "S10")
    assert previous_of(listed, current).id == "S9"
    assert previous_of(listed, next(s for s in listed if s.id == "S9")) is None


def test_the_sheet_numbers_roots_by_creation_then_subtasks_and_keeps_bugs_apart() -> None:
    board = _board(
        {
            "S10": orders(
                item("late", "Late root", created=datetime(2026, 10, 7, 9)),
                item("early", "Early root", people=(LINH,), created=datetime(2026, 9, 30, 9)),
                item("sub", "Sub", parent="early", created=datetime(2026, 10, 2, 9)),
                item("deep", "Deep", parent="sub", created=datetime(2026, 10, 3, 9)),
                item("bug", "Bug", parent="deep", bug=True, status="in progress"),
                item("bug2", "Bug 2", parent="early", bug=True, status="done"),
            )
        }
    )

    sheet = sprint_sheet(board, board.sprints[1])

    assert (sheet.name, sheet.number, sheet.id, sheet.headers) == ("Sprint 10 (10/6 - 10/17)", 10, "S10", API_HEADERS)
    assert [(row.stt, row.id, row.kind, row.root_id) for row in sheet.rows] == [
        (1, "early", "Task", "early"),
        (2, "late", "Task", "late"),
        (3, "sub", "Subtask", "early"),
        (4, "deep", "Subtask", "early"),
    ]
    assert [(bug.id, bug.kind, bug.root_id) for bug in sheet.bugs] == [
        ("bug", "Bug", "early"),
        ("bug2", "Bug", "early"),
    ]
    assert sheet.rows[0].cells[9:] == (1, 2)  # Bug mở, Bug tổng


def test_history_is_every_root_once_with_the_sprints_that_list_it() -> None:
    board = _board(
        {
            "S9": orders(item("a", "1.0.0", people=(AN,), app="Roblox", hours=20, created=datetime(2026, 9, 20, 9))),
            "S10": orders(item("a", "1.0.0", people=(AN,), app="Roblox", created=datetime(2026, 9, 20, 9))),
            TECH_MANAGER_LIST: orders(
                item("a", "1.0.0", people=(AN,), app="Roblox", created=datetime(2026, 9, 20, 9)),
                item("mvp", "Research", people=(LINH,), app="New", created=datetime(2026, 8, 1, 9)),
                item("sub", "Sub", parent="mvp"),
            ),
        }
    )

    found = {order.title: order for order in history_orders(board)}

    assert set(found) == {"1.0.0", "Research"}
    assert found["1.0.0"].sprint == "Sprint 9 (9/21 - 10/2), Sprint 10 (10/6 - 10/17)"
    assert [label.number for label in found["1.0.0"].sprints] == [9, 10]
    assert (found["1.0.0"].hours, found["1.0.0"].created) == (20.0, date(2026, 9, 20))
    assert (found["Research"].sprint, found["Research"].sprints) == ("", ())


def test_the_empty_backlog_counts_unfinished_empty_roots_outside_every_sprint() -> None:
    board = _board(
        {
            "S10": orders(item("in-sprint", people=())),
            TECH_MANAGER_LIST: orders(
                item("in-sprint", people=()),
                item("old", status="all issue", created=datetime(2026, 2, 1, 9)),
                item("new", status="ready to progress", created=datetime(2026, 10, 1, 9)),
                item("done", status="done"),
                item("taken", people=(LINH,)),
                item("sub", parent="old"),
            ),
        }
    )

    assert empty_backlog(board, date(2026, 10, 13)) == (2, 1)
    assert newest_update(board) == datetime(2026, 10, 1, 9)
