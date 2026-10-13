"""Reading the past from today's data (bot spec §8, A70, A74). Pure."""

from __future__ import annotations

from datetime import date, datetime

from scrumbot.model import SprintRow, SprintSheet, StatusChange
from scrumbot.normalize import text_key
from scrumbot.rules.timeline import by_task, carry_at, checkpoints, done_time, outcome, status_at, view_at
from tests.api_builders import LINH, MINH, POOL

KINDS = {text_key(name): kind for name, kind in (("in progress", "custom"), ("done", "done"), ("release", "done"))}
START, END = date(2026, 10, 6), date(2026, 10, 16)


def row(
    ident: str,
    *,
    status: str = "in progress",
    kind: str = "custom",
    people: tuple[str, ...] = (LINH,),
    created: datetime = datetime(2026, 10, 1, 9),
    closed: datetime | None = None,
    due: date | None = None,
    root: str | None = None,
    task_kind: str = "Task",
) -> SprintRow:
    return SprintRow(
        1,
        ident,
        task_kind,
        "Demo",
        people,
        status,
        "",
        due,
        created.date(),
        "",
        (),
        None,
        ident,
        root or ident,
        kind,
        created,
        None,
        closed,
    )


def change(ident: str, old: str, new: str, day: int, hour: int = 9) -> StatusChange:
    return StatusChange(ident, old, new, datetime(2026, 10, day, hour))


def test_status_at_reads_the_history_and_before_the_first_move_its_old_status() -> None:
    changes = by_task((change("a", "ready to progress", "in progress", 7), change("a", "in progress", "done", 9)))
    item = row("a")

    assert status_at(item, changes, datetime(2026, 10, 6, 9), KINDS) == ("ready to progress", "")
    assert status_at(item, changes, datetime(2026, 10, 8, 9), KINDS) == ("in progress", "custom")
    assert status_at(item, changes, datetime(2026, 10, 9, 9), KINDS) == ("done", "done")
    assert status_at(row("b"), changes, datetime(2026, 10, 9, 9), KINDS) is None


def test_done_time_is_the_closing_date_else_the_first_move_into_a_done_kind() -> None:
    changes = by_task(
        (change("a", "in progress", "qa", 8), change("a", "qa", "release", 10), change("a", "release", "done", 12))
    )

    assert done_time(row("a"), changes, KINDS) == datetime(2026, 10, 10, 9)
    assert done_time(row("a", closed=datetime(2026, 10, 9, 18)), changes, KINDS) == datetime(2026, 10, 9, 18)
    assert done_time(row("b"), changes, KINDS) is None


def test_view_at_drops_later_items_and_puts_back_the_status_of_the_time() -> None:
    sheet = SprintSheet(
        "Sprint 10",
        10,
        START,
        END,
        (),
        (
            row("hist"),
            row("done-unknown", status="done", kind="done"),
            row("open", status="ready to progress"),
            row("closed-before", status="done", kind="done", closed=datetime(2026, 10, 7, 9)),
            row("later", created=datetime(2026, 10, 9, 9)),
        ),
        "S10",
        (),
        (change("hist", "ready to progress", "in progress", 7), change("hist", "in progress", "done", 9)),
    )

    view = view_at(sheet, datetime(2026, 10, 8, 8, 30), KINDS)

    assert [(r.id, r.status, r.status_kind) for r in view.rows] == [
        ("hist", "in progress", "custom"),
        ("done-unknown", "in progress", "custom"),
        ("open", "ready to progress", "custom"),
        ("closed-before", "done", "done"),
    ]
    assert len(view.changes) == 1


def test_carry_at_uses_history_then_the_closing_date_then_today_and_the_carried_roots() -> None:
    prev = SprintSheet(
        "Sprint 9",
        9,
        date(2026, 9, 21),
        date(2026, 10, 2),
        (),
        (
            row("busy-then", people=(LINH,)),
            row("closed-late", people=(LINH,), status="done", kind="done", closed=datetime(2026, 10, 7, 9)),
            row("done-carried", people=(MINH,), status="done", kind="done"),
            row("done-left", people=(MINH,), status="done", kind="done"),
            row("open-now", people=(MINH,), status="ready to progress"),
        ),
        "S9",
        (),
        (change("busy-then", "", "in progress", 1), change("busy-then", "in progress", "done", 8)),
    )

    counts = carry_at(prev, datetime(2026, 10, 6), POOL, {"done-carried"}, KINDS)

    assert counts == {"LinhNV": 2, "MinhNM": 2, "AnTD": 0, "TiếnBV": 0}


def test_outcome_names_every_reason_and_is_empty_for_a_good_order() -> None:
    bugs = tuple(row(f"bug{n}", root="buggy", task_kind="Bug") for n in range(5))
    sheet = SprintSheet("Sprint 10", 10, START, END, (), (), "S10", bugs)
    changes = by_task((change("late", "in progress", "done", 19), change("good", "in progress", "done", 12)))

    assert outcome(row("late", due=date(2026, 10, 14)), sheet, set(), changes, KINDS) == (
        "xong sau ngày kết thúc",
        "xong sau hạn",
    )
    assert outcome(row("moved"), sheet, {"moved"}, changes, KINDS) == ("có mặt ở sprint sau", "chưa xong")
    assert outcome(row("buggy", status="done", kind="done"), sheet, set(), changes, KINDS) == ("5 bug",)
    assert outcome(row("good", due=date(2026, 10, 14)), sheet, set(), changes, KINDS) == ()


def test_checkpoints_are_the_first_day_the_fifth_and_three_days_before_the_end() -> None:
    long = SprintSheet("S", 10, START, END, (), ())  # Tue 06/10 – Fri 16/10: 9 working days
    short = SprintSheet("S", 6, date(2026, 8, 10), date(2026, 8, 12), (), ())  # 3 working days

    assert [at.date() for at in checkpoints(long)] == [date(2026, 10, 6), date(2026, 10, 12), date(2026, 10, 14)]
    assert [at.strftime("%H:%M") for at in checkpoints(long)] == ["08:30"] * 3
    assert [at.date() for at in checkpoints(short)] == [date(2026, 8, 10)]
