"""Delete what the bot keeps only for a while (A57): snapshots and logs older than 30 days. Clones are never touched."""

from __future__ import annotations

import shutil
from datetime import datetime, timedelta
from pathlib import Path

KEEP_DAYS = 30


def prune(folder: Path, now: datetime, *, keep_days: int = KEEP_DAYS) -> int:
    """Remove the entries of `folder` last modified more than `keep_days` ago; return how many."""
    if not folder.is_dir():
        return 0
    limit = (now - timedelta(days=keep_days)).timestamp()
    removed = 0
    for entry in folder.iterdir():
        if entry.stat().st_mtime >= limit:
            continue
        if entry.is_dir():
            shutil.rmtree(entry, ignore_errors=True)
        else:
            entry.unlink(missing_ok=True)
        removed += 1
    return removed


def remove_tree(folder: Path) -> None:
    shutil.rmtree(folder, ignore_errors=True)


def append_log(folder: Path, now: datetime, line: str) -> Path:
    """One line in `state/log/scrumbot-<YYYY-MM-DD>.log` (bot spec §7 step 6)."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"scrumbot-{now:%Y-%m-%d}.log"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{now:%H:%M} {line}\n")
    return path
