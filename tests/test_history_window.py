from datetime import date

from scrumbot.core.model import HistoryOrder, SprintLabel
from scrumbot.core.sprint.history_window import history_for, in_sprint

S9 = SprintLabel(9, date(2026, 9, 21), date(2026, 10, 2))
S10 = SprintLabel(10, date(2026, 10, 6), date(2026, 10, 17))
MVP3 = SprintLabel(3, date(2026, 9, 3), date(2026, 9, 30))
S11 = SprintLabel(11, date(2026, 10, 20), date(2026, 10, 31))


def order(title: str, created: date, *sprints: SprintLabel) -> HistoryOrder:
    return HistoryOrder("", "App", title, ("Dev",), None, created, sprints)


def test_in_sprint_needs_number_and_both_dates_unless_unknown() -> None:
    item = order("a", date(2026, 10, 1), S9, S10)

    assert in_sprint(item, 10, S10.start, S10.end)
    assert not in_sprint(item, 10, S10.start, date(2026, 10, 18))
    assert not in_sprint(order("b", date(2026, 9, 1), MVP3), 3, date(2026, 6, 22), date(2026, 7, 3))
    assert in_sprint(item, 10, None, None)
    assert not in_sprint(order("c", date(2026, 10, 1)), 10, None, None)


def test_history_for_drops_the_target_sprint_and_anything_after_the_run_day() -> None:
    history = (
        order("previous sprint", date(2026, 9, 22), S9),
        order("other board", date(2026, 9, 4), MVP3),
        order("no sprint", date(2026, 8, 1)),
        order("target", date(2026, 9, 30), S10),
        order("carried into target", date(2026, 9, 22), S9, S10),
        order("filed after the run day", date(2026, 10, 8), MVP3),
        order("future sprint", date(2026, 10, 5), S11),
    )

    kept = history_for(history, 10, S10.start, S10.end, date(2026, 10, 7))

    assert [item.title for item in kept] == ["previous sprint", "other board", "no sprint"]
    assert [item.title for item in history_for(history, 10, S10.start, S10.end, date(2026, 10, 20))] == [
        "previous sprint",
        "other board",
        "no sprint",
        "filed after the run day",
        "future sprint",
    ]
