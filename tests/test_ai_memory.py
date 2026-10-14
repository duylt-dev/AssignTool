"""The AI answers between runs (bot spec §5, A51, A67): they round-trip through a real SQLite file."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from scrumbot.ai.memory import FILE, AnswerMemory
from scrumbot.core.model import Size, SizeEstimate

AT = datetime(2026, 10, 13, 9, 30)


def test_ai_answers_are_found_by_id_and_title_casefolded_and_defaults_are_never_kept(tmp_path: Path) -> None:
    memory = AnswerMemory(tmp_path)
    memory.save_ai_answers(
        {
            ("o1", "1.0.1 - Add Ads"): SizeEstimate(
                Size.L, "Thêm ads", False, "ads", ("Add ads",), ("SDK mới",), questions=("Có màn nào mới?",)
            ),
            ("o2", "x"): SizeEstimate(Size.M, "", True),
        },
        "agy",
        AT,
    )

    found = memory.ai_answers([("o1", "1.0.1 -   add ads"), ("o1", "1.0.2 - Add ads"), ("o2", "x")])

    # questions are never remembered (bot spec §2.6, A90)
    assert found == {
        ("o1", "1.0.1 -   add ads"): SizeEstimate(Size.L, "Thêm ads", False, "ads", ("Add ads",), ("SDK mới",), True)
    }


def test_a_file_written_by_the_old_version_still_opens(tmp_path: Path) -> None:
    """Before D62 the file also held proposals, order states and outcomes; they are left alone."""
    with closing(sqlite3.connect(tmp_path / FILE)) as connection, connection:
        connection.execute("CREATE TABLE proposals (order_id TEXT PRIMARY KEY, code TEXT)")
        connection.execute("INSERT INTO proposals VALUES ('o1', 'LinhNV')")

    memory = AnswerMemory(tmp_path)
    memory.save_ai_answers({("o1", "x"): SizeEstimate(Size.S, "nhỏ", False)}, "agy", AT)

    assert memory.ai_answers([("o1", "x")])[("o1", "x")].size is Size.S
