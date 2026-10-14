"""The Process step of scrumbot (bot spec §8): the standard input in, the standard outcome out.

    from scrumbot import core

    inputs = core.Inputs.from_dict(data)  # or built by an input adapter
    outcome = core.evaluate(inputs, now=datetime.now(), sizer=None)  # None: the AI is off, every order M
    outcome.to_dict()

The core does no I/O and imports only the standard library: no file, network, clock, subprocess or printing.
"""

from scrumbot.core.engine import Prepared, decide, evaluate, prepare
from scrumbot.core.errors import AssignError, InputError
from scrumbot.core.inputs import Inputs, SprintInfo, Task
from scrumbot.core.model import Dev, Level, OrderDraft, RuleKind, StatusChange, TeamRule
from scrumbot.core.outcome import Outcome, Status
from scrumbot.core.sizing import Sizer, Sizing

__all__ = [
    "AssignError",
    "Dev",
    "InputError",
    "Inputs",
    "Level",
    "OrderDraft",
    "Outcome",
    "Prepared",
    "RuleKind",
    "Sizer",
    "Sizing",
    "SprintInfo",
    "StatusChange",
    "Task",
    "TeamRule",
    "Status",
    "decide",
    "evaluate",
    "prepare",
]
