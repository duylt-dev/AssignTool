from datetime import date

from scrumbot.core.model import Dev, Level
from scrumbot.core.rules.leave import leave_count, on_leave_all_sprint, working_days


def test_working_days_and_leave_helpers() -> None:
    days = working_days(date(2026, 10, 2), date(2026, 10, 6))
    dev = Dev("Linh", "L", Level.MIDDLE, True, (date(2026, 10, 2), date(2026, 10, 5), date(2026, 10, 7)))

    assert days == (date(2026, 10, 2), date(2026, 10, 5), date(2026, 10, 6))
    assert leave_count(dev, days) == 2
    assert not on_leave_all_sprint(dev, days)
    assert working_days(None, date(2026, 10, 6)) == ()


def test_on_leave_all_sprint_requires_a_non_empty_range() -> None:
    dev = Dev("Linh", "L", Level.MIDDLE, True, ())
    assert not on_leave_all_sprint(dev, ())
