"""What `assign` needs besides the API: options, devs and TM rules, AI sizes with memory, risk counts. The flow never
prints; it hands lines to `say`, which `cli.py` binds to print (LLM.md §2)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from scrumbot.actions.state_store import StateStore
from scrumbot.model import Dev, Finding, HistoryOrder, Order, Result, SizeEstimate, TeamRule
from scrumbot.model_risk import RiskLevel
from scrumbot.rules.team_rules import check_rules
from scrumbot.sources.dev_reader import read_devs
from scrumbot.sources.discovery import devs_path, rules_path
from scrumbot.sources.rules_reader import read_rules
from scrumbot.understanding import ai_cli
from scrumbot.understanding.sizing import build_prompt, default_sizes, parse_reply

Say = Callable[[str], None]


@dataclass(frozen=True)
class Options:
    """The command line, already parsed (bot spec §1)."""

    input_dir: Path = Path("input")
    devs: str | None = None
    rules: str | None = None
    state_dir: Path = Path("state")
    out_dir: Path = Path("output")
    today: date | None = None  # --today
    sprint_id: str | None = None  # --sprint-id
    ai: str = "gemini"
    ai_model: str | None = None
    ai_timeout: int = 180
    env_file: Path = Path(".env")


def load_team(
    options: Options, besides: Path | None = None
) -> tuple[tuple[Dev, ...], tuple[TeamRule, ...], Path | None]:
    """devs.xlsx and the TM rules file checked against it (assignment spec §4, §14). `besides`, the order file of
    `assign`, is never taken for the rules file (bot spec §7.1)."""
    devs = read_devs(devs_path(options.input_dir, options.devs))
    path = rules_path(options.input_dir, options.rules, besides)
    rules: tuple[TeamRule, ...] = ()
    if path is not None:
        rules = read_rules(path)
        check_rules(rules, devs, str(path))
    return devs, rules, path


def rules_note(path: Path | None, rules: tuple[TeamRule, ...], detail: str) -> str:
    return "Luật TM: không có" if path is None else f"Luật TM: file {path.name} ({len(rules)} luật, {detail})"


def sizes_for(
    orders: tuple[Order, ...],
    examples: tuple[HistoryOrder, ...],
    options: Options,
    store: StateStore | None,
    say: Say,
    now: datetime,
    fresh: frozenset[int] = frozenset(),
) -> tuple[dict[int, SizeEstimate], tuple[Finding, ...], str]:
    """AI sizes, from the memory when an answer for the same order id and title exists (A67). Orders whose STT is in
    `fresh` are sized by this call and never remembered: their description comes from an order file (bot spec §7.2)."""
    if options.ai == "off":
        return default_sizes(orders), (), "tắt AI (mọi đơn M)"
    if not orders:
        return {}, (), "không có đơn"
    keys = [(order.row.id, order.row.title) for order in orders if order.row.id and order.row.stt not in fresh]
    remembered = store.ai_answers(keys) if store is not None else {}
    sizes = {
        order.row.stt: remembered[key] for order in orders if (key := (order.row.id, order.row.title)) in remembered
    }
    todo = tuple(order for order in orders if order.row.stt not in sizes)
    if not todo:
        return sizes, (), f"AI (bộ nhớ, {len(sizes)}/{len(orders)} đơn)"
    say(f"Đang ước lượng độ lớn bằng {options.ai}… ({len(todo)} đơn)")
    prompt = build_prompt(todo, examples)
    reply = ai_cli.run_ai(options.ai, prompt, model=options.ai_model, timeout=options.ai_timeout)
    sized, findings, note = parse_reply(reply, todo)
    if store is not None and reply.failure is None:
        store.save_ai_answers(
            {(o.row.id, o.row.title): sized[o.row.stt] for o in todo if o.row.id and o.row.stt not in fresh},
            options.ai,
            now,
        )
    sizes.update(sized)
    if remembered:
        valid = sum(not estimate.is_default for estimate in sizes.values())
        note = (
            f"{note}; {len(remembered)} đơn từ bộ nhớ"
            if reply.failure is not None
            else f"AI ({options.ai}, {valid}/{len(orders)} đơn; {len(remembered)} từ bộ nhớ)"
        )
    return sizes, findings, note


def risk_counts(result: Result) -> str:
    counts = [sum(risk.level is level for risk in result.risks) for level in RiskLevel]
    return f"{counts[0]} cao · {counts[1]} trung bình · {counts[2]} thấp"
