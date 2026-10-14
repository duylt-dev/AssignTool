"""Read the API, place the order file of `scrumbot assign` in the running sprint, then decide (bot spec §2–§4, §7).
The review between the two steps (bot spec §7.3) is in `flows/assign_order.py`."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from scrumbot.actions.state_store import StateStore
from scrumbot.flows.common import Options, Say, load_team, rules_note, sizes_for
from scrumbot.flows.fetch import load_board
from scrumbot.model import Dev, HistoryOrder, OrderDraft, Result, TeamRule
from scrumbot.model_board import Board, SprintInfo
from scrumbot.rules.board import history_orders, label_of, newest_update, previous_of, sprint_sheet
from scrumbot.rules.history_window import history_for
from scrumbot.rules.new_order import Placed, place
from scrumbot.rules.pipeline import Team, build_result, team_for
from scrumbot.rules.team_rules import in_force, rules_day
from scrumbot.rules.validate import orders_and_findings
from scrumbot.sources.api_client import ApiClient
from scrumbot.sources.env_config import load_config
from scrumbot.sources.raw_store import LiveSource


@dataclass(frozen=True)
class Prepared:
    """The order file placed in the running sprint, before the review (bot spec §7.2)."""

    board: Board
    sprint: SprintInfo
    placed: Placed
    devs: tuple[Dev, ...]
    rules: tuple[TeamRule, ...]  # in force on the rules day
    history: tuple[HistoryOrder, ...]
    today: date
    run_at: datetime
    freshness: datetime | None


@dataclass(frozen=True)
class Decision:
    """The decision on the whole sprint with the order file in it, before anything is written."""

    result: Result
    team: Team


def prepare(options: Options, say: Say, now: datetime, draft: OrderDraft, order_file: Path) -> Prepared:
    """Read devs, TM rules and the API, and place the order file in the running sprint (§7.2)."""
    today = options.today or now.date()
    run_at = now if options.today is None else datetime.combine(options.today, now.time())
    devs, rules, rules_file = load_team(options, order_file)
    config = load_config(os.environ, options.env_file)
    source = LiveSource(ApiClient(config), options.state_dir / "cache", today)
    if options.today is not None:
        say(f"Ngày chạy: {today:%d/%m/%Y} (--today)")
    board, sprint = load_board(source, day=today, sprint_id=options.sprint_id, fetched_at=now)
    freshness = newest_update(board)
    say(f"Nguồn: {board.source}" + (f" (dữ liệu mới nhất {freshness:%d/%m/%Y %H:%M})" if freshness else ""))
    placed = place(sprint_sheet(board, sprint), draft, _people(board, devs), today, run_at)
    history = history_for(history_orders(board), label_of(sprint).number, sprint.start, sprint.end, today)
    day = rules_day(today, sprint.start)
    rules_now = in_force(rules, day)
    say(rules_note(rules_file, rules, f"{len(rules_now)} có hiệu lực ngày {day:%d/%m/%Y}"))
    say(f"Lịch sử: API ({len(history)} đơn gốc)")
    return Prepared(board, sprint, placed, devs, rules_now, history, today, run_at, freshness)


def decide(prepared: Prepared, options: Options, say: Say) -> Decision:
    """Size with the AI, assign (assignment spec §7) and build the risk register (§4) on the whole sprint."""
    target = prepared.placed.sheet
    orders, findings = orders_and_findings(target)
    store = StateStore(options.state_dir)
    fresh = frozenset({prepared.placed.stt})
    sizes, size_findings, sizing_note = sizes_for(orders, prepared.history, options, store, say, prepared.run_at, fresh)
    previous = previous_of(prepared.board.sprints, prepared.sprint)
    result = build_result(
        target=target,
        prev=sprint_sheet(prepared.board, previous) if previous is not None else None,
        prev_name=previous.name if previous is not None else "sprint trước",
        orders=orders,
        findings=findings + size_findings,
        devs=prepared.devs,
        history=prepared.history,
        sizes=sizes,
        sizing_note=sizing_note,
        rules=prepared.rules,
        run_day=prepared.today,
        now=prepared.run_at,
    )
    return Decision(result, team_for(prepared.devs, target, prepared.today))


def _people(board: Board, devs: tuple[Dev, ...]) -> frozenset[str]:
    """Every name the bot knows, kept away from the AI (A18): the devs' names and codes and every `Người làm`."""
    names = {name for tasks in board.lists.values() for task in tasks for name in task.assignees}
    return frozenset(names | {dev.name for dev in devs} | {dev.code for dev in devs})
