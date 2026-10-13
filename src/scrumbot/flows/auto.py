"""`scrumbot auto`, the scheduled run (bot spec §7, D54): full run once a day, quick runs after it, a report only when
something changed, a notification for new proposals and new Cao risks, one log line per run."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from scrumbot.actions.housekeeping import append_log, prune, remove_tree
from scrumbot.actions.notify import notify
from scrumbot.actions.state_store import StateStore
from scrumbot.actions.xlsx_report import write_report
from scrumbot.errors import AssignError, NoRunningSprint
from scrumbot.flows.common import Options, Say, result_lines
from scrumbot.flows.run_api import ApiRun, commit, prepare
from scrumbot.flows.sprint_end import write_for
from scrumbot.rules.board import previous_of
from scrumbot.rules.changes import fingerprint

REPORTS = "bao-cao"
LOGS = "log"


def auto(options: Options, say: Say, now: datetime) -> int:
    """Exit 0 when the run is done or there is no running sprint; an input or API error is logged and raised."""
    options = replace(options, out_dir=options.state_dir / REPORTS, today=None, snapshot=None)
    logs = options.state_dir / LOGS
    prune(logs, now)
    store = StateStore(options.state_dir)
    kind = "quick" if store.full_run_on(now.date()) else "full"
    label = "đầy đủ" if kind == "full" else "nhanh"
    try:
        run = prepare(options, say, now)
    except NoRunningSprint:
        append_log(logs, now, f"{label}: không có sprint đang chạy")
        say("Không có sprint đang chạy; bỏ lượt này.")
        return 0
    except AssignError as error:
        append_log(logs, now, f"{label}: lỗi: {error}")
        raise
    _report(run, kind, label, options, store, say, now)
    if kind == "full":
        _sprint_end(run, options, store, say, now)
    return 0


def _report(run: ApiRun, kind: str, label: str, options: Options, store: StateStore, say: Say, now: datetime) -> None:
    logs = options.state_dir / LOGS
    mark = fingerprint(run.result)
    last = store.last_report(run.sprint.id)
    write = kind == "full" or last is None or last[0] != mark
    path = write_report(run.result, run.headers, options.out_dir, now) if write else None
    commit(run)
    store.record_run(run.sprint.id, kind, mark, run.high_risks, run.proposed_ids, str(path or ""), now)
    new_high = [risk for risk in run.high_risks if last is None or risk not in last[1]]
    if path is None:
        if run.snapshot is not None:
            remove_tree(run.snapshot)
        append_log(logs, now, f"{label} {run.sprint.name}: không đổi")
        say("Không có gì mới; không ghi báo cáo.")
    else:
        parts = [f"giao {len(run.proposals)} đơn mới"] if run.proposals else []
        if new_high:
            parts.append(f"{len(new_high)} rủi ro cao mới")
        detail = f" ({', '.join(parts)})" if parts else ""
        append_log(logs, now, f"{label} {run.sprint.name}: ghi {path.name}{detail}")
        for line in result_lines(run.result, path):
            say(line)
        if parts:
            notify(f"{run.sprint.name}: {', '.join(parts)}. Báo cáo: {path.name}")
    if run.note:
        append_log(logs, now, run.note)


def _sprint_end(run: ApiRun, options: Options, store: StateStore, say: Say, now: datetime) -> None:
    """Once per finished sprint, on the first full run after it (bot spec §7 step 4)."""
    ended = previous_of(run.board.sprints, run.sprint)
    if ended is None or ended.end is None or ended.end >= now.date() or store.sprint_end_done(ended.id):
        return
    path = write_for(run.board, ended, run.source, run.devs, run.rules, store, options.out_dir, now)
    append_log(options.state_dir / LOGS, now, f"cuối sprint {ended.name}: ghi {path.name}")
    say(f"Báo cáo cuối sprint {ended.name}: {path}")
    notify(f"Báo cáo cuối sprint {ended.name}: {path.name}")
