"""The core (bot spec §8.2): the standard input in, the standard outcome out. `prepare` picks the running sprint,
places the filed order and reviews it; `decide` sizes, assigns and builds the risk register. Pure: the run time comes
in as `now`, the AI as a sizer."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime

from scrumbot.core.inputs import Inputs, SprintInfo
from scrumbot.core.model import HistoryOrder, Source, TeamRule
from scrumbot.core.model_risk import RiskLevel
from scrumbot.core.outcome import OrderRef, Outcome, ReviewItem, RiskCounts, SprintRef, Status
from scrumbot.core.rules.board import history_orders, label_of, newest_update, previous_of, select_current, sprint_view
from scrumbot.core.rules.history_window import history_for
from scrumbot.core.rules.new_order import Placed, order_report, place
from scrumbot.core.rules.pipeline import build_result, team_for
from scrumbot.core.rules.review import review
from scrumbot.core.rules.team_rules import in_force, rules_day
from scrumbot.core.rules.validate import check_inputs, orders_and_findings
from scrumbot.core.sizing import Sizer, size_orders

NO_PREVIOUS = "sprint trước"


@dataclass(frozen=True)
class Prepared:
    """The filed order placed in the running sprint and reviewed (bot spec §7.2, §7.3), before any AI call."""

    inputs: Inputs
    sprint: SprintInfo
    previous: SprintInfo | None  # bot spec §2.3
    placed: Placed
    rules: tuple[TeamRule, ...]  # in force on `rules_day`
    rules_day: date
    history: tuple[HistoryOrder, ...]  # inside the window of assignment spec §5.1
    today: date
    run_at: datetime
    freshness: datetime | None
    review: tuple[ReviewItem, ...]  # what blocks the order; empty when it is ready


def evaluate(
    inputs: Inputs,
    *,
    now: datetime,
    today: date | None = None,
    sprint_id: str | None = None,
    sizer: Sizer | None = None,
) -> Outcome:
    """`prepare`, then `decide`."""
    return decide(prepare(inputs, now=now, today=today, sprint_id=sprint_id), sizer)


def prepare(inputs: Inputs, *, now: datetime, today: date | None = None, sprint_id: str | None = None) -> Prepared:
    """Check the input, pick the running sprint (or `sprint_id`), place the filed order and review it."""
    check_inputs(inputs)
    day = today or now.date()
    sprint = select_current(inputs.sprints, day, sprint_id)
    placed = place(sprint_view(inputs, sprint), inputs.order, _people(inputs), day)
    on = rules_day(day, sprint.start)
    return Prepared(
        inputs=inputs,
        sprint=sprint,
        previous=previous_of(inputs.sprints, sprint),
        placed=placed,
        rules=in_force(inputs.rules, on),
        rules_day=on,
        history=history_for(history_orders(inputs), label_of(sprint).number, sprint.start, sprint.end, day),
        today=day,
        run_at=datetime.combine(day, now.timetz()),
        freshness=newest_update(inputs),
        review=review(placed.row, placed.how),
    )


def decide(prepared: Prepared, sizer: Sizer | None = None) -> Outcome:
    """A blocked order is not sized (A86). Otherwise size, assign (assignment spec §7) and build the risk register
    (bot spec §4) on the whole sprint with the order in it."""
    if prepared.review:
        return replace(_outcome(prepared, Status.NOT_READY), review=prepared.review)
    inputs, placed, previous = prepared.inputs, prepared.placed, prepared.previous
    orders, findings = orders_and_findings(placed.view)
    sizing = size_orders(orders, prepared.history, frozenset({placed.stt}), sizer)
    result = build_result(
        target=placed.view,
        prev=sprint_view(inputs, previous) if previous is not None else None,
        prev_name=_previous_name(prepared),
        orders=orders,
        findings=findings + sizing.findings,
        devs=inputs.devs,
        history=prepared.history,
        sizes=dict(sizing.sizes),
        sizing_note=sizing.note,
        rules=prepared.rules,
        run_day=prepared.today,
        now=prepared.run_at,
    )
    report = order_report(result, placed, team_for(inputs.devs, placed.view, prepared.today), prepared.history)
    proposed = report.item.source is Source.PROPOSED
    return replace(
        _outcome(prepared, Status.PROPOSED if proposed else Status.PRE_ASSIGNED),
        assignment=report.item,
        sizing_note=result.sizing_note,
        risks=report.risks,
        sprint_risks=RiskCounts(*(sum(risk.level is level for risk in result.risks) for level in RiskLevel)),
        devs=report.devs,
        findings=report.findings,
    )


def _outcome(prepared: Prepared, status: Status) -> Outcome:
    """The facts every outcome has: the run, the sprint and the order as placed."""
    sprint, row = prepared.sprint, prepared.placed.row
    return Outcome(
        status=status,
        run_at=prepared.run_at,
        source=prepared.inputs.source,
        freshness=prepared.freshness,
        sprint=SprintRef(sprint.id, sprint.name, sprint.start, sprint.end, _previous_name(prepared)),
        order=OrderRef(
            row.title,
            row.stt,
            row.id,
            prepared.placed.how,
            prepared.inputs.order.origin,
            row.app,
            row.priority_raw,
            row.due,
            row.description,
        ),
    )


def _previous_name(prepared: Prepared) -> str:
    return prepared.previous.name if prepared.previous is not None else NO_PREVIOUS


def _people(inputs: Inputs) -> frozenset[str]:
    """Every name the bot knows, kept away from the AI (A18): the devs' names and codes and every `Người làm`."""
    names = {name for tasks in inputs.lists.values() for task in tasks for name in task.assignees}
    return frozenset(names | {dev.name for dev in inputs.devs} | {dev.code for dev in inputs.devs})
