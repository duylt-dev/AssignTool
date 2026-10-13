"""The end-of-sprint report (bot spec §9, A72): what happened to each order of a finished sprint and which risks the
bot would have flagged in time."""

from __future__ import annotations

import os
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from scrumbot.actions.replay_report import write_sprint_end
from scrumbot.actions.state_store import StateStore
from scrumbot.errors import InputError
from scrumbot.flows.common import Options, Say, load_team
from scrumbot.model import Dev, SizeEstimate, TeamRule
from scrumbot.model_board import TECH_MANAGER_LIST, Board, SprintInfo
from scrumbot.rules.board import maintain_sprints, previous_of, sprint_sheet
from scrumbot.rules.replay_risks import replay_risks, scores
from scrumbot.sources.api_client import ApiClient
from scrumbot.sources.api_reader import read_board, read_changes, read_sprints
from scrumbot.sources.env_config import load_config
from scrumbot.sources.raw_store import LiveSource, RawSource, StoredSource


def sprint_end(options: Options, say: Say, now: datetime) -> Path:
    """`scrumbot sprint-end`: the sprint that ended last before today, or `--sprint-id`."""
    devs, rules, _ = load_team(options)
    today = options.today or now.date()
    if options.snapshot is not None:
        source: RawSource = StoredSource(options.snapshot, options.state_dir / "cache")
    else:
        source = LiveSource(
            ApiClient(load_config(os.environ, options.env_file)), options.state_dir / "cache", None, today
        )
    raw_sprints = source.sprints()
    sprints = read_sprints(raw_sprints)
    ended = _ended(sprints, today, options.sprint_id)
    lists = {sprint.id: source.orders(sprint.id, sprint) for sprint in maintain_sprints(sprints)}
    lists[TECH_MANAGER_LIST] = source.orders(TECH_MANAGER_LIST, None)
    board = read_board(raw_sprints, lists, None, now, source.label)
    path = write_for(board, ended, source, devs, rules, StateStore(options.state_dir), options.out_dir, now)
    say(f"Báo cáo cuối sprint {ended.name}: {path}")
    return path


def write_for(
    board: Board,
    ended: SprintInfo,
    source: RawSource,
    devs: tuple[Dev, ...],
    rules: tuple[TeamRule, ...],
    store: StateStore,
    out_dir: Path,
    now: datetime,
) -> Path:
    """Read the history of the ended sprint and the one before it, score it, write the report, remember it."""
    sheets = [sprint_sheet(board, ended)]
    previous = previous_of(board.sprints, ended)
    if previous is not None:
        sheets.append(sprint_sheet(board, previous))
    ids = list(dict.fromkeys(row.id for sheet in sheets for row in (*sheet.rows, *sheet.bugs)))
    extra = read_changes(source.history(ids)) if ids else ()
    board = replace(board, changes=tuple(sorted({*board.changes, *extra}, key=lambda change: change.at)))
    roots = [row for row in sheets[0].rows if row.kind == "Task"]
    remembered = store.ai_answers([(row.id, row.title) for row in roots])
    sizes: dict[str, SizeEstimate] = {key[0]: estimate for key, estimate in remembered.items()}
    (result,) = replay_risks(board, devs, rules, sizes, only=ended) or (None,)
    if result is None:
        raise InputError(f"Sprint {ended.name} không có đơn nào để chấm.")
    path = write_sprint_end(result, scores((result,)), store.outcomes(ended.id), out_dir, now)
    store.record_sprint_end(ended.id, str(path), now)
    return path


def _ended(sprints: tuple[SprintInfo, ...], today: object, wanted: str | None) -> SprintInfo:
    if wanted is not None:
        for sprint in maintain_sprints(sprints):
            if sprint.id == wanted:
                return sprint
        raise InputError(f"Không có sprint id '{wanted}' trong folder Maintain.")
    finished = [sprint for sprint in maintain_sprints(sprints) if sprint.end is not None and sprint.end < today]
    if not finished:
        raise InputError("Chưa có sprint Maintain nào kết thúc trước hôm nay.")
    return max(finished, key=lambda sprint: (sprint.end, sprint.start))
