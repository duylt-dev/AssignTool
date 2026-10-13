"""Command line (bot spec §1, assignment spec §2, §11): parse, dispatch to a flow, print, exit codes. The only module
that prints; flows hand their lines to `say`."""

from __future__ import annotations

import argparse
import contextlib
import logging
import sys
import traceback
from datetime import date, datetime
from pathlib import Path

from scrumbot.errors import AssignError, InputError
from scrumbot.flows.auto import auto
from scrumbot.flows.clone import clone
from scrumbot.flows.common import Options
from scrumbot.flows.replay_flow import replay
from scrumbot.flows.run_api import run_api
from scrumbot.flows.run_file import run_file
from scrumbot.flows.sprint_end import sprint_end
from scrumbot.normalize import parse_date

COMMANDS = ("run", "clone", "replay", "auto", "sprint-end")
AI_TOOLS = ("gemini", "agy", "off")


def main(argv: list[str] | None = None) -> int:
    _utf8_console()
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments or arguments[0] not in (*COMMANDS, "-h", "--help"):
        arguments.insert(0, "run")  # A77: `scrumbot` alone is `scrumbot run`
    args = _parser().parse_args(arguments)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING, format="%(levelname)s %(name)s: %(message)s"
    )
    try:
        return _dispatch(args)
    except AssignError as error:
        if args.verbose:
            traceback.print_exc()
        print(f"Lỗi: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Đã dừng.", file=sys.stderr)
        return 130


def _dispatch(args: argparse.Namespace) -> int:
    now = datetime.now()
    options = _options(args)
    say = _say
    if args.command == "run":
        if args.source == "file":
            run_file(options, say, now)
        else:
            run_api(options, say, now)
        return 0
    if args.command == "clone":
        clone(options, say, now)
        return 0
    if args.command == "replay":
        replay(options, Path(args.clone), say, now)
        return 0
    if args.command == "sprint-end":
        sprint_end(options, say, now)
        return 0
    return auto(options, say, now)


def _options(args: argparse.Namespace) -> Options:
    return Options(
        input_dir=Path(getattr(args, "input", "input")),
        devs=getattr(args, "devs", None),
        rules=getattr(args, "rules", None),
        state_dir=Path(args.state),
        out_dir=Path(getattr(args, "out", "output")),
        today=_today(getattr(args, "today", None)),
        snapshot=Path(args.snapshot) if getattr(args, "snapshot", None) else None,
        sprint_id=getattr(args, "sprint_id", None),
        ai=getattr(args, "ai", "off"),
        ai_model=getattr(args, "ai_model", None),
        ai_timeout=getattr(args, "ai_timeout", 180),
        sprint=getattr(args, "sprint", None),
        history=getattr(args, "history", None),
        sheet=getattr(args, "sheet", None),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scrumbot", description="Bot scrum master: giao PIC cho đơn trống và quản lý rủi ro sprint."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("run", help="giao đơn trống và lập sổ rủi ro (mặc định)")
    run.add_argument("--source", choices=("api", "file"), default="api", help="nguồn dữ liệu (mặc định: api)")
    run.add_argument("--snapshot", help="chạy trên snapshot hoặc bản sao đã lưu thay vì gọi API")
    run.add_argument("--sprint-id", help="id sprint cần giao (mặc định: sprint đang chạy)")
    run.add_argument("--today", help="chạy như thể hôm nay là ngày này, YYYY-MM-DD hoặc DD/MM/YYYY")
    run.add_argument("--out", default="output", help="thư mục ghi báo cáo (mặc định: output/)")
    _team(run)
    _ai(run, default="gemini", timeout=180)
    file_group = run.add_argument_group("chỉ dùng với --source file")
    file_group.add_argument(
        "--sprint", help="file export sprint .xlsx (mặc định: file .xlsx duy nhất có sheet Sprint N)"
    )
    file_group.add_argument(
        "--history",
        help="file lịch sử Tech manager .xlsx/.csv (mặc định: file .xlsx không có sheet Sprint N hoặc file .csv; "
        "không có thì dùng sheet sprint cũ)",
    )
    file_group.add_argument("--sheet", help="sheet sprint cần giao (mặc định: Sprint N lớn nhất)")

    copy = commands.add_parser("clone", help="sao toàn bộ dữ liệu Maintain và Tech manager về state/clone/ (chỉ GET)")
    _common(copy)

    again = commands.add_parser("replay", help="giao lại và chấm rủi ro các sprint cũ trên một bản sao")
    again.add_argument("--clone", required=True, help="thư mục bản sao (state/clone/<giờ>)")
    again.add_argument("--out", default="output", help="thư mục ghi báo cáo (mặc định: output/)")
    _team(again)
    _ai(again, default="off", timeout=300)

    scheduled = commands.add_parser("auto", help="lần chạy theo lịch (launchd gọi)")
    _team(scheduled)
    _ai(scheduled, default="agy", timeout=300)

    end = commands.add_parser("sprint-end", help="báo cáo cuối sprint của sprint vừa kết thúc")
    end.add_argument("--sprint-id", help="id sprint (mặc định: sprint kết thúc gần nhất trước hôm nay)")
    end.add_argument("--snapshot", help="đọc snapshot hoặc bản sao đã lưu thay vì gọi API")
    end.add_argument("--today", help="ngày tính 'trước hôm nay', YYYY-MM-DD hoặc DD/MM/YYYY")
    end.add_argument("--out", default="output", help="thư mục ghi báo cáo (mặc định: output/)")
    _team(end)
    return parser


def _common(command: argparse.ArgumentParser) -> None:
    command.add_argument("--state", default="state", help="thư mục bộ nhớ, cache, snapshot, log (mặc định: state/)")
    command.add_argument("-v", "--verbose", action="store_true", help="in traceback và trao đổi với AI")


def _team(command: argparse.ArgumentParser) -> None:
    _common(command)
    command.add_argument("--input", default="input", help="thư mục chứa devs.xlsx và file luật (mặc định: input/)")
    command.add_argument("--devs", help="file dev (mặc định: <input>/devs.xlsx)")
    command.add_argument("--rules", help="file luật TM .md (mặc định: file .md duy nhất trong thư mục input)")


def _ai(command: argparse.ArgumentParser, *, default: str, timeout: int) -> None:
    command.add_argument("--ai", choices=AI_TOOLS, default=default, help=f"công cụ AI (mặc định: {default})")
    command.add_argument("--ai-model", help="model truyền thẳng cho công cụ AI")
    command.add_argument("--ai-timeout", type=int, default=timeout, help=f"số giây chờ AI (mặc định: {timeout})")


def _today(value: str | None) -> date | None:
    """The run day given with --today (A35); None means the clock, read only here and in `_dispatch`."""
    if value is None:
        return None
    try:
        day = parse_date(value)
    except ValueError:
        day = None
    if day is None:
        raise InputError(f"--today '{value}': không đọc được ngày; dùng YYYY-MM-DD hoặc DD/MM/YYYY.")
    return day


def _say(line: str) -> None:
    print(line, flush=True)


def _utf8_console() -> None:
    """Vietnamese output on a Windows console whose code page cannot encode it (best practices §5).

    A stream that cannot be reconfigured keeps its encoding; printing still works with its own errors policy.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            with contextlib.suppress(ValueError, OSError):
                reconfigure(encoding="utf-8", errors="replace")
