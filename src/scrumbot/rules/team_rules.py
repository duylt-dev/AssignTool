"""TM rules (spec §14, D28–D35): check a rules file against the devs, pick the rules in force on a day, and say how
a rule acts on one order of §7. Pure."""

from __future__ import annotations

from datetime import date
from itertools import combinations

from scrumbot.errors import InputError
from scrumbot.model import Assignment, Dev, Finding, RuleKind, Severity, TeamRule
from scrumbot.normalize import app_key, text_key

_CHOOSING = (RuleKind.PIN, RuleKind.PREFER)


def check_rules(rules: tuple[TeamRule, ...], devs: tuple[Dev, ...], source: str) -> None:
    """Raise InputError for a dev missing from devs.xlsx or two rules in conflict (spec §14.2). Checked over the whole
    file, so a normal run and the backtest accept or reject the same file."""
    codes = {text_key(dev.code) for dev in devs}
    for rule in rules:
        if text_key(rule.dev) not in codes:
            raise InputError(f"File '{source}', dòng {rule.line}: không có dev mã '{rule.dev}' trong file dev.")
    for first, second in combinations(rules, 2):
        message = _conflict(first, second) if _overlap(first, second) else None
        if message is not None:
            raise InputError(f"File '{source}', dòng {first.line} và {second.line}: {message}")


def rules_day(today: date, sprint_start: date | None) -> date:
    """The day a normal run applies rules: today, but not before the sprint starts (A34)."""
    return today if sprint_start is None else max(today, sprint_start)


def in_force(rules: tuple[TeamRule, ...], day: date) -> tuple[TeamRule, ...]:
    return tuple(
        rule for rule in rules if (rule.start is None or rule.start <= day) and (rule.end is None or day <= rule.end)
    )


def unavailable_findings(
    rules: tuple[TeamRule, ...], devs: tuple[Dev, ...], pool: tuple[Dev, ...]
) -> tuple[Finding, ...]:
    """RULE-DEV-UNAVAILABLE for each pin or preference naming a dev outside the pool (spec §9, D35)."""
    in_pool = {text_key(dev.code) for dev in pool}
    codes = {text_key(dev.code): dev.code for dev in devs}
    findings: list[Finding] = []
    for rule in rules:
        if rule.kind in _CHOOSING and text_key(rule.dev) not in in_pool:
            code = codes.get(text_key(rule.dev), rule.dev)
            findings.append(
                Finding(
                    Severity.WARN,
                    "RULE-DEV-UNAVAILABLE",
                    f"Luật dòng {rule.line}",
                    f"Luật dòng {rule.line} ({rule.kind.value} {code}) không áp dụng: "
                    f"{code} không nhận việc hoặc nghỉ cả sprint.",
                )
            )
    return tuple(findings)


def relaxed_findings(assignments: tuple[Assignment, ...]) -> tuple[Finding, ...]:
    """RULE-NO-CANDIDATE for each order the rules left without a candidate (spec §9, A31)."""
    return tuple(
        Finding(
            Severity.WARN,
            "RULE-NO-CANDIDATE",
            f"Đơn STT {item.order.row.stt}",
            f"Luật TM loại hết dev khỏi đơn STT {item.order.row.stt}; "
            "đơn này được giao như khi không có luật Không giao và Tối đa đơn.",
        )
        for item in assignments
        if item.rules_relaxed
    )


def blocking_rule(rules: tuple[TeamRule, ...], dev: Dev, app: str, held: int) -> TeamRule | None:
    """The `Không giao` or `Tối đa đơn` rule that keeps `dev`, holding `held` orders, off an order of `app`."""
    for rule in rules:
        if not names(rule, dev):
            continue
        if rule.kind is RuleKind.EXCLUDE and (not app_key(rule.app) or _same_app(rule, app)):
            return rule
        if rule.kind is RuleKind.MAX_ORDERS and rule.max_orders is not None and held >= rule.max_orders:
            return rule
    return None


def pin_rule(rules: tuple[TeamRule, ...], app: str) -> TeamRule | None:
    return next((rule for rule in rules if rule.kind is RuleKind.PIN and _same_app(rule, app)), None)


def prefer_rule(rules: tuple[TeamRule, ...], dev: Dev, app: str) -> TeamRule | None:
    return next(
        (rule for rule in rules if rule.kind is RuleKind.PREFER and names(rule, dev) and _same_app(rule, app)),
        None,
    )


def names(rule: TeamRule, dev: Dev) -> bool:
    """The rule's `Dev` is this dev's `Mã` (A10 matching)."""
    return text_key(rule.dev) == text_key(dev.code)


def _same_app(rule: TeamRule, app: str) -> bool:
    return bool(app_key(app)) and app_key(rule.app) == app_key(app)


def _overlap(first: TeamRule, second: TeamRule) -> bool:
    return (first.start is None or second.end is None or first.start <= second.end) and (
        second.start is None or first.end is None or second.start <= first.end
    )


def _conflict(first: TeamRule, second: TeamRule) -> str | None:
    kinds = {first.kind, second.kind}
    same_dev = text_key(first.dev) == text_key(second.dev)
    if kinds == {RuleKind.PIN} and app_key(first.app) == app_key(second.app) and not same_dev:
        return f"hai luật Chỉ định khác dev cho app '{first.app}'."
    if same_dev and RuleKind.EXCLUDE in kinds and kinds & set(_CHOOSING):
        choosing, exclude = (first, second) if first.kind in _CHOOSING else (second, first)
        if not app_key(exclude.app) or app_key(exclude.app) == app_key(choosing.app):
            return f"luật {choosing.kind.value} và Không giao mâu thuẫn cho {first.dev}."
    if kinds == {RuleKind.MAX_ORDERS} and same_dev and first.max_orders != second.max_orders:
        return f"hai luật Tối đa đơn khác số cho {first.dev}."
    return None
