"""The first step of both `review` and `assign` (bot spec §8.2): check the standard input, pick the running sprint and
place the filed order in it. Pure: the run time comes in as `now`."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime

from scrumbot.core.inputs import Inputs, SprintInfo
from scrumbot.core.model import HistoryOrder, TeamRule
from scrumbot.core.outcome import OrderRef, Outcome, SprintRef, Status
from scrumbot.core.sprint.board import history_orders, label_of, newest_update, previous_of, select_current, sprint_view
from scrumbot.core.sprint.history_window import history_for
from scrumbot.core.sprint.new_order import PlacedOrder, place_order
from scrumbot.core.sprint.team_rules import in_force, rules_day
from scrumbot.core.sprint.validate import check_inputs

NO_PREVIOUS = "sprint trước"


@dataclass(frozen=True)
class Placed:
    """The filed order in the running sprint (bot spec §7.2), and what the terminal prints before any AI call."""

    inputs: Inputs
    sprint: SprintInfo
    previous: SprintInfo | None  # bot spec §2.3
    order: PlacedOrder
    rules: tuple[TeamRule, ...]  # in force on `rules_day`
    rules_day: date
    history: tuple[HistoryOrder, ...]  # inside the window of assignment spec §5.1
    today: date
    run_at: datetime
    freshness: datetime | None

    @property
    def previous_name(self) -> str:
        return self.previous.name if self.previous is not None else NO_PREVIOUS

    @property
    def fingerprint(self) -> str:
        """The order as `review` saw it (A101): title, ID, App, priority, `Hạn` and the description the AI reads."""
        row = self.order.row
        fields = [row.title, row.id, row.app, row.priority_raw, row.due.isoformat() if row.due else "", row.description]
        return hashlib.sha256(json.dumps(fields, ensure_ascii=False).encode()).hexdigest()[:16]

    def outcome(self, status: Status) -> Outcome:
        """The facts every outcome has: the run, the sprint and the order as placed."""
        sprint, row = self.sprint, self.order.row
        return Outcome(
            status=status,
            run_at=self.run_at,
            source=self.inputs.source,
            freshness=self.freshness,
            sprint=SprintRef(sprint.id, sprint.name, sprint.start, sprint.end, self.previous_name),
            order=OrderRef(
                row.title,
                row.stt,
                row.id,
                self.order.how,
                self.inputs.order.origin,
                row.app,
                row.priority_raw,
                row.due,
                row.description,
                self.fingerprint,
            ),
        )


def place(inputs: Inputs, *, now: datetime, today: date | None = None, sprint_id: str | None = None) -> Placed:
    """Check the input, pick the running sprint (or `sprint_id`) and place the filed order in it."""
    check_inputs(inputs)
    day = today or now.date()
    sprint = select_current(inputs.sprints, day, sprint_id)
    on = rules_day(day, sprint.start)
    return Placed(
        inputs=inputs,
        sprint=sprint,
        previous=previous_of(inputs.sprints, sprint),
        order=place_order(sprint_view(inputs, sprint), inputs.order, _people(inputs), day),
        rules=in_force(inputs.rules, on),
        rules_day=on,
        history=history_for(history_orders(inputs), label_of(sprint).number, sprint.start, sprint.end, day),
        today=day,
        run_at=datetime.combine(day, now.timetz()),
        freshness=newest_update(inputs),
    )


def _people(inputs: Inputs) -> frozenset[str]:
    """Every name the bot knows, kept away from the AI (A18): the devs' names and codes and every `Người làm`."""
    names = {name for tasks in inputs.lists.values() for task in tasks for name in task.assignees}
    return frozenset(names | {dev.name for dev in inputs.devs} | {dev.code for dev in inputs.devs})
