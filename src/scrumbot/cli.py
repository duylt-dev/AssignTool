"""Command line (bot spec §1, §7, assignment spec §2, §11): parse, run `assign`, print, exit codes. The only module that
prints; the flow hands its lines to `say`."""

from __future__ import annotations

import argparse
import contextlib
import logging
import sys
import traceback
from datetime import date, datetime
from pathlib import Path

from scrumbot.errors import AssignError, InputError
from scrumbot.flows.assign_order import assign_order
from scrumbot.flows.common import Options
from scrumbot.normalize import parse_date

AI_TOOLS = ("gemini", "agy", "off")


def main(argv: list[str] | None = None) -> int:
    _utf8_console()
    args = _parser().parse_args(sys.argv[1:] if argv is None else argv)  # no sub-command: usage, exit 2 (A91)
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
    assign_order(_options(args), Path(args.file), _say, datetime.now())
    return 0


def _options(args: argparse.Namespace) -> Options:
    return Options(
        input_dir=Path(args.input),
        devs=args.devs,
        rules=args.rules,
        state_dir=Path(args.state),
        out_dir=Path(args.out),
        today=_today(args.today),
        sprint_id=args.sprint_id,
        ai=args.ai,
        ai_model=args.ai_model,
        ai_timeout=args.ai_timeout,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scrumbot", description="Bot scrum master: review đơn của BA/MO, đề xuất PIC và rủi ro."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    assign = commands.add_parser("assign", help="review và giao một đơn từ file .md của BA/MO, ghi output/output.md")
    assign.add_argument("file", help="file đơn .md (mẫu: README mục 4)")
    _options_of(assign)
    return parser


def _options_of(command: argparse.ArgumentParser) -> None:
    command.add_argument("--sprint-id", help="id sprint đặt đơn vào (mặc định: sprint đang chạy)")
    command.add_argument("--today", help="chạy như thể hôm nay là ngày này, YYYY-MM-DD hoặc DD/MM/YYYY")
    command.add_argument("--out", default="output", help="thư mục ghi output.md (mặc định: output/)")
    command.add_argument("--state", default="state", help="thư mục cache câu trả lời AI và list (mặc định: state/)")
    command.add_argument("-v", "--verbose", action="store_true", help="in traceback và trao đổi với AI")
    command.add_argument("--input", default="input", help="thư mục chứa devs.xlsx và file luật (mặc định: input/)")
    command.add_argument("--devs", help="file dev (mặc định: <input>/devs.xlsx)")
    command.add_argument("--rules", help="file luật TM .md (mặc định: file .md duy nhất trong thư mục input)")
    command.add_argument("--ai", choices=AI_TOOLS, default="gemini", help="công cụ AI (mặc định: gemini)")
    command.add_argument("--ai-model", help="model truyền thẳng cho công cụ AI")
    command.add_argument("--ai-timeout", type=int, default=180, help="số giây chờ AI (mặc định: 180)")


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
