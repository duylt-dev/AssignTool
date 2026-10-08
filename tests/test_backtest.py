from datetime import date

from assigntool.model import Dev, HistoryOrder, Level, RuleKind, SprintLabel, TeamRule
from assigntool.rules.backtest import backtest, maintain_sprints, percent

LINH = Dev("Linh", "LinhNV", Level.MIDDLE_PLUS, True, ())
MINH = Dev("Minh", "MinhNM", Level.MIDDLE, True, ())
AN = Dev("An", "AnTD", Level.JUNIOR_PLUS, True, ())
POOL = (LINH, MINH, AN)

S9 = SprintLabel(9, date(2026, 9, 21), date(2026, 10, 2), "Sprint 9 (9/21 - 10/2)")
S10 = SprintLabel(10, date(2026, 10, 6), date(2026, 10, 17), "Sprint 10 (10/6 - 10/17)")
MVP = SprintLabel(3, date(2026, 9, 3), date(2026, 10, 30), "Sprint 3 (9/3 - 10/30)")


def order(
    app: str, people: tuple[str, ...], created: date, *sprints: SprintLabel, title: str = "", priority: str = ""
) -> HistoryOrder:
    return HistoryOrder("", app, title or app, people, None, created, sprints, priority)


def replay(*history: HistoryOrder, devs: tuple[Dev, ...] = POOL, rules: tuple[TeamRule, ...] = ()):
    return {sprint.label.number: sprint for sprint in backtest(history, devs, rules)}


def picks(sprint) -> dict[str, str]:
    return {item.order.title: item.assignment.pic_codes[0] for item in sprint.orders}


def test_maintain_sprints_are_the_short_labels_oldest_first() -> None:
    history = (order("A", (), date(2026, 10, 1), S10, MVP), order("B", (), date(2026, 9, 1), S9, S10))

    assert maintain_sprints(history) == (S9, S10)
    assert (percent(5, 8), percent(1, 3), percent(0, 1)) == (63, 33, 0)


def test_urgent_orders_are_replayed_first_even_when_filed_later() -> None:
    """Priority.URGENT is 0: a truthiness fallback once turned every urgent order into a normal one."""
    sprint = replay(
        order("New A", ("Minh",), date(2026, 10, 1), S10, title="normal"),
        order("New B", ("Linh",), date(2026, 10, 2), S10, title="urgent", priority="urgent"),
    )[10]

    assert picks(sprint) == {"normal": "MinhNM", "urgent": "LinhNV"}
    assert [item.matched for item in sprint.orders] == [True, True]


def test_carried_orders_are_kept_and_orders_without_pool_devs_are_ignored() -> None:
    sprint = replay(
        order("Known", ("An",), date(2026, 9, 1), S9, title="history"),
        order("Other", ("Minh",), date(2026, 9, 22), S9, S10, title="carried"),
        order("Other", ("Minh",), date(2026, 9, 23), S9, S10, title="carried 2"),
        order("Other", ("RnD",), date(2026, 10, 1), S10, title="outside"),
        order("Other", (), date(2026, 10, 1), S10, title="unassigned"),
        order("Known", ("Linh", "An"), date(2026, 10, 1), S10, title="compared"),
    )[10]

    assert sprint.kept == 2
    (item,) = sprint.orders
    assert (item.order.title, item.tm_codes, item.assignment.pic_codes, item.matched) == (
        "compared",
        ("LinhNV", "AnTD"),
        ("AnTD",),
        True,
    )


def test_the_sprints_own_orders_are_never_history() -> None:
    sprint = replay(
        order("Fresh", ("An",), date(2026, 10, 1), S10, title="first"),
        order("Fresh", ("An",), date(2026, 10, 1), S10, title="second"),
    )[10]

    assert all(item.assignment.reason.startswith("Chưa làm Fresh") for item in sprint.orders)
    assert {item.assignment.pic_codes[0] for item in sprint.orders} == {"LinhNV", "MinhNM"}


def test_mid_sprint_orders_are_replayed_on_their_filing_day_with_the_history_of_that_day() -> None:
    sprint = replay(
        order("Wheel", ("Linh",), date(2026, 10, 1), S10, title="before start"),
        order("Wheel", ("An",), date(2026, 10, 8), MVP, title="other board, mid-sprint"),
        order("Wheel", ("An",), date(2026, 10, 9), S10, title="mid-sprint"),
    )[10]

    assert picks(sprint) == {"before start": "LinhNV", "mid-sprint": "AnTD"}
    assert sprint.orders[1].assignment.reason.startswith("Làm version gần nhất của Wheel")


def test_a_pool_on_leave_for_the_whole_sprint_compares_nothing() -> None:
    off = Dev("Linh", "LinhNV", Level.MIDDLE_PLUS, True, tuple(date(2026, 10, day) for day in range(6, 18)))
    sprint = replay(order("App", ("Linh",), date(2026, 10, 1), S10), devs=(off,))[10]

    assert sprint.orders == ()


def test_rules_act_only_on_the_replay_days_inside_their_dates() -> None:
    """D34: a pin dated from 8/10 leaves the order assigned on the sprint's first day alone."""
    pin = TeamRule(RuleKind.PIN, "AnTD", "Fresh", None, date(2026, 10, 8), None, "", 5)
    history = (
        order("Fresh", ("Linh",), date(2026, 10, 1), S10, title="first day"),
        order("Fresh", ("An",), date(2026, 10, 9), S10, title="mid-sprint"),
    )

    sprint = replay(*history, rules=(pin,))[10]

    assert picks(sprint) == {"first day": "LinhNV", "mid-sprint": "AnTD"}
    assert [item.assignment.rule_lines for item in sprint.orders] == [(), (5,)]
    assert picks(replay(*history)[10]) == {"first day": "LinhNV", "mid-sprint": "MinhNM"}
