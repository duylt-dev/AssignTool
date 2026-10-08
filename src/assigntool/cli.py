"""Command line: input discovery, orchestration, printing and exit codes (spec §2, §11). The only module that prints."""

from __future__ import annotations

import argparse
import contextlib
import logging
import sys
import traceback
from datetime import date, datetime
from pathlib import Path

from assigntool import ai_cli
from assigntool.dev_reader import read_devs
from assigntool.errors import AssignError, InputError
from assigntool.history_reader import read_history
from assigntool.model import (
    BacktestOrder,
    Dev,
    Finding,
    HistoryOrder,
    Order,
    Result,
    Severity,
    SizeEstimate,
    Source,
    TeamRule,
)
from assigntool.rules.backtest import backtest, percent
from assigntool.rules.history_window import history_for
from assigntool.rules.pipeline import build_result
from assigntool.rules.sizing import build_prompt, default_sizes, parse_reply
from assigntool.rules.team_rules import check_rules, in_force, rules_day
from assigntool.rules.validate import history_findings, orders_and_findings
from assigntool.rules_reader import read_rules
from assigntool.sprint_reader import has_sprint_sheets, read_sheet_history, read_workbook
from assigntool.xlsx_report import write_backtest, write_report

DEVS_FILE = "devs.xlsx"


def main(argv: list[str] | None = None) -> int:
    _utf8_console()
    args = _parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING, format="%(levelname)s %(name)s: %(message)s"
    )
    try:
        return _run(args)
    except AssignError as error:
        if args.verbose:
            traceback.print_exc()
        print(f"Lỗi: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Đã dừng.", file=sys.stderr)
        return 130


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="assigntool", description="Giao PIC cho các đơn còn trống của sprint.")
    parser.add_argument("--input", default="input", help="thư mục chứa file input (mặc định: input/)")
    parser.add_argument("--sprint", help="file export sprint .xlsx (mặc định: file .xlsx duy nhất có sheet Sprint N)")
    parser.add_argument("--devs", help="file dev (mặc định: <input>/devs.xlsx)")
    parser.add_argument(
        "--history",
        help="file lịch sử Tech manager .xlsx/.csv (mặc định: file .xlsx không có sheet Sprint N hoặc file .csv; "
        "không có thì dùng sheet sprint cũ)",
    )
    parser.add_argument("--rules", help="file luật TM .md (mặc định: file .md duy nhất trong thư mục input)")
    parser.add_argument(
        "--backtest", action="store_true", help="giao lại các sprint Maintain trong file lịch sử và so với TM"
    )
    parser.add_argument("--sheet", help="sheet sprint cần giao (mặc định: Sprint N lớn nhất)")
    parser.add_argument("--out", default="output", help="thư mục ghi báo cáo (mặc định: output/)")
    parser.add_argument("--ai", choices=("gemini", "agy", "off"), default="gemini", help="công cụ AI ước lượng độ lớn")
    parser.add_argument("--ai-model", help="model truyền thẳng cho công cụ AI")
    parser.add_argument("--ai-timeout", type=int, default=180, help="số giây chờ AI (mặc định: 180)")
    parser.add_argument("-v", "--verbose", action="store_true", help="in traceback và trao đổi với AI")
    return parser


def _run(args: argparse.Namespace) -> int:
    input_dir = Path(args.input)
    workbooks = [p for p in _files(input_dir, ".xlsx") if p.name.lower() != DEVS_FILE]
    sprint_books = [p for p in workbooks if has_sprint_sheets(p)]
    sprint_path = None
    if not args.backtest:
        sprint_path = _explicit(args.sprint, "--sprint") or _only_one(
            sprint_books, "file .xlsx export sprint (có sheet Sprint N)", "--sprint"
        )
    devs_path = _explicit(args.devs, "--devs") or _only_one(
        [p for p in _files(input_dir, ".xlsx") if p.name.lower() == DEVS_FILE], f"file {DEVS_FILE}", "--devs"
    )
    history_path = _explicit(args.history, "--history") or _at_most_one(
        [*_files(input_dir, ".csv"), *(p for p in workbooks if p not in sprint_books)], "file lịch sử", "--history"
    )
    rules_path = _explicit(args.rules, "--rules") or _at_most_one(_files(input_dir, ".md"), "file luật .md", "--rules")
    if args.backtest:
        if history_path is None:
            raise InputError("Không tìm thấy file lịch sử để backtest. Chỉ định bằng --history.")
        devs = read_devs(devs_path)
        rules = _rules(rules_path, devs)
        print(_rules_note(rules_path, rules, "áp theo ngày giao lại"))
        return _backtest(read_history(history_path), devs, rules, history_path, Path(args.out))

    target, prev, prev_name = read_workbook(sprint_path, args.sheet)
    devs = read_devs(devs_path)
    rules = _rules(rules_path, devs)
    day = rules_day(date.today(), target.start)
    rules_now = in_force(rules, day)
    print(_rules_note(rules_path, rules, f"{len(rules_now)} có hiệu lực ngày {day:%d/%m/%Y}"))
    if history_path is not None:
        history = history_for(read_history(history_path), target.number, target.start, target.end, date.today())
        history_note = f"file {history_path.name} ({len(history)} đơn gốc)"
        sheets: tuple[str, ...] = ()
    else:
        history, sheets = read_sheet_history(sprint_path, target.number)
        history_note = f"sheet {', '.join(sheets)} trong workbook (không có file lịch sử)" if sheets else "không có"
    print(f"Lịch sử: {history_note}")
    orders, findings = orders_and_findings(target)
    findings += history_findings(history_path is not None, sheets)
    sizes, size_findings, note = _sizes(args, orders, history)
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
    )
    path = write_report(result, target.headers, Path(args.out), datetime.now())
    _print_summary(result, path)
    return 0


def _rules(path: Path | None, devs: tuple[Dev, ...]) -> tuple[TeamRule, ...]:
    """The TM rules file, checked against devs.xlsx (spec §14); no file means no rules."""
    if path is None:
        return ()
    rules = read_rules(path)
    check_rules(rules, devs, str(path))
    return rules


def _rules_note(path: Path | None, rules: tuple[TeamRule, ...], detail: str) -> str:
    return "Luật TM: không có" if path is None else f"Luật TM: file {path.name} ({len(rules)} luật, {detail})"


def _backtest(
    history: tuple[HistoryOrder, ...],
    devs: tuple[Dev, ...],
    rules: tuple[TeamRule, ...],
    history_path: Path,
    out_dir: Path,
) -> int:
    """Replay the history's Maintain sprints and compare with the TM (D22, spec §13)."""
    sprints = backtest(history, devs, rules)
    if not sprints:
        raise InputError(f"File '{history_path}' không có sprint Maintain nào để backtest.")
    print(f"Backtest: file {history_path.name}, {len(sprints)} sprint Maintain (mọi đơn M, không tính việc dở)")
    for sprint in sprints:
        print(f"{sprint.label.name}: {_matches(sprint.orders)}")
    print(f"Tổng: {_matches(tuple(order for sprint in sprints for order in sprint.orders))}")
    print(f"Báo cáo: {write_backtest(sprints, out_dir, datetime.now())}")
    return 0


def _matches(orders: tuple[BacktestOrder, ...]) -> str:
    if not orders:
        return "không có đơn để so"
    matched = sum(order.matched for order in orders)
    return f"khớp {matched}/{len(orders)} đơn ({percent(matched, len(orders))}%)"


def _sizes(
    args: argparse.Namespace, orders: tuple[Order, ...], history: tuple[HistoryOrder, ...]
) -> tuple[dict[int, SizeEstimate], tuple[Finding, ...], str]:
    if args.ai == "off":
        return default_sizes(orders), (), "tắt AI (mọi đơn M)"
    if not orders:
        return {}, (), "không có đơn"
    print(f"Đang ước lượng độ lớn bằng {args.ai}…", flush=True)
    reply = ai_cli.run_ai(args.ai, build_prompt(orders, history), model=args.ai_model, timeout=args.ai_timeout)
    return parse_reply(reply, orders)


def _files(directory: Path, suffix: str) -> list[Path]:
    if not directory.is_dir():
        raise InputError(f"Không có thư mục input '{directory}'.")
    return sorted(
        p
        for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() == suffix and not p.name.startswith(("~$", "."))
    )


def _only_one(found: list[Path], what: str, flag: str) -> Path:
    if len(found) == 1:
        return found[0]
    if not found:
        raise InputError(f"Không tìm thấy {what}. Chỉ định bằng {flag}.")
    names = ", ".join(p.name for p in found)
    raise InputError(f"Có nhiều {what}: {names}. Chỉ định một file bằng {flag}.")


def _at_most_one(found: list[Path], what: str, flag: str) -> Path | None:
    return _only_one(found, what, flag) if found else None


def _explicit(value: str | None, flag: str) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if not path.is_file():
        raise InputError(f"Không có file '{path}' ({flag}).")
    return path


def _print_summary(result: Result, path: Path) -> None:
    warn = sum(f.severity is Severity.WARN for f in result.findings)
    proposed = [a for a in result.assignments if a.source is Source.PROPOSED]
    print(f"Sprint: {result.sheet_name}")
    print(f"Độ lớn: {result.sizing_note}")
    print(
        f"Đơn: {len(result.assignments)} · giao sẵn: {len(result.assignments) - len(proposed)} · "
        f"tool đề xuất: {len(proposed)} · cảnh báo: {warn} WARN, {len(result.findings) - warn} INFO"
    )
    for item in proposed:
        row = item.order.row
        backups = ", ".join(item.backups) or "không có"
        print(
            f"STT {row.stt} · {row.app} {row.title} [{item.size.size.name}] → {item.pic_codes[0]} (dự phòng: {backups})"
        )
    for finding in result.findings:
        if finding.severity is Severity.WARN:
            print(f"WARN {finding.code}: {finding.message}")
    print(f"Báo cáo: {path}")


def _utf8_console() -> None:
    """Vietnamese output on a Windows console whose code page cannot encode it (best practices §5).

    A stream that cannot be reconfigured keeps its encoding; printing still works with its own errors policy.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            with contextlib.suppress(ValueError, OSError):
                reconfigure(encoding="utf-8", errors="replace")
