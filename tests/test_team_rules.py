from datetime import date

import pytest

from scrumbot.core.errors import InputError
from scrumbot.core.model import Dev, Level, RuleKind, TeamRule
from scrumbot.core.rules.team_rules import check_rules, in_force, rules_day, unavailable_findings

LINH = Dev("Ngọc Văn Linh", "LinhNV", Level.MIDDLE_PLUS, True, ())
MINH = Dev("Nguyễn Nhật Minh", "MinhNM", Level.MIDDLE, True, ())
OUT = Dev("Out", "OutDev", Level.MIDDLE, False, ())
DEVS = (LINH, MINH, OUT)

PIN, EXCLUDE, MAX, PREFER = RuleKind.PIN, RuleKind.EXCLUDE, RuleKind.MAX_ORDERS, RuleKind.PREFER


def rule(
    kind: RuleKind,
    dev: str,
    app: str = "",
    line: int = 1,
    *,
    count: int | None = None,
    start: date | None = None,
    end: date | None = None,
) -> TeamRule:
    return TeamRule(kind=kind, dev=dev, line=line, app=app, max_orders=count, start=start, end=end)


def test_a_dev_missing_from_devs_xlsx_is_an_input_error_and_codes_ignore_case() -> None:
    check_rules((rule(PIN, "linhnv", "AR Dog"),), DEVS, "luat.md")

    with pytest.raises(InputError, match=r"^File 'luat.md', dòng 4: không có dev mã 'LinhN' trong file dev\.$"):
        check_rules((rule(PIN, "LinhN", "AR Dog", 4),), DEVS, "luat.md")


OCT_6, OCT_17, OCT_20, OCT_31 = date(2026, 10, 6), date(2026, 10, 17), date(2026, 10, 20), date(2026, 10, 31)


@pytest.mark.parametrize(
    ("rules", "message"),
    [
        (
            (rule(PIN, "LinhNV", "AR Dog", 3), rule(PIN, "MinhNM", "ardog", 5)),
            "dòng 3 và 5: hai luật Chỉ định khác dev cho app 'AR Dog'.",
        ),
        (
            (rule(PIN, "LinhNV", "AR Dog", 3), rule(EXCLUDE, "LinhNV", "", 5)),
            "dòng 3 và 5: luật Chỉ định và Không giao mâu thuẫn cho LinhNV.",
        ),
        (
            (rule(EXCLUDE, "MinhNM", "VPN", 2), rule(PREFER, "MinhNM", "VPN", 6)),
            "dòng 2 và 6: luật Ưu tiên và Không giao mâu thuẫn cho MinhNM.",
        ),
        (
            (rule(MAX, "LinhNV", line=2, count=1, end=OCT_17), rule(MAX, "LinhNV", line=3, count=2, start=OCT_6)),
            "dòng 2 và 3: hai luật Tối đa đơn khác số cho LinhNV.",
        ),
    ],
)
def test_conflicting_rules_are_input_errors(rules: tuple[TeamRule, ...], message: str) -> None:
    with pytest.raises(InputError, match=f"^File 'luat.md', {message}$"):
        check_rules(rules, DEVS, "luat.md")


@pytest.mark.parametrize(
    "rules",
    [
        (rule(PIN, "LinhNV", "AR Dog", end=OCT_17), rule(PIN, "MinhNM", "AR Dog", start=OCT_20)),
        (rule(PIN, "LinhNV", "AR Dog"), rule(PIN, "LinhNV", "AR Dog")),
        (rule(PIN, "LinhNV", "AR Dog"), rule(EXCLUDE, "LinhNV", "VPN")),
        (rule(PIN, "LinhNV", "AR Dog"), rule(EXCLUDE, "MinhNM", "")),
        (rule(PIN, "LinhNV", "AR Dog"), rule(PREFER, "MinhNM", "AR Dog"), rule(MAX, "LinhNV", count=1)),
        (rule(MAX, "LinhNV", count=1), rule(MAX, "LinhNV", count=1)),
        (rule(MAX, "LinhNV", count=1, end=OCT_17), rule(MAX, "LinhNV", count=3, start=OCT_20)),
    ],
)
def test_rules_that_do_not_conflict_pass(rules: tuple[TeamRule, ...]) -> None:
    check_rules(rules, DEVS, "luat.md")


def test_rules_in_force_on_a_day_include_both_ends_and_open_sides() -> None:
    rules = (
        always := rule(PIN, "LinhNV", "AR Dog"),
        sprint := rule(EXCLUDE, "MinhNM", start=OCT_6, end=OCT_17),
        until := rule(MAX, "LinhNV", count=1, end=OCT_6),
        later := rule(PREFER, "MinhNM", "VPN", start=OCT_20),
    )

    assert in_force(rules, OCT_6) == (always, sprint, until)
    assert in_force(rules, OCT_17) == (always, sprint)
    assert in_force(rules, OCT_31) == (always, later)


def test_a_run_before_the_sprint_applies_the_rules_of_its_first_day() -> None:
    """A34: the TM often runs the tool on the Friday before the sprint."""
    assert rules_day(date(2026, 10, 3), OCT_6) == OCT_6
    assert rules_day(date(2026, 10, 8), OCT_6) == date(2026, 10, 8)
    assert rules_day(date(2026, 10, 3), None) == date(2026, 10, 3)


def test_pins_and_preferences_for_a_dev_outside_the_pool_are_reported() -> None:
    rules = (
        rule(PIN, "outdev", "AR Dog", 3),
        rule(PREFER, "MinhNM", "VPN", 4),
        rule(EXCLUDE, "OutDev", line=5),
        rule(MAX, "OutDev", line=6, count=1),
    )

    (finding,) = unavailable_findings(rules, DEVS, (LINH, MINH))
    minh_on_leave = unavailable_findings(rules, DEVS, (LINH,))

    assert (finding.code, finding.where) == ("RULE-DEV-UNAVAILABLE", "Luật dòng 3")
    assert finding.message == (
        "Luật dòng 3 (Chỉ định OutDev) không áp dụng: OutDev không nhận việc hoặc nghỉ cả sprint."
    )
    assert [item.where for item in minh_on_leave] == ["Luật dòng 3", "Luật dòng 4"]
    assert unavailable_findings(rules[1:], DEVS, (LINH, MINH)) == ()
