"""The memory between runs (bot spec §5, A51): one SQLite file in `state/`. The only module that imports sqlite3.

Tables: kept proposals (A66), AI answers by order id + title (A67), the per-day state of each order (A62),
outcomes of proposals (bot spec §5.2), runs and their report fingerprints (A78), end-of-sprint reports (A72).
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import date, datetime
from pathlib import Path

from scrumbot.errors import InputError
from scrumbot.model import Size, SizeEstimate
from scrumbot.model_risk import KeptProposal, OrderMark, Outcome
from scrumbot.normalize import clean

FILE = "scrumbot.sqlite"
_TIME = "%Y-%m-%d %H:%M:%S"
_SCHEMA = """
CREATE TABLE IF NOT EXISTS proposals (
    order_id TEXT PRIMARY KEY, sprint_id TEXT NOT NULL, code TEXT NOT NULL, reason TEXT NOT NULL,
    backups TEXT NOT NULL, at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ai_answers (
    order_id TEXT NOT NULL, title_key TEXT NOT NULL, size TEXT NOT NULL, reason TEXT NOT NULL, kind TEXT NOT NULL,
    items TEXT NOT NULL, tech_risks TEXT NOT NULL, tool TEXT NOT NULL, at TEXT NOT NULL,
    PRIMARY KEY (order_id, title_key));
CREATE TABLE IF NOT EXISTS order_marks (
    sprint_id TEXT NOT NULL, day TEXT NOT NULL, order_id TEXT NOT NULL, title TEXT NOT NULL, priority TEXT NOT NULL,
    due TEXT, codes TEXT NOT NULL, at TEXT NOT NULL, PRIMARY KEY (sprint_id, day, order_id));
CREATE TABLE IF NOT EXISTS outcomes (
    order_id TEXT PRIMARY KEY, sprint_id TEXT NOT NULL, title TEXT NOT NULL, proposed TEXT NOT NULL,
    actual TEXT NOT NULL, at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs (
    at TEXT NOT NULL, sprint_id TEXT NOT NULL, kind TEXT NOT NULL, fingerprint TEXT NOT NULL,
    high_risks TEXT NOT NULL, proposed TEXT NOT NULL, report TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sprint_ends (sprint_id TEXT PRIMARY KEY, at TEXT NOT NULL, report TEXT NOT NULL);
"""


class StateStore:
    """Open with `StateStore(folder)`; every method commits its own change, so a crash loses at most one step."""

    def __init__(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / FILE
        try:
            with closing(self._connect()) as connection:
                connection.executescript(_SCHEMA)
        except sqlite3.DatabaseError as error:
            raise InputError(f"Không mở được bộ nhớ '{self.path}': {error}") from error

    # A66: kept proposals
    def proposals(self, sprint_id: str) -> tuple[KeptProposal, ...]:
        rows = self._all("SELECT order_id, code, reason, backups, at FROM proposals WHERE sprint_id = ?", (sprint_id,))
        return tuple(KeptProposal(row[0], row[1], row[2], tuple(json.loads(row[3])), _time(row[4])) for row in rows)

    def save_proposals(self, sprint_id: str, proposals: tuple[KeptProposal, ...]) -> None:
        self._many(
            "INSERT OR REPLACE INTO proposals VALUES (?, ?, ?, ?, ?, ?)",
            [
                (item.order_id, sprint_id, item.code, item.reason, json.dumps(item.backups), item.at.strftime(_TIME))
                for item in proposals
            ],
        )

    def forget_proposals(self, order_ids: tuple[str, ...]) -> None:
        self._many("DELETE FROM proposals WHERE order_id = ?", [(order_id,) for order_id in order_ids])

    # A67: AI answers
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

    # A62: per-day state of the orders
    def baseline(self, sprint_id: str, today: date) -> tuple[tuple[OrderMark, ...], datetime] | None:
        """The latest state stored before `today` for this sprint, with the time it was stored."""
        row = self._one(
            "SELECT day FROM order_marks WHERE sprint_id = ? AND day < ? ORDER BY day DESC LIMIT 1",
            (sprint_id, today.isoformat()),
        )
        if row is None:
            return None
        rows = self._all(
            "SELECT order_id, title, priority, due, codes, at FROM order_marks WHERE sprint_id = ? AND day = ?",
            (sprint_id, row[0]),
        )
        marks = tuple(
            OrderMark(r[0], r[1], r[2], date.fromisoformat(r[3]) if r[3] else None, tuple(json.loads(r[4])))
            for r in rows
        )
        return marks, max(_time(r[5]) for r in rows)

    def save_marks(self, sprint_id: str, marks: tuple[OrderMark, ...], now: datetime) -> None:
        """Replace today's state of the sprint; keep only the two latest days."""
        day = now.date().isoformat()
        with closing(self._connect()) as connection, connection:
            connection.execute("DELETE FROM order_marks WHERE sprint_id = ? AND day = ?", (sprint_id, day))
            connection.executemany(
                "INSERT INTO order_marks VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        sprint_id,
                        day,
                        mark.id,
                        mark.title,
                        mark.priority_raw,
                        mark.due.isoformat() if mark.due else None,
                        json.dumps(mark.codes),
                        now.strftime(_TIME),
                    )
                    for mark in marks
                ],
            )
            connection.execute(
                "DELETE FROM order_marks WHERE sprint_id = ? AND day NOT IN "
                "(SELECT DISTINCT day FROM order_marks WHERE sprint_id = ? ORDER BY day DESC LIMIT 2)",
                (sprint_id, sprint_id),
            )

    # bot spec §5.2: outcomes
    def save_outcomes(self, sprint_id: str, outcomes: tuple[Outcome, ...]) -> None:
        self._many(
            "INSERT OR REPLACE INTO outcomes VALUES (?, ?, ?, ?, ?, ?)",
            [
                (item.order_id, sprint_id, item.title, item.proposed, json.dumps(item.actual), item.at.strftime(_TIME))
                for item in outcomes
            ],
        )

    def outcomes(self, sprint_id: str, day: date | None = None) -> tuple[Outcome, ...]:
        """Outcomes of a sprint, or only those recorded on `day`."""
        rows = self._all(
            "SELECT order_id, title, proposed, actual, at FROM outcomes WHERE sprint_id = ? ORDER BY at", (sprint_id,)
        )
        found = (Outcome(r[0], r[1], r[2], tuple(json.loads(r[3])), _time(r[4])) for r in rows)
        return tuple(item for item in found if day is None or item.at.date() == day)

    # A78: runs and fingerprints
    def record_run(
        self,
        sprint_id: str,
        kind: str,
        fingerprint: str,
        high_risks: tuple[str, ...],
        proposed: tuple[str, ...],
        report: str,
        now: datetime,
    ) -> None:
        self._many(
            "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    now.strftime(_TIME),
                    sprint_id,
                    kind,
                    fingerprint,
                    json.dumps(high_risks, ensure_ascii=False),
                    json.dumps(proposed),
                    report,
                )
            ],
        )

    def full_run_on(self, day: date) -> bool:
        row = self._one("SELECT 1 FROM runs WHERE kind = 'full' AND substr(at, 1, 10) = ?", (day.isoformat(),))
        return row is not None

    def last_report(self, sprint_id: str) -> tuple[str, tuple[str, ...], tuple[str, ...]] | None:
        """(fingerprint, Cao risks as "code|where", proposed order ids) of the last run that wrote a report."""
        row = self._one(
            "SELECT fingerprint, high_risks, proposed FROM runs WHERE sprint_id = ? AND report != '' "
            "ORDER BY at DESC, rowid DESC LIMIT 1",
            (sprint_id,),
        )
        if row is None:
            return None
        return row[0], tuple(json.loads(row[1])), tuple(json.loads(row[2]))

    # A72: end-of-sprint reports
    def sprint_end_done(self, sprint_id: str) -> bool:
        return self._one("SELECT 1 FROM sprint_ends WHERE sprint_id = ?", (sprint_id,)) is not None

    def record_sprint_end(self, sprint_id: str, report: str, now: datetime) -> None:
        self._many("INSERT OR REPLACE INTO sprint_ends VALUES (?, ?, ?)", [(sprint_id, now.strftime(_TIME), report)])

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=30)

    def _all(self, query: str, params: tuple[object, ...]) -> list[tuple[object, ...]]:
        with closing(self._connect()) as connection:
            return list(connection.execute(query, params))

    def _one(self, query: str, params: tuple[object, ...]) -> tuple[object, ...] | None:
        rows = self._all(query, params)
        return rows[0] if rows else None

    def _many(self, query: str, rows: list[tuple[object, ...]]) -> None:
        if not rows:
            return
        with closing(self._connect()) as connection, connection:
            connection.executemany(query, rows)


def _time(value: object) -> datetime:
    return datetime.strptime(str(value), _TIME)


def _title_key(title: str) -> str:
    return clean(title).casefold()
