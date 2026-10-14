"""`scrumbot assign <file>` (bot spec §7, §8): the input adapter, the core, the AI and the output adapters, wired. It
prints nothing itself: it hands lines to `say`, which `cli.py` binds to print."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from scrumbot import core
from scrumbot.ai.memory import AnswerMemory
from scrumbot.ai.sizer import AiSizer
from scrumbot.ai.tools import cli_ask
from scrumbot.input.local import load_inputs
from scrumbot.output import markdown, terminal

Say = Callable[[str], None]


@dataclass(frozen=True)
class Options:
    """The command line, already parsed (bot spec §1)."""

    input_dir: Path = Path("input")
    devs: str | None = None  # --devs
    rules: str | None = None  # --rules
    state_dir: Path = Path("state")
    out_dir: Path = Path("output")
    today: date | None = None  # --today
    sprint_id: str | None = None  # --sprint-id
    ai: str = "gemini"  # gemini, agy or off
    ai_model: str | None = None
    ai_timeout: int = 180
    env_file: Path = Path(".env")


def run_assign(options: Options, order_file: Path, say: Say, now: datetime) -> Path:
    """Read, prepare, decide, write `output.md`; return its path."""
    if options.today is not None:
        say(terminal.run_day(options.today))
    inputs = load_inputs(
        order_file,
        input_dir=options.input_dir,
        devs=options.devs,
        rules=options.rules,
        cache_dir=options.state_dir / "cache",
        env_file=options.env_file,
        environ=os.environ,
        day=options.today or now.date(),
        sprint_id=options.sprint_id,
        now=now,
    )
    prepared = core.prepare(inputs, now=now, today=options.today, sprint_id=options.sprint_id)
    for line in terminal.prepared_lines(prepared):
        say(line)
    sizer = None if prepared.review else _sizer(options, prepared.run_at, say)
    outcome = core.decide(prepared, sizer)
    path = markdown.write(outcome, options.out_dir)
    for line in terminal.outcome_lines(outcome, path):
        say(line)
    return path


def _sizer(options: Options, run_at: datetime, say: Say) -> core.Sizer | None:
    """The AI of `--ai`, remembering its answers in `--state` (bot spec §5); `off` sizes every order `M`."""
    if options.ai == "off":
        return None
    ask = cli_ask(options.ai, model=options.ai_model, timeout=options.ai_timeout)
    return AiSizer(ask, tool=options.ai, now=run_at, memory=AnswerMemory(options.state_dir), say=say)
