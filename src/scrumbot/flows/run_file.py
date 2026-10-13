"""`scrumbot run --source file`: one run on the export files, as before the API (D51). Kept for `eval/`."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path

from scrumbot.actions.xlsx_report import write_report
from scrumbot.errors import InputError
from scrumbot.flows.common import Options, Say, result_lines, rules_note, sizes_for, summary_rows
from scrumbot.model import HistoryOrder
from scrumbot.rules.history_window import history_for
from scrumbot.rules.pipeline import build_result
from scrumbot.rules.team_rules import check_rules, in_force, rules_day
from scrumbot.rules.validate import history_findings, orders_and_findings
from scrumbot.sources.dev_reader import read_devs
from scrumbot.sources.discovery import file_inputs
from scrumbot.sources.history_reader import read_history
from scrumbot.sources.rules_reader import read_rules
from scrumbot.sources.sprint_reader import read_sheet_history, read_workbook

FILE_CHANGES = "Nguồn file export không có id đơn; không so được."


def run_file(options: Options, say: Say, now: datetime) -> Path:
    inputs = file_inputs(options.input_dir, options.sprint, options.devs, options.history, options.rules)
    today = options.today or now.date()
    target, prev, prev_name = read_workbook(inputs.sprint, options.sheet)
    devs = read_devs(inputs.devs)
    rules = read_rules(inputs.rules) if inputs.rules is not None else ()
    if inputs.rules is not None:
        check_rules(rules, devs, str(inputs.rules))
    if options.today is not None:
        say(f"Ngày chạy: {today:%d/%m/%Y} (--today)")
    day = rules_day(today, target.start)
    rules_now = in_force(rules, day)
    say(rules_note(inputs.rules, rules, f"{len(rules_now)} có hiệu lực ngày {day:%d/%m/%Y}"))
    sheets: tuple[str, ...] = ()
    if inputs.history is not None:
        history = history_for(read_history(inputs.history), target.number, target.start, target.end, today)
        history_note = f"file {inputs.history.name} ({len(history)} đơn gốc)"
    else:
        history, sheets = read_sheet_history(inputs.sprint, target.number)
        history_note = f"sheet {', '.join(sheets)} trong workbook (không có file lịch sử)" if sheets else "không có"
    say(f"Lịch sử: {history_note}")
    orders, findings = orders_and_findings(target)
    findings += history_findings(inputs.history is not None, sheets)
    sizes, size_findings, note = sizes_for(
        orders, _examples(history, inputs.sprint, target.number), options, None, say, now
    )
    result = build_result(
        target=target,
        prev=prev,
        prev_name=prev_name,
        orders=orders,
        findings=findings + size_findings,
        devs=devs,
        history=history,
        sizes=sizes,
        sizing_note=note,
        rules=rules_now,
        run_day=today,
    )
    result = replace(result, change_note=FILE_CHANGES)
    run_at = datetime.combine(today, now.time())
    rows = summary_rows(
        result,
        label=target.name,
        start=target.start,
        end=target.end,
        run_at=run_at,
        today_given=options.today is not None,
        source=f"File {inputs.sprint.name}",
        freshness=None,
        note="",
        backlog=None,
    )
    result = replace(result, summary=rows)
    path = write_report(result, target.headers, options.out_dir, now)
    for line in result_lines(result, path):
        say(line)
    return path


def _examples(history: tuple[HistoryOrder, ...], sprint_path: Path, number: int) -> tuple[HistoryOrder, ...]:
    """Calibration examples for the AI (assignment spec §6.4, A19): history orders with hours, else the workbook's
    older sheets. They serve only as examples; familiarity still comes from the history file alone (A8)."""
    if any(order.hours for order in history):
        return history
    try:
        return read_sheet_history(sprint_path, number)[0]
    except InputError:
        return ()
