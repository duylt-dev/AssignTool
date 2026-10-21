"""The Process step of scrumbot (bot spec §8): the standard input in, the standard outcome out, in two steps that share
their first part (D64).

    from scrumbot import core

    inputs = core.Inputs.from_dict(data)  # or built by an input adapter
    passed = set()  # the fingerprints of the passed reviews, kept by the caller between the two steps
    outcome = core.review(core.place(inputs, now=datetime.now()), asker=None)  # None: the AI is off, no question
    if outcome.status is core.Status.READY:
        passed.add(outcome.order.fingerprint)
    outcome = core.assign(core.place(inputs, now=datetime.now()), reviewed=passed, sizer=None)  # None: every order M
    outcome.to_dict()

The core does no I/O and imports only the standard library: no file, network, clock, subprocess or printing.
`core.review` and `core.assign` are the functions of the sub-packages of the same names.
"""

from scrumbot.core.assign import assign
from scrumbot.core.assign.sizing import Sizer, Sizing
from scrumbot.core.errors import AssignError, InputError
from scrumbot.core.inputs import Inputs, SprintInfo, Task
from scrumbot.core.model import Dev, Level, OrderDraft, RuleKind, StatusChange, TeamRule
from scrumbot.core.outcome import Outcome, Questions, Status
from scrumbot.core.place import Placed, place
from scrumbot.core.review import review
from scrumbot.core.review.asking import Asker

__all__ = [
    "Asker",
    "AssignError",
    "Dev",
    "InputError",
    "Inputs",
    "Level",
    "OrderDraft",
    "Outcome",
    "Placed",
    "Questions",
    "RuleKind",
    "Sizer",
    "Sizing",
    "SprintInfo",
    "StatusChange",
    "Task",
    "TeamRule",
    "Status",
    "assign",
    "place",
    "review",
]
