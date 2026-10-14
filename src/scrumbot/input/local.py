"""The input of `scrumbot assign` (bot spec §7): the order file, `devs.xlsx` and the TM rules from disk, the sprints
from the dev API, joined into one `Inputs`."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from pathlib import Path

from scrumbot.core.errors import InputError
from scrumbot.core.inputs import Inputs
from scrumbot.core.rules.team_rules import check_rules
from scrumbot.input.dev_api.config import load_config
from scrumbot.input.dev_api.fetch import read_snapshot
from scrumbot.input.files.devs_xlsx import read_devs
from scrumbot.input.files.discovery import devs_path, rules_path
from scrumbot.input.files.order_md import read_order
from scrumbot.input.files.rules_md import read_rules


def load_inputs(
    order_file: Path,
    *,
    input_dir: Path,
    devs: str | None,
    rules: str | None,
    cache_dir: Path,
    env_file: Path,
    environ: Mapping[str, str],
    day: date,
    sprint_id: str | None,
    now: datetime,
) -> Inputs:
    """The files first, rules checked against the devs too, so that a mistake in them shows before any API call.
    `devs` and `rules` are `--devs` and `--rules`; the order file is never taken for the rules file (bot spec §7.1)."""
    if not order_file.is_file():
        raise InputError(f"Không có file đơn '{order_file}'.")
    order = read_order(order_file)
    team = read_devs(devs_path(input_dir, devs))
    found = rules_path(input_dir, rules, order_file)
    team_rules = read_rules(found) if found is not None else ()
    rules_source = str(found) if found is not None else ""
    check_rules(team_rules, team, rules_source)
    snapshot = read_snapshot(load_config(environ, env_file), cache_dir, day=day, sprint_id=sprint_id, now=now)
    return Inputs(
        source=snapshot.source,
        fetched_at=snapshot.fetched_at,
        sprints=snapshot.sprints,
        lists=snapshot.lists,
        history_lists=snapshot.history_lists,
        status_changes=snapshot.status_changes,
        devs=team,
        rules=team_rules,
        rules_source=rules_source,
        order=order,
    )
