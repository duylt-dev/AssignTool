from datetime import date

from scrumbot.core.assign.summary import summarize
from scrumbot.core.model import Assignment, Dev, Level, Order, Priority, Size, SizeEstimate, Source, SprintRow


def test_summary_keeps_the_dev_list_order_skips_inactive_devs_and_counts_held_orders() -> None:
    linh = Dev("Linh", "L", Level.MIDDLE, True, ())
    minh = Dev("Minh", "M", Level.MIDDLE, True, (date(2026, 10, 5),))
    inactive = Dev("Old", "O", Level.MIDDLE, False, ())
    row = SprintRow(1, "Task", "Task", "App", (), "", "", None, None, "")
    assignment = Assignment(
        Order(row, Priority.NORMAL), SizeEstimate(Size.M, "", False), Source.PROPOSED, ("Linh",), ("L",), "", ()
    )

    rows = summarize(
        (linh, minh, inactive), {"L": 1, "M": 2}, {"L": 0, "M": 1}, (assignment,), {"L": 30, "M": 24}, {"L": 16}
    )

    assert [(item.dev.code, item.orders, item.carry_over, item.leave_days) for item in rows] == [
        ("L", 1, 1, 0),
        ("M", 0, 2, 1),
    ]
    assert [(item.capacity, item.open_hours) for item in rows] == [(30, 16), (24, 0)]
    assert summarize((linh,), {}, {}, ())[0].capacity is None
