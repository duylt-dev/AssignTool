"""Pure assembly of the rule outputs into one report result (assignment spec §7–§10, bot spec §3–§5)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time

from scrumbot.errors import InputError
from scrumbot.model import (
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
from scrumbot.model_risk import KeptProposal, OrderMark, Outcome
from scrumbot.rules.assign import assign
from scrumbot.rules.capacity import capacities, dev_loads
from scrumbot.rules.carry_over import carry_over
from scrumbot.rules.changes import change_rows
from scrumbot.rules.familiarity import FamiliarityIndex
from scrumbot.rules.leave import leave_count, on_leave_all_sprint, pre_assigned_on_leave, working_days
from scrumbot.rules.pic_risks import suggester
from scrumbot.rules.proposals import restore, with_kept
from scrumbot.rules.risk_register import RiskContext, register
from scrumbot.rules.summary import summarize
from scrumbot.rules.team_rules import relaxed_findings, rules_day, unavailable_findings

MORNING = time(8, 30)  # a run day with no clock time is read as the start of the working day


@dataclass(frozen=True)
class Team:
    """Who can take work on the base day (bot spec §3, A75)."""

    days: tuple[date, ...]  # working days of the sprint
    base: date
    rest: tuple[date, ...]  # remaining working days
    active: tuple[Dev, ...]  # "Nhận việc" = Y
    removed: tuple[Dev, ...]  # off every working day of the sprint (DEV-ON-LEAVE)
    off_rest: tuple[Dev, ...]  # off every remaining day (DEV-ON-LEAVE-REST)
    pool: tuple[Dev, ...]


def team_for(devs: tuple[Dev, ...], target: SprintSheet, run_day: date | None) -> Team:
    """Without `run_day` the run is read as the sprint's first day, the behaviour before the remaining-days leave."""
    days = working_days(target.start, target.end)
    base = rules_day(run_day, target.start) if run_day is not None else target.start or date.min
    rest = working_days(base, target.end) if target.end is not None else ()
    active = tuple(dev for dev in devs if dev.active)
    removed = tuple(dev for dev in active if on_leave_all_sprint(dev, days))
    off_rest = tuple(dev for dev in active if dev not in removed and on_leave_all_sprint(dev, rest))
    pool = tuple(dev for dev in active if dev not in removed and dev not in off_rest)
    return Team(days, base, rest, active, removed, off_rest, pool)


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
    run_day: date | None = None,
    now: datetime | None = None,
    kept: dict[int, KeptProposal] | None = None,
    baseline: tuple[OrderMark, ...] | None = None,
    outcomes: tuple[Outcome, ...] = (),
) -> Result:
    """Leave exclusion, §7 with kept proposals, the risk register and the change rows. `rules` are those in force.

    Without `run_day` the run is read as the sprint's first day (`team_for`)."""
    team = team_for(devs, target, run_day)
    days, base, rest, active = team.days, team.base, team.rest, team.active
    removed, off_rest, pool = team.removed, team.off_rest, team.pool
    if not pool:
        raise InputError("Không còn dev nào để giao đơn.")

    extra: list[Finding] = [
        Finding(Severity.INFO, "DEV-ON-LEAVE", dev.code, f"{dev.code} nghỉ cả sprint; không được giao đơn.")
        for dev in removed
    ]
    extra += [
        Finding(
            Severity.INFO,
            "DEV-ON-LEAVE-REST",
            dev.code,
            f"{dev.code} nghỉ hết các ngày còn lại của sprint (từ {base:%d/%m/%Y}); không được giao đơn mới.",
        )
        for dev in off_rest
    ]
    extra += pre_assigned_on_leave(orders, removed, pool)
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
    leave = {dev.code: leave_count(dev, rest or days) for dev in active}
    for_rule, used = with_kept(orders, kept or {}, pool)
    assignments = restore(assign(for_rule, sizes, pool, fam, carry, leave, prev_name, rules), orders, used)
    extra += [*unavailable_findings(rules, devs, pool), *relaxed_findings(assignments)]
    context = RiskContext(
        sheet=target,
        assignments=assignments,
        pool=pool,
        active=active,
        fam=fam,
        carry=carry,
        prev_name=prev_name,
        leave_rest=leave,
        base=base,
        rest=rest,
        now=now or datetime.combine(base, MORNING),
        suggest=suggester(orders, assignments, sizes, pool, fam, carry, leave, prev_name, rules),
        baseline=baseline,
    )
    risks = register(context)
    summaries = summarize(devs, pool, days, carry, leave, assignments, fam, capacities(context), dev_loads(context))
    ordered_findings = tuple(
        sorted(
            (*findings, *extra),
            key=lambda finding: (0 if finding.severity is Severity.WARN else 1, finding.code, finding.where),
        )
    )
    changes = change_rows(assignments, baseline, outcomes, active) if baseline is not None else ()
    return Result(target.name, prev_name, sizing_note, assignments, ordered_findings, summaries, risks, changes)
