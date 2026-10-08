"""Pure assembly of the rule outputs into one report result."""

from __future__ import annotations

from assigntool.errors import InputError
from assigntool.model import (
    Dev,
    Finding,
    HistoryOrder,
    Order,
    Result,
    Severity,
    SizeEstimate,
    SprintSheet,
    TeamRule,
)
from assigntool.rules.assign import assign
from assigntool.rules.carry_over import carry_over
from assigntool.rules.familiarity import FamiliarityIndex
from assigntool.rules.leave import leave_count, on_leave_all_sprint, working_days
from assigntool.rules.summary import summarize
from assigntool.rules.team_rules import relaxed_findings, unavailable_findings


def build_result(
    *,
    target: SprintSheet,
    prev: SprintSheet | None,
    prev_name: str,
    orders: tuple[Order, ...],
    findings: tuple[Finding, ...],
    devs: tuple[Dev, ...],
    history: tuple[HistoryOrder, ...],
    sizes: dict[int, SizeEstimate],
    sizing_note: str,
    rules: tuple[TeamRule, ...] = (),
) -> Result:
    """Apply leave exclusion and combine all pure rules into a report result. `rules` are the TM rules in force."""
    days = working_days(target.start, target.end)
    active = tuple(dev for dev in devs if dev.active)
    removed = tuple(dev for dev in active if on_leave_all_sprint(dev, days))
    pool = tuple(dev for dev in active if dev not in removed)
    if not pool:
        raise InputError("Không còn dev nào để giao đơn.")

    extra: list[Finding] = [
        Finding(Severity.INFO, "DEV-ON-LEAVE", dev.code, f"{dev.code} nghỉ cả sprint; không được giao đơn.")
        for dev in removed
    ]
    if prev is None:
        extra.append(
            Finding(
                Severity.WARN,
                "PREV-SPRINT-MISSING",
                prev_name,
                f"Không có sheet {prev_name}; coi như không dev nào còn việc dở.",
            )
        )
    fam = FamiliarityIndex.build(history, pool)
    carry = carry_over(prev, active)
    leave = {dev.code: leave_count(dev, days) for dev in active}
    assignments = assign(orders, sizes, pool, fam, carry, leave, prev_name, rules)
    extra += [*unavailable_findings(rules, devs, pool), *relaxed_findings(assignments)]
    summaries = summarize(devs, pool, days, carry, leave, assignments, fam)
    ordered_findings = tuple(
        sorted(
            (*findings, *extra),
            key=lambda finding: (0 if finding.severity is Severity.WARN else 1, finding.code, finding.where),
        )
    )
    return Result(target.name, prev_name, sizing_note, assignments, ordered_findings, summaries)
