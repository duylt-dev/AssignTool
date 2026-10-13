from datetime import date

from scrumbot.model import Assignment, Dev, Level, Order, Priority, Size, SizeEstimate, Source, SprintRow
from scrumbot.rules.familiarity import FamiliarityIndex
from scrumbot.rules.summary import summarize


def test_summary_keeps_devs_xlsx_order_and_includes_full_sprint_leave() -> None:
    linh = Dev("Linh", "L", Level.MIDDLE, True, ())
    minh = Dev("Minh", "M", Level.MIDDLE, True, (date(2026, 10, 5),))
    inactive = Dev("Old", "O", Level.MIDDLE, False, ())
    row = SprintRow(1, "Task", "Task", "App", (), "", "", None, None, "", ())
    assignment = Assignment(
        Order(row, Priority.NORMAL), SizeEstimate(Size.M, "", False), Source.PROPOSED, ("Linh",), ("L",), "", ()
    )

    rows = summarize(
        (linh, minh, inactive),
        (linh,),
        (date(2026, 10, 5),),
        {"L": 1, "M": 2},
        {"L": 0, "M": 1},
        (assignment,),
        FamiliarityIndex.build((), (linh,)),
    )

    assert [item.dev.code for item in rows] == ["L", "M"]
    assert rows[0].orders == ("Task [M]",)
    assert rows[1].on_leave_all_sprint and rows[1].hours == 0
