from datetime import date

import pytest

from assigntool.model import (
    Dev,
    HistoryOrder,
    Level,
    Order,
    Priority,
    RuleKind,
    Size,
    SizeEstimate,
    SprintRow,
    TeamRule,
)
from assigntool.rules.assign import GAP_ORDERS, assign
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
    rules: tuple[TeamRule, ...] = (),
):
    return assign(
        orders,
        sizes or {item.row.stt: estimate() for item in orders},
        pool,
        FamiliarityIndex.build(history, pool),
        carry or {item.code: 0 for item in pool},
        leave or {item.code: 0 for item in pool},
        "Sprint 9",
        rules,
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


def test_order_cap_overrides_familiarity_and_backups_ignore_cap() -> None:
    linh, minh = dev("Linh"), dev("Minh")
    history = (HistoryOrder("S9", "Known", "latest", ("Linh",), None, date(2026, 1, 1)),)
    orders = (order(1, "Other", people=("Linh",)), order(2, "Other", people=("Linh",)), order(3, "Known"))
    result = choose((linh, minh), history, orders)

    assert GAP_ORDERS == 1
    assert result[2].pic_codes == ("Minh",)
    assert result[2].backups == ("Linh",)
    assert "Linh quen app hơn nhưng đang có 2 đơn (cân tải)" in result[2].reason


def test_cap_counts_orders_not_hours_so_large_sizes_do_not_exclude_the_familiar_dev() -> None:
    """D26: the case of confirm.md O7, where an XL pre-assignment used to cap out the only dev who knew the app."""
    linh, minh = dev("Linh"), dev("Minh")
    history = (HistoryOrder("S9", "Known", "latest", ("Linh",), None, date(2026, 1, 1)),)
    orders = (order(1, "Other", people=("Linh",)), order(2, "Known"))
    result = choose((linh, minh), history, orders, sizes={1: estimate(Size.XL), 2: estimate()})

    assert result[1].pic_codes == ("Linh",)
    assert "Tải sprint này: 64h (1 đơn)" in result[1].reason


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
    orders = (order(1, "Other", people=("Linh",)), order(2, "Other", people=("Linh",)), order(3, "New"))
    result = choose((linh, tien), (), orders)

    assert result[2].pic_codes == ("Tien",)
    assert "Linh là middle trở lên nhưng đang có 2 đơn (cân tải)" in result[2].reason
    assert "quen app hơn" not in result[2].reason


# TM rules (spec §7, §8, §14). Each kind has a case where it alone changes the PIC.


def rule(kind: RuleKind, dev: str, app: str = "", line: int = 1, *, count: int | None = None, note: str = ""):
    return TeamRule(kind, dev, app, count, None, None, note, line)


def latest(*people: str, app: str = "Known") -> tuple[HistoryOrder, ...]:
    return (HistoryOrder("S9", app, "latest", people, None, date(2026, 1, 1)),)


def test_a_pin_beats_familiarity_and_the_cap_like_a_preassignment() -> None:
    """D31: Linh holds 2 orders (capped at 0 + 1) and never built Known; Minh built it. The pin still wins."""
    orders = (order(1, "Other", people=("Linh",)), order(2, "Other", people=("Linh",)), order(3, "Known"))
    pool = (dev("Linh"), dev("Minh"))

    assert choose(pool, latest("Minh"), orders)[2].pic_codes == ("Minh",)
    result = choose(pool, latest("Minh"), orders, rules=(rule(RuleKind.PIN, "linh", "known", 7, note="giữ app"),))[2]

    assert result.pic_codes == ("Linh",)
    assert result.reason == (
        "Luật TM dòng 7: chỉ định Linh cho Known (giữ app) · Chưa làm Known · Tải sprint này: 32h (2 đơn) · "
        "Việc dở Sprint 9: 0"
    )
    assert (result.backups, result.rule_lines, result.rules_relaxed) == (("Minh",), (7,), False)


def test_a_pinned_dev_at_their_order_limit_is_not_pinned_and_the_reason_says_why() -> None:
    orders = (order(1, "Other", people=("Linh",)), order(2, "Other", people=("Linh",)), order(3, "Known"))
    rules = (rule(RuleKind.PIN, "Linh", "Known", 7), rule(RuleKind.MAX_ORDERS, "Linh", line=8, count=2))

    result = choose((dev("Linh"), dev("Minh")), latest("Minh"), orders, rules=rules)[2]

    assert result.pic_codes == ("Minh",)
    assert result.reason.endswith(" · Linh đã đủ 2 đơn (luật TM dòng 8)")
    assert result.rule_lines == (8,)


@pytest.mark.parametrize(
    ("app", "expected", "backups"),
    [("known ", "Minh", ("An",)), ("", "Minh", ("An",)), ("VPN", "Linh", ("Minh", "An"))],
)
def test_keep_off_one_app_or_every_app(app: str, expected: str, backups: tuple[str, ...]) -> None:
    pool = (dev("Linh"), dev("Minh"), dev("An", Level.JUNIOR))

    result = choose(pool, latest("Linh"), (order(1, "Known"),), rules=(rule(RuleKind.EXCLUDE, "Linh", app, 2),))[0]

    assert (result.pic_codes, result.backups) == ((expected,), backups)
    assert ("Linh không nhận đơn (luật TM dòng 2)" in result.reason) is (expected != "Linh")


def test_a_rule_on_a_dev_who_would_not_win_anyway_is_neither_quoted_nor_counted() -> None:
    result = choose((dev("Linh"), dev("Minh")), latest("Linh"), (order(1),), rules=(rule(RuleKind.EXCLUDE, "Minh"),))

    assert result[0].pic_codes == ("Linh",)
    assert "luật TM" not in result[0].reason and result[0].rule_lines == ()


def test_the_order_limit_counts_preassigned_orders() -> None:
    orders = (order(1, "Other", people=("Linh",)), order(2, "Known"))
    pool = (dev("Linh"), dev("Minh"))

    assert choose(pool, latest("Linh"), orders)[1].pic_codes == ("Linh",)
    limited = choose(pool, latest("Linh"), orders, rules=(rule(RuleKind.MAX_ORDERS, "Linh", line=3, count=1),))[1]

    assert limited.pic_codes == ("Minh",)
    assert "Linh đã đủ 1 đơn (luật TM dòng 3)" in limited.reason


def test_a_preference_comes_before_familiarity() -> None:
    result = choose(
        (dev("Linh"), dev("Minh")), latest("Linh"), (order(1),), rules=(rule(RuleKind.PREFER, "Minh", "Known", 4),)
    )[0]

    assert result.pic_codes == ("Minh",)
    assert result.reason.startswith("Luật TM dòng 4: ưu tiên Minh cho Known · Chưa làm Known · ")
    assert result.rule_lines == (4,)


def test_a_preference_stays_inside_the_cap_and_the_reason_says_so() -> None:
    """D32: Minh is preferred but holds 2 orders against Linh's 0."""
    orders = (order(1, "Other", people=("Minh",)), order(2, "Other", people=("Minh",)), order(3, "Known"))

    result = choose((dev("Linh"), dev("Minh")), (), orders, rules=(rule(RuleKind.PREFER, "Minh", "Known", 4),))[2]

    assert result.pic_codes == ("Linh",)
    assert result.reason.endswith(" · Minh được ưu tiên (luật TM dòng 4) nhưng đang có 2 đơn (cân tải)")
    assert result.rule_lines == (4,)


def test_the_cap_counts_only_devs_the_rules_leave_on_the_order() -> None:
    """A30: An, kept off everything with 0 orders, must not cap Linh at 0 + 1."""
    orders = (
        order(1, "Other", people=("Linh",)),
        order(2, "Other", people=("Linh",)),
        order(3, "Other", people=("Minh",)),
        order(4, "Known"),
    )
    pool = (dev("Linh"), dev("Minh"), dev("An"))

    assert choose(pool, latest("Linh"), orders)[3].pic_codes == ("An",)
    assert choose(pool, latest("Linh"), orders, rules=(rule(RuleKind.EXCLUDE, "An"),))[3].pic_codes == ("Linh",)


def test_rules_that_leave_nobody_are_relaxed_for_that_order_only() -> None:
    """A31: both devs are kept off Known; the order is still assigned, and flagged for RULE-NO-CANDIDATE."""
    rules = (rule(RuleKind.EXCLUDE, "Linh", "Known", 1), rule(RuleKind.EXCLUDE, "Minh", "Known", 2))

    known, other = choose((dev("Linh"), dev("Minh")), latest("Linh"), (order(1), order(2, "Other")), rules=rules)

    assert (known.pic_codes, known.rules_relaxed, known.rule_lines) == (("Linh",), True, ())
    assert other.rules_relaxed is False
