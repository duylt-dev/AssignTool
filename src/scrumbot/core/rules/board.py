"""From the standard input to the values the rules use (bot spec §2.3, §2.5): which sprint runs, its orders, the
previous sprint, the history. Pure."""

from __future__ import annotations

import re
from datetime import date, datetime

from scrumbot.core.errors import InputError, NoRunningSprint
from scrumbot.core.inputs import Inputs, SprintInfo, Task
from scrumbot.core.model import HistoryOrder, SprintLabel, SprintRow, SprintView

DONE_KINDS = frozenset({"done", "closed"})

_SPRINT_NAME = re.compile(r"^Sprint\s+(\d+)\b")


def is_done_kind(kind: str) -> bool:
    return kind in DONE_KINDS


def maintain_sprints(sprints: tuple[SprintInfo, ...]) -> tuple[SprintInfo, ...]:
    """The real sprints of folder Maintain (A56), oldest first: `kieu` sprint, a `Sprint N` name, dates, orders."""
    found = [
        sprint
        for sprint in sprints
        if _sprint_like(sprint) and sprint.total > 0 and sprint.start is not None and sprint.end is not None
    ]
    return tuple(sorted(found, key=lambda sprint: (sprint.start, sprint.end, sprint.id)))


def select_current(sprints: tuple[SprintInfo, ...], day: date, wanted: str | None) -> SprintInfo:
    """The running sprint (A59), or the one named by `--sprint-id`."""
    if wanted is not None:
        for sprint in sprints:
            if sprint.id == wanted:
                return sprint
        raise InputError(f"Không có sprint id '{wanted}' trong folder Maintain.")
    running = [
        sprint
        for sprint in sprints
        if _sprint_like(sprint)
        and not sprint.archived
        and sprint.start is not None
        and sprint.end is not None
        and sprint.start <= day <= sprint.end
    ]
    if len(running) > 1 and any(sprint.total > 0 for sprint in running):
        running = [sprint for sprint in running if sprint.total > 0]
    if not running:
        raise NoRunningSprint(
            f"Không có sprint Maintain nào đang chạy ngày {day:%d/%m/%Y}. Chọn sprint bằng --sprint-id."
        )
    if len(running) > 1:
        listed = ", ".join(f"{sprint.name} ({sprint.id})" for sprint in running)
        raise InputError(f"Có nhiều sprint đang chạy ngày {day:%d/%m/%Y}: {listed}. Chọn một bằng --sprint-id.")
    return running[0]


def previous_of(sprints: tuple[SprintInfo, ...], current: SprintInfo) -> SprintInfo | None:
    """The Maintain sprint that ended last before `current` starts (A59); archived ones count."""
    if current.start is None:
        return None
    earlier = [
        sprint
        for sprint in maintain_sprints(sprints)
        if sprint.id != current.id and sprint.end is not None and sprint.end < current.start
    ]
    return max(earlier, key=lambda sprint: (sprint.end, sprint.start)) if earlier else None


def label_of(sprint: SprintInfo) -> SprintLabel:
    """The sprint as a label: its number, dates and name, as the history quotes it (A25)."""
    match = _SPRINT_NAME.match(sprint.name)
    number = int(match[1]) if match else 0
    start = sprint.start or date.min
    return SprintLabel(number, start, sprint.end or start, sprint.name)


def sprint_view(inputs: Inputs, sprint: SprintInfo) -> SprintView:
    """The sprint's items (bot spec §2.5): roots numbered by creation, then subtasks; bugs apart."""
    tasks = inputs.lists.get(sprint.id, ())
    by_id = {task.id: task for task in tasks}
    roots = sorted((task for task in tasks if not task.parent_id and not task.is_bug), key=_created_key)
    stt = {task.id: number for number, task in enumerate(roots, start=1)}
    root_of = {task.id: _root(task, by_id) for task in tasks}

    def nested_key(task: Task) -> tuple[int, datetime, str]:
        return stt.get(root_of[task.id], len(roots) + 1), task.created, task.id

    subtasks = sorted((task for task in tasks if task.parent_id and not task.is_bug), key=nested_key)
    bugs = sorted((task for task in tasks if task.is_bug), key=nested_key)
    numbered = enumerate((*roots, *subtasks, *bugs), start=1)
    rows = [_row(task, number, _kind(task), root_of[task.id]) for number, task in numbered]
    changes = sorted((change for change in inputs.status_changes if change.task_id in by_id), key=lambda c: c.at)
    return SprintView(
        sprint.name,
        label_of(sprint).number,
        sprint.start,
        sprint.end,
        tuple(row for row in rows if row.kind != "Bug"),
        sprint.id,
        tuple(row for row in rows if row.kind == "Bug"),
        tuple(changes),
    )


def history_orders(inputs: Inputs) -> tuple[HistoryOrder, ...]:
    """Every root order of every Maintain sprint and of `history_lists`, once per id, with its sprints (§2.5)."""
    sprints = maintain_sprints(inputs.sprints)
    member_of: dict[str, list[SprintInfo]] = {}
    roots: dict[str, Task] = {}
    for sprint in sprints:
        for task in inputs.lists.get(sprint.id, ()):
            if not task.parent_id and not task.is_bug:
                member_of.setdefault(task.id, []).append(sprint)
                roots.setdefault(task.id, task)
    for list_id in inputs.history_lists:
        for task in inputs.lists.get(list_id, ()):
            if not task.parent_id and not task.is_bug:
                roots.setdefault(task.id, task)
    orders = []
    for task in sorted(roots.values(), key=_created_key):
        labels = tuple(label_of(sprint) for sprint in member_of.get(task.id, ()))
        orders.append(
            HistoryOrder(
                ", ".join(label.name for label in labels),
                task.app,
                task.title,
                task.assignees,
                task.hours,
                task.created.date(),
                labels,
                task.priority_raw,
                task.due,
            )
        )
    return tuple(orders)


def newest_update(inputs: Inputs) -> datetime | None:
    """The freshest `updated` read (D49): how far behind the source is."""
    times = [task.updated for tasks in inputs.lists.values() for task in tasks if task.updated is not None]
    return max(times, default=None)


def _sprint_like(sprint: SprintInfo) -> bool:
    return sprint.kind == "sprint" and _SPRINT_NAME.match(sprint.name) is not None


def _created_key(task: Task) -> tuple[datetime, str]:
    return task.created, task.id


def _root(task: Task, by_id: dict[str, Task]) -> str:
    """The id of the item's nearest root in this list (the item itself for a root)."""
    current, seen = task, {task.id}
    while current.parent_id and current.parent_id in by_id and current.parent_id not in seen:
        current = by_id[current.parent_id]
        seen.add(current.id)
    return current.id


def _kind(task: Task) -> str:
    return "Bug" if task.is_bug else "Subtask" if task.parent_id else "Task"


def _row(task: Task, stt: int, kind: str, root_id: str) -> SprintRow:
    return SprintRow(
        stt,
        task.title,
        kind,
        task.app,
        task.assignees,
        task.status,
        task.priority_raw,
        task.due,
        task.created.date(),
        "",
        task.hours,
        task.id,
        root_id,
        task.status_kind,
        task.updated,
        task.closed,
    )
