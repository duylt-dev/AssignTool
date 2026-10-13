"""`scrumbot clone` (D55): copy every list of folder Maintain, list Tech manager and the status history to disk.
GET only; the copy is the input of `scrumbot replay` and is never changed by the bot."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from scrumbot.flows.common import Options, Say
from scrumbot.model_board import MAINTAIN_FOLDER, TECH_MANAGER_LIST
from scrumbot.rules.board import maintain_sprints
from scrumbot.sources.api_client import ApiClient
from scrumbot.sources.api_reader import read_sprints, read_tasks
from scrumbot.sources.env_config import load_config
from scrumbot.sources.raw_store import HISTORY, LISTS, SPRINTS, Recorder


def clone(options: Options, say: Say, now: datetime) -> Path:
    config = load_config(os.environ, options.env_file)
    client = ApiClient(config)
    folder = options.state_dir / "clone" / f"{now:%Y%m%d-%H%M%S}"
    recorder = Recorder(folder, kind="clone", host=config.host, now=now)
    raw_sprints = client.sprints(MAINTAIN_FOLDER)
    recorder.save(SPRINTS, raw_sprints)
    sprints = read_sprints(raw_sprints)
    maintain = {sprint.id for sprint in maintain_sprints(sprints)}
    ids: dict[str, None] = {}
    targets = [*((sprint.id, sprint.name) for sprint in sprints), (TECH_MANAGER_LIST, "Tech manager")]
    for number, (list_id, name) in enumerate(targets, start=1):
        say(f"Đang sao list {number}/{len(targets)}: {name}")
        raw = client.orders(list_id)
        recorder.save(f"{LISTS}/{list_id}", raw)
        if list_id in maintain:
            ids.update((task.id, None) for task in read_tasks(raw, list_id))
    say(f"Đang sao lịch sử trạng thái của {len(ids)} dòng…")
    recorder.save(HISTORY, client.history(list(ids)))
    say(f"Bản sao: {folder} ({client.calls} request, chỉ GET)")
    return folder
