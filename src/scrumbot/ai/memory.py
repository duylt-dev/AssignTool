"""What is remembered between runs (bot spec §5): the AI answers (A51, A67) and the passed reviews (A101), in one
SQLite file in `state/`. The only module that imports sqlite3. A file written by an older version may hold more
tables; they are left alone."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from scrumbot.core.errors import InputError
from scrumbot.core.model import Size, SizeEstimate
from scrumbot.core.normalize import clean

FILE = "scrumbot.sqlite"
_TIME = "%Y-%m-%d %H:%M:%S"
_SCHEMA = """
CREATE TABLE IF NOT EXISTS ai_answers (
    order_id TEXT NOT NULL, title_key TEXT NOT NULL, size TEXT NOT NULL, reason TEXT NOT NULL, kind TEXT NOT NULL,
    items TEXT NOT NULL, tech_risks TEXT NOT NULL, tool TEXT NOT NULL, at TEXT NOT NULL,
    PRIMARY KEY (order_id, title_key));
CREATE TABLE IF NOT EXISTS reviews (fingerprint TEXT PRIMARY KEY, origin TEXT NOT NULL, at TEXT NOT NULL);
"""


class _Store:
    """The SQLite file of `folder`; every method commits its own change, so a crash loses at most one step."""

    def __init__(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / FILE
        try:
            with closing(self._connect()) as connection:
                connection.executescript(_SCHEMA)
        except sqlite3.DatabaseError as error:
            raise InputError(f"Không mở được bộ nhớ '{self.path}': {error}") from error

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=30)

    def _one(self, query: str, params: tuple[object, ...]) -> tuple[object, ...] | None:
        with closing(self._connect()) as connection:
            return connection.execute(query, params).fetchone()

    def _many(self, query: str, rows: list[tuple[object, ...]]) -> None:
        if not rows:
            return
        with closing(self._connect()) as connection, connection:
            connection.executemany(query, rows)


class AnswerMemory(_Store):
    """The AI answers of `assign`, by order id and title (bot spec §2.6)."""

    def ai_answers(self, keys: list[tuple[str, str]]) -> dict[tuple[str, str], SizeEstimate]:
        """Remembered answers for (order id, title); the estimate is marked `remembered`."""
        found: dict[tuple[str, str], SizeEstimate] = {}
        for order_id, title in keys:
            row = self._one(
                "SELECT size, reason, kind, items, tech_risks FROM ai_answers WHERE order_id = ? AND title_key = ?",
                (order_id, _title_key(title)),
            )
            if row is not None and row[0] in Size.__members__:
                found[(order_id, title)] = SizeEstimate(
                    Size[row[0]], row[1], False, row[2], tuple(json.loads(row[3])), tuple(json.loads(row[4])), True
                )
        return found

    def save_ai_answers(self, answers: dict[tuple[str, str], SizeEstimate], tool: str, now: datetime) -> None:
        self._many(
            "INSERT OR REPLACE INTO ai_answers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    order_id,
                    _title_key(title),
                    estimate.size.name,
                    estimate.reason,
                    estimate.kind,
                    json.dumps(estimate.items, ensure_ascii=False),
                    json.dumps(estimate.tech_risks, ensure_ascii=False),
                    tool,
                    now.strftime(_TIME),
                )
                for (order_id, title), estimate in answers.items()
                if not estimate.is_default
            ],
        )


class ReviewMemory(_Store):
    """The fingerprints of the orders that passed `review` (A101): the `reviewed` of `core.assign`. Never expire."""

    def __contains__(self, fingerprint: object) -> bool:
        return (
            isinstance(fingerprint, str)
            and self._one("SELECT 1 FROM reviews WHERE fingerprint = ?", (fingerprint,)) is not None
        )

    def save(self, fingerprint: str, origin: str, now: datetime) -> None:
        self._many("INSERT OR REPLACE INTO reviews VALUES (?, ?, ?)", [(fingerprint, origin, now.strftime(_TIME))])


def _title_key(title: str) -> str:
    return clean(title).casefold()
