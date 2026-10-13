"""`scrumbot run` on the internal system's API (bot spec §2–§6): read, decide, write the report, update the memory."""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

from scrumbot.actions.housekeeping import prune
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
from scrumbot.model import Dev, Result, Source, TeamRule
from scrumbot.model_board import Board, SprintInfo
from scrumbot.model_risk import KeptProposal, Outcome, RiskLevel
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
from scrumbot.rules.pipeline import build_result
from scrumbot.rules.proposals import settle
from scrumbot.rules.team_rules import in_force, rules_day
from scrumbot.rules.validate import orders_and_findings
from scrumbot.sources.api_client import ApiClient
from scrumbot.sources.env_config import load_config
from scrumbot.sources.raw_store import LiveSource, RawSource, Recorder, StoredSource

NOT_COMPARED = "Không so khi chạy với --today hoặc --snapshot."
NO_BASELINE = "Chưa có lần chạy trước để so"


@dataclass(frozen=True)
class ApiRun:
    """One run decided but not yet written: the flow that calls `prepare` chooses whether to write (bot spec §7)."""

    result: Result
    sprint: SprintInfo
    board: Board
    source: RawSource  # for what a flow reads after deciding, e.g. the end-of-sprint history
    devs: tuple[Dev, ...]
    rules: tuple[TeamRule, ...]
    headers: tuple[str, ...]
    store: StateStore
    live: bool  # live data of today: the memory is read and written (A66)
    run_at: datetime
    snapshot: Path | None
    note: str  # the D50 description note
    proposals: tuple[KeptProposal, ...]  # new proposals of this run
    outcomes: tuple[Outcome, ...]  # outcomes found by this run
    forget: tuple[str, ...]  # order ids whose remembered proposal no longer stands

    @property
    def high_risks(self) -> tuple[str, ...]:
        return tuple(f"{risk.code}|{risk.where}" for risk in self.result.risks if risk.level is RiskLevel.HIGH)

    @property
    def proposed_ids(self) -> tuple[str, ...]:
        return tuple(
            item.order.row.id
            for item in self.result.assignments
            if item.source is Source.PROPOSED and item.order.row.id
        )


def run_api(options: Options, say: Say, now: datetime) -> Path:
    """A manual run: always writes its report to `--out` (D54: `output/` is for manual runs)."""
    run = prepare(options, say, now)
    path = write_report(run.result, run.headers, options.out_dir, now)
    commit(run)
    for line in result_lines(run.result, path):
        say(line)
    return path


def prepare(options: Options, say: Say, now: datetime) -> ApiRun:
    today = options.today or now.date()
    run_at = now if options.today is None else datetime.combine(options.today, now.time())
    live = options.today is None and options.snapshot is None
    devs, rules, rules_file = load_team(options)
    state = options.state_dir
    snapshot: Path | None = None
    source: RawSource
    if options.snapshot is not None:
        stored = StoredSource(options.snapshot, state / "cache")
        source, fetched_at = stored, stored.fetched_at or now
    else:
        config = load_config(os.environ, options.env_file)
        prune(state / "snapshots", now)
        snapshot = state / "snapshots" / f"{now:%Y%m%d-%H%M%S}"
        recorder = Recorder(snapshot, kind="snapshot", host=config.host, now=now)
        source, fetched_at = LiveSource(ApiClient(config), state / "cache", recorder, today), now
    if options.today is not None:
        say(f"Ngày chạy: {today:%d/%m/%Y} (--today)")
    board, sprint = load_board(source, day=today, sprint_id=options.sprint_id, fetched_at=fetched_at)
    freshness = newest_update(board)
    say(f"Nguồn: {board.source}" + (f" (dữ liệu mới nhất {freshness:%d/%m/%Y %H:%M})" if freshness else ""))
    target = sprint_sheet(board, sprint)
    previous = previous_of(board.sprints, sprint)
    label = label_of(sprint)
    history = history_for(history_orders(board), label.number, sprint.start, sprint.end, today)
    day = rules_day(today, sprint.start)
    rules_now = in_force(rules, day)
    say(rules_note(rules_file, rules, f"{len(rules_now)} có hiệu lực ngày {day:%d/%m/%Y}"))
    say(f"Lịch sử: API ({len(history)} đơn gốc)")
    orders, findings = orders_and_findings(target)
    store = StateStore(state)
    sizes, size_findings, sizing_note = sizes_for(orders, history, options, store, say, run_at)
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
    if note:
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
    standing_ids = {proposal.order_id for proposal in standing.values()}
    return ApiRun(
        result=replace(result, summary=rows),
        sprint=sprint,
        board=board,
        source=source,
        devs=devs,
        rules=rules,
        headers=target.headers,
        store=store,
        live=live,
        run_at=run_at,
        snapshot=snapshot,
        note=note,
        proposals=tuple(
            KeptProposal(item.order.row.id, item.pic_codes[0], item.reason, item.backups, run_at)
            for item in result.assignments
            if item.source is Source.PROPOSED and not item.kept and item.order.row.id
        ),
        outcomes=outcomes,
        forget=tuple(proposal.order_id for proposal in kept_before if proposal.order_id not in standing_ids),
    )


def commit(run: ApiRun) -> None:
    """Store what the next runs need (A62, A66). Only runs on live data of today touch the memory."""
    if not run.live:
        return
    active = tuple(summary.dev for summary in run.result.devs)
    run.store.save_outcomes(run.sprint.id, run.outcomes)
    run.store.forget_proposals(run.forget)
    run.store.save_proposals(run.sprint.id, run.proposals)
    run.store.save_marks(run.sprint.id, marks(run.result.assignments, active), run.run_at)
