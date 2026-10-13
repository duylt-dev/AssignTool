"""`scrumbot run` on the internal system's API (bot spec §2–§6): read, decide, write the report, update the memory.
`decide` is shared with `scrumbot assign` (bot spec §7)."""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

from scrumbot.actions.state_store import StateStore
from scrumbot.actions.xlsx_report import write_report
from scrumbot.flows.common import (
    Options,
    Say,
    description_note,
    load_team,
    result_lines,
    rules_note,
    sizes_for,
    summary_rows,
)
from scrumbot.flows.fetch import load_board
from scrumbot.model import Dev, HistoryOrder, OrderDraft, Result, Source
from scrumbot.model_board import Board, SprintInfo
from scrumbot.model_risk import KeptProposal, Outcome
from scrumbot.rules.board import (
    empty_backlog,
    history_orders,
    label_of,
    newest_update,
    previous_of,
    sprint_sheet,
)
from scrumbot.rules.changes import marks
from scrumbot.rules.history_window import history_for
from scrumbot.rules.new_order import Placed, place
from scrumbot.rules.pipeline import Team, build_result, team_for
from scrumbot.rules.proposals import settle
from scrumbot.rules.team_rules import in_force, rules_day
from scrumbot.rules.validate import orders_and_findings
from scrumbot.sources.api_client import ApiClient
from scrumbot.sources.env_config import load_config
from scrumbot.sources.raw_store import LiveSource

NOT_COMPARED = "Không so khi chạy với --today."
NO_BASELINE = "Chưa có lần chạy trước để so"


@dataclass(frozen=True)
class Decision:
    """One run's decision, before anything is written."""

    result: Result
    sprint: SprintInfo
    headers: tuple[str, ...]
    run_at: datetime
    live: bool  # live data of today: the memory is read and written (A66)
    freshness: datetime | None
    source: str
    store: StateStore
    kept_before: tuple[KeptProposal, ...]
    standing: dict[int, KeptProposal]
    outcomes: tuple[Outcome, ...]
    team: Team
    history: tuple[HistoryOrder, ...]
    placed: Placed | None  # where the order file sits, for `assign`


def run_api(options: Options, say: Say, now: datetime) -> Path:
    """Read the API, decide, write the report to `--out`, then update the memory (bot spec §2–§6)."""
    decision = decide(options, say, now)
    result, store, sprint = decision.result, decision.store, decision.sprint
    path = write_report(result, decision.headers, options.out_dir, now)
    if decision.live:  # only runs on live data of today touch the memory (A62, A66)
        standing_ids = {proposal.order_id for proposal in decision.standing.values()}
        store.save_outcomes(sprint.id, decision.outcomes)
        store.forget_proposals(tuple(p.order_id for p in decision.kept_before if p.order_id not in standing_ids))
        store.save_proposals(
            sprint.id,
            tuple(
                KeptProposal(item.order.row.id, item.pic_codes[0], item.reason, item.backups, decision.run_at)
                for item in result.assignments
                if item.source is Source.PROPOSED and not item.kept and item.order.row.id
            ),
        )
        store.save_marks(sprint.id, marks(result.assignments, tuple(s.dev for s in result.devs)), decision.run_at)
    for line in result_lines(result, path):
        say(line)
    return path


def decide(
    options: Options, say: Say, now: datetime, draft: OrderDraft | None = None, order_file: Path | None = None
) -> Decision:
    """Read the API and the memory and decide; with `draft`, the order file is placed in the sprint first (§7.2)."""
    today = options.today or now.date()
    run_at = now if options.today is None else datetime.combine(options.today, now.time())
    live = options.today is None
    devs, rules, rules_file = load_team(options, order_file)
    state = options.state_dir
    config = load_config(os.environ, options.env_file)
    source = LiveSource(ApiClient(config), state / "cache", today)
    if options.today is not None:
        say(f"Ngày chạy: {today:%d/%m/%Y} (--today)")
    board, sprint = load_board(source, day=today, sprint_id=options.sprint_id, fetched_at=now)
    freshness = newest_update(board)
    say(f"Nguồn: {board.source}" + (f" (dữ liệu mới nhất {freshness:%d/%m/%Y %H:%M})" if freshness else ""))
    target = sprint_sheet(board, sprint)
    placed = None
    if draft is not None:
        placed = place(target, draft, _people(board, devs), today, run_at)
        target = placed.sheet
    previous = previous_of(board.sprints, sprint)
    label = label_of(sprint)
    history = history_for(history_orders(board), label.number, sprint.start, sprint.end, today)
    day = rules_day(today, sprint.start)
    rules_now = in_force(rules, day)
    say(rules_note(rules_file, rules, f"{len(rules_now)} có hiệu lực ngày {day:%d/%m/%Y}"))
    say(f"Lịch sử: API ({len(history)} đơn gốc)")
    orders, findings = orders_and_findings(target)
    store = StateStore(state)
    fresh = frozenset({placed.stt}) if placed is not None else frozenset()
    sizes, size_findings, sizing_note = sizes_for(orders, history, options, store, say, run_at, fresh)
    active = tuple(dev for dev in devs if dev.active)
    kept_before = store.proposals(sprint.id) if live else ()
    standing, outcomes = settle(kept_before, orders, active, run_at) if live else ({}, ())
    stored_state = store.baseline(sprint.id, today) if live else None
    result = build_result(
        target=target,
        prev=sprint_sheet(board, previous) if previous is not None else None,
        prev_name=previous.name if previous is not None else "sprint trước",
        orders=orders,
        findings=findings + size_findings,
        devs=devs,
        history=history,
        sizes=sizes,
        sizing_note=sizing_note,
        rules=rules_now,
        run_day=today,
        now=run_at,
        kept=standing,
        baseline=stored_state[0] if stored_state is not None else None,
        outcomes=(*store.outcomes(sprint.id, today), *outcomes) if live else (),
    )
    if not live:
        change_note = NOT_COMPARED
    elif stored_state is None:
        change_note = NO_BASELINE
    else:
        change_note = f"So với dữ liệu lưu lúc {stored_state[1]:%d/%m/%Y %H:%M}"
    result = replace(result, change_note=change_note)
    note = description_note(result)
    if note and draft is None:
        say(note)
    rows = summary_rows(
        result,
        label=sprint.name,
        start=sprint.start,
        end=sprint.end,
        run_at=run_at,
        today_given=options.today is not None,
        source=board.source,
        freshness=freshness,
        note=note,
        backlog=empty_backlog(board, today),
    )
    return Decision(
        result=replace(result, summary=rows),
        sprint=sprint,
        headers=target.headers,
        run_at=run_at,
        live=live,
        freshness=freshness,
        source=board.source,
        store=store,
        kept_before=kept_before,
        standing=standing,
        outcomes=outcomes,
        team=team_for(devs, target, today),
        history=history,
        placed=placed,
    )


def _people(board: Board, devs: tuple[Dev, ...]) -> frozenset[str]:
    """Every name the bot knows, kept away from the AI (A18): the devs' names and codes and every `Người làm`."""
    names = {name for tasks in board.lists.values() for task in tasks for name in task.assignees}
    return frozenset(names | {dev.name for dev in devs} | {dev.code for dev in devs})
