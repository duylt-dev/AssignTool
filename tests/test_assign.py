from datetime import date

import pytest

from assigntool.model import Dev, HistoryOrder, Level, Order, Priority, Size, SizeEstimate, SprintRow
from assigntool.rules.assign import GAP_HOURS, assign
from assigntool.rules.familiarity import FamiliarityIndex


def dev(code: str, level: Level = Level.MIDDLE) -> Dev:
    return Dev(code, code, level, True, ())


def order(stt: int, app: str = "Known", *, people: tuple[str, ...] = (), priority: Priority = Priority.NORMAL) -> Order:
    return Order(SprintRow(stt, f"Order {stt}", "Task", app, people, "", "", None, date(2026, 10, 1), "", ()), priority)


def estimate(size: Size = Size.M) -> SizeEstimate:
    return SizeEstimate(size, "", False)


def choose(
    pool: tuple[Dev, ...],
    history: tuple[HistoryOrder, ...],
    orders: tuple[Order, ...],
    carry: dict[str, int] | None = None,
    leave: dict[str, int] | None = None,
    sizes: dict[int, SizeEstimate] | None = None,
):
    return assign(
        orders,
        sizes or {item.row.stt: estimate() for item in orders},
        pool,
        FamiliarityIndex.build(history, pool),
        carry or {item.code: 0 for item in pool},
        leave or {item.code: 0 for item in pool},
        "Sprint 9",
    )


@pytest.mark.parametrize(
    ("pool", "history", "item", "carry", "leave", "expected"),
    [
        (
            (dev("A"), dev("B")),
            (HistoryOrder("S9", "Known", "latest", ("B",), None, date(2026, 1, 1)),),
            order(1),
            {"A": 0, "B": 0},
            {"A": 0, "B": 0},
            "B",
        ),
        (
            (dev("A", Level.JUNIOR), dev("B", Level.MIDDLE)),
            (),
            order(1, "New"),
            {"A": 0, "B": 0},
            {"A": 0, "B": 0},
            "B",
        ),
        (
            (dev("A"), dev("B")),
            (HistoryOrder("S9", "Known", "latest", ("A", "B"), None, date(2026, 1, 1)),),
            order(1),
            {"A": 1, "B": 0},
            {"A": 0, "B": 0},
            "B",
        ),
        (
            (dev("A"), dev("B")),
            (HistoryOrder("S9", "Known", "latest", ("A", "B"), None, date(2026, 1, 1)),),
            order(1),
            {"A": 0, "B": 0},
            {"A": 1, "B": 0},
            "B",
        ),
        (
            (dev("A", Level.MIDDLE), dev("B", Level.MIDDLE_PLUS)),
            (HistoryOrder("S9", "Known", "latest", ("A", "B"), None, date(2026, 1, 1)),),
            order(1),
            {"A": 0, "B": 0},
            {"A": 0, "B": 0},
            "B",
        ),
        (
            (dev("B", Level.MIDDLE), dev("A", Level.MIDDLE)),
            (HistoryOrder("S9", "Known", "latest", ("A", "B"), None, date(2026, 1, 1)),),
            order(1),
            {"A": 0, "B": 0},
            {"A": 0, "B": 0},
            "A",
        ),
    ],
)
def test_assignment_key_parts_choose_the_pic(
    pool: tuple[Dev, ...],
    history: tuple[HistoryOrder, ...],
    item: Order,
    carry: dict[str, int],
    leave: dict[str, int],
    expected: str,
) -> None:
    assert choose(pool, history, (item,), carry, leave)[0].pic_codes == (expected,)


def test_load_hours_and_cap_override_familiarity_and_backups_ignore_cap() -> None:
    linh, minh = dev("Linh"), dev("Minh")
    history = (HistoryOrder("S9", "Known", "latest", ("Linh",), None, date(2026, 1, 1)),)
    assigned = order(1, "Other", people=("Linh",))
    proposed = order(2, "Known")
    result = choose((linh, minh), history, (assigned, proposed), sizes={1: estimate(Size.L), 2: estimate()})

    assert GAP_HOURS == 16
    assert result[1].pic_codes == ("Minh",)
    assert result[1].backups == ("Linh",)
    assert "Linh quen app hơn nhưng đang có 32h (cân tải)" in result[1].reason


def test_hours_not_order_count_choose_pic_and_outside_preassignment_adds_no_load() -> None:
    linh, minh = dev("Linh"), dev("Minh")
    history = (HistoryOrder("S9", "Known", "latest", ("Linh", "Minh"), None, date(2026, 1, 1)),)
    orders = (
        order(1, people=("Linh",)),
        order(2, people=("Linh",)),
        order(3, people=("Minh",)),
        order(4, people=("Outside",)),
        order(5),
    )
    result = choose(
        (linh, minh),
        history,
        orders,
        sizes={1: estimate(Size.S), 2: estimate(Size.S), 3: estimate(Size.M), 4: estimate(Size.XL), 5: estimate()},
    )

    assert result[3].pic_codes == ()
    assert result[-1].pic_codes == ("Linh",)


def test_reason_names_seniors_excluded_by_the_cap() -> None:
    linh, tien = dev("Linh", Level.MIDDLE_PLUS), dev("Tien", Level.JUNIOR)
    orders = (order(1, "Other", people=("Linh",)), order(2, "New"))
    result = choose((linh, tien), (), orders, sizes={1: estimate(Size.L), 2: estimate(Size.XL)})

    assert result[1].pic_codes == ("Tien",)
    assert "Linh là middle trở lên nhưng đang có 32h (cân tải)" in result[1].reason
    assert "quen app hơn" not in result[1].reason
