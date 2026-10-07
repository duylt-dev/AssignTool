from assigntool.model import Dev, Level, SprintRow, SprintSheet
from assigntool.rules.carry_over import BUSY_STATUSES, carry_over


def test_carry_over_counts_busy_tasks_and_subtasks_once_per_pool_dev() -> None:
    linh = Dev("Linh", "L", Level.MIDDLE, True, ())
    minh = Dev("Minh", "M", Level.MIDDLE, True, ())
    rows = (
        SprintRow(1, "task", "Task", "", ("Linh", "Linh"), "QA - Need Fix", "", None, None, "", ()),
        SprintRow(2, "subtask", "Subtask", "", ("Linh", "Minh"), "pending", "", None, None, "", ()),
        SprintRow(3, "subtask", "Subtask", "", ("Minh",), "internal - cant fix", "", None, None, "", ()),
        SprintRow(4, "subtask", "Subtask", "", ("Minh",), "Internal - Need Fix", "", None, None, "", ()),
        SprintRow(5, "task", "Task", "", ("Linh",), "đã ro", "", None, None, "", ()),
        SprintRow(6, "task", "Task", "", ("Linh", "Minh"), "qa - cant fix", "", None, None, "", ()),
    )
    prev = SprintSheet("Sprint 9", 9, None, None, (), rows)

    assert carry_over(prev, (linh, minh)) == {"L": 2, "M": 2}
    assert carry_over(None, (linh, minh)) == {"L": 0, "M": 0}
    assert len(BUSY_STATUSES) == 8
