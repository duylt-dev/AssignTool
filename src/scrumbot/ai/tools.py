"""The AI CLI tools `gemini` and `agy` (best practices §4): one call, read-only, in an empty temporary directory. The
only module that starts a child process, never with `shell=True`."""

from __future__ import annotations

import contextlib
import json
import logging
import os
import re
import shutil
import signal
import subprocess
import tempfile
from collections.abc import Callable
from functools import partial
from pathlib import Path

from scrumbot.ai.prompt import AiReply
from scrumbot.core.normalize import clean

Ask = Callable[[str], AiReply]  # one AI call: prompt in, reply out

_LOGGER = logging.getLogger(__name__)
_OBJECT_START = re.compile(r"(?m)^\s*\{")
# A "message" value inside JSON that may itself be escaped JSON text: message": "…, message\": \"…
_MESSAGE = re.compile(r'message(?:\\*")?\s*:\s*(?:\\*")+([^"\\{}]{3,})')


def cli_ask(tool: str, *, model: str | None, timeout: int) -> Ask:
    """`ask` for `AiSizer` and `AiAsker` that runs `gemini` or `agy`."""
    return partial(run_ai, tool, model=model, timeout=timeout)


def run_ai(
    tool: str, prompt: str, *, model: str | None, timeout: int, command: tuple[str, ...] | None = None
) -> AiReply:
    """Return the AI response or a short Vietnamese failure reason."""
    executable = command or _resolve(tool)
    if executable is None:
        return AiReply(tool, None, f"không tìm thấy {tool}")
    if tool == "agy" and Path(executable[0]).suffix.lower() in {".cmd", ".bat"}:
        return AiReply(tool, None, "agy là file .cmd/.bat; không truyền prompt qua tham số")

    args, process_input, logged_args = _arguments(tool, executable, prompt, model, timeout)
    _LOGGER.debug("AI prompt: %s", prompt)
    _LOGGER.debug("AI args: %r", logged_args)
    try:
        with tempfile.TemporaryDirectory() as directory:
            returncode, stdout, stderr = _run_child(args, process_input, directory, timeout)
    except subprocess.TimeoutExpired:
        return AiReply(tool, None, f"hết thời gian {timeout}s")
    except OSError as error:
        return AiReply(tool, None, f"không chạy được {tool}: {error}")

    _LOGGER.debug("AI stdout: %s", stdout)
    _LOGGER.debug("AI stderr: %s", stderr)
    if returncode:
        message = _error_message(stdout) or _error_message(stderr)
        failure = f"mã thoát {returncode}"
        if message:
            failure += f": {message}"
        return AiReply(tool, None, failure)

    response = _parse_response(tool, stdout)
    return response


def _run_child(args: list[str], process_input: str | None, cwd: str, timeout: int) -> tuple[int, str, str]:
    """Run the child in its own process group; on timeout or Ctrl+C kill the whole group, then re-raise.

    Measured with gemini 0.57.0: `gemini` re-spawns itself as a second node process. `subprocess.run` kills only the
    direct child on timeout, and the second one kept calling the API after the report was written.
    """
    with subprocess.Popen(
        args,
        stdin=subprocess.PIPE if process_input is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=cwd,
        start_new_session=os.name != "nt",
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
    ) as process:
        try:
            stdout, stderr = process.communicate(process_input, timeout=timeout)
        except BaseException:
            _kill_tree(process)
            raise
        return process.returncode, stdout, stderr


def _kill_tree(process: subprocess.Popen[str]) -> None:
    if os.name == "nt":
        with contextlib.suppress(OSError):
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, check=False)
    else:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(process.pid, signal.SIGKILL)
    process.kill()


def _resolve(tool: str) -> tuple[str, ...] | None:
    executable = shutil.which(tool)
    if executable:
        return (executable,)
    if tool == "agy":
        directory = Path.home() / ".gemini" / "bin"
        for name in ("agy", "agy.exe"):
            candidate = directory / name
            if candidate.is_file():
                return (str(candidate),)
    return None


def _arguments(
    tool: str, executable: tuple[str, ...], prompt: str, model: str | None, timeout: int
) -> tuple[list[str], str | None, list[str]]:
    if tool == "gemini":
        args = [*executable, "-p", "", "-o", "json", "--approval-mode", "plan", "--skip-trust"]
        if model:
            args.extend(("-m", model))
        return args, prompt, args.copy()

    args = [*executable, "-p", prompt, "--mode", "plan", "--output-format", "json", "--print-timeout", f"{timeout}s"]
    logged_args = [
        *executable,
        "-p",
        "<prompt>",
        "--mode",
        "plan",
        "--output-format",
        "json",
        "--print-timeout",
        f"{timeout}s",
    ]
    if model:
        args.extend(("--model", model))
        logged_args.extend(("--model", model))
    return args, None, logged_args


def _parse_response(tool: str, stdout: str) -> AiReply:
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError:
        return AiReply(tool, None, "kết quả không phải JSON")
    if not isinstance(value, dict):
        return AiReply(tool, None, "kết quả không phải JSON")
    if isinstance(value.get("error"), dict):
        return AiReply(tool, None, f"lỗi: {_message(value['error'])}")
    if tool == "agy" and value.get("status") != "SUCCESS":
        return AiReply(tool, None, f"trạng thái {value.get('status')}")
    response = value.get("response")
    if not isinstance(response, str):
        return AiReply(tool, None, "không có trường response")
    return AiReply(tool, response, None)


def _error_message(text: str) -> str | None:
    """`error.message` from a CLI error, even after warning lines or nested in an escaped JSON string.

    Measured with gemini 0.57.0: stderr starts with warnings ("Ripgrep is not available…", "[STARTUP] …") before the
    JSON object, and an API error arrives as one text line whose inner JSON is escaped several times.
    """
    decoder = json.JSONDecoder()
    for match in _OBJECT_START.finditer(text):
        try:
            value, _ = decoder.raw_decode(text, match.end() - 1)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and isinstance(value.get("error"), dict):
            return _message(value["error"])
    found = _MESSAGE.findall(text)
    return clean(found[-1])[:150] if found else None


def _message(error: dict[object, object]) -> str:
    text = clean(error.get("message"))
    inner = _MESSAGE.findall(text)
    return clean(inner[-1] if inner else text)[:150]
