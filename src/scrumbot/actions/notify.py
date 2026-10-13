"""macOS notifications for scheduled runs (bot spec §7, A78). Besides `understanding/ai_cli.py`, the only module that
starts a child process; the text holds a sprint label, counts and a file name, never order text."""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys

_LOGGER = logging.getLogger(__name__)
_SCRIPT = ("on run argv", "display notification (item 1 of argv) with title (item 2 of argv)", "end run")


def notify(message: str, title: str = "scrumbot") -> bool:
    """Show a notification; False (and a log line) when it cannot be shown. A missed notification never fails a run:
    the report is already written."""
    osascript = shutil.which("osascript") if sys.platform == "darwin" else None
    if osascript is None:
        return False
    args = [osascript]
    for line in _SCRIPT:
        args += ["-e", line]
    try:
        done = subprocess.run([*args, message, title], capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        _LOGGER.warning("notification failed: %s", error)
        return False
    if done.returncode:
        _LOGGER.warning("notification failed: exit %s %s", done.returncode, done.stderr.strip())
    return done.returncode == 0
