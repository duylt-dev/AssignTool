"""An order file in the target sprint (bot spec §7): the description the AI may read, where the order sits in the
sprint, and what the order report shows. Pure."""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass, replace
from datetime import date, datetime

from scrumbot.errors import InputError
from scrumbot.model import (
    Assignment,
    Dev,
    Finding,
    HistoryOrder,
    Level,
    OrderDraft,
    Result,
    Source,
    SprintRow,
    SprintSheet,
)
from scrumbot.model_risk import Risk
from scrumbot.normalize import app_key, clean, text_key
from scrumbot.rules.familiarity import FamiliarityIndex
from scrumbot.rules.pipeline import Team

PERSON = "[người]"
LINK_KINDS = (
    ("figma.com", "Figma"),
    ("docs.google.com/document", "Google Docs"),
    ("docs.google.com/spreadsheets", "Google Sheets"),
    ("docs.google.com/presentation", "Google Slides"),
    ("drive.google.com", "Google Drive"),
)

_MD_LINK = re.compile(r"\[([^\]]*)\]\((https?://[^)\s]+)\)")
_URL = re.compile(r"https?://[^\s)\]>]+")
_WORD = re.compile(r"\w+")


class Placement(enum.Enum):
    """How the order file met the sprint (bot spec §7.2)."""

    NEW = "new"
    BY_ID = "id"
    BY_TITLE = "title"


@dataclass(frozen=True, slots=True)
class Placed:
    sheet: SprintSheet
    stt: int
    how: Placement


@dataclass(frozen=True, slots=True)
class DevLine:
    """One row of the dev table of the order report (bot spec §7.3)."""

    code: str
    level: Level
    familiarity: str
    orders: int
    open_hours: int
    capacity: int | None
    carry_over: int
    leave_days: int
    role: str


@dataclass(frozen=True, slots=True)
class OrderReport:
    item: Assignment
    how: Placement
    risks: tuple[Risk, ...]  # of the order, of its PIC and of the sprint
    devs: tuple[DevLine, ...]
    findings: tuple[Finding, ...]  # every finding not about another order


def scrub(text: str, people: frozenset[str]) -> str:
    """The description as the AI may read it (A18, R9): links become `[link <kind>]`, known names and words shaped
    like a person's code (`TestBA`) become `[người]`, whitespace is collapsed."""
    text = _MD_LINK.sub(lambda m: _labelled(m[1], m[2]), text)
    text = _URL.sub(lambda m: _link(m[0]), text)
    for name in sorted({clean(person) for person in people if clean(person)}, key=len, reverse=True):
        text = re.sub(rf"(?<!\w){re.escape(name)}(?!\w)", PERSON, text, flags=re.IGNORECASE)
    text = _WORD.sub(lambda m: PERSON if looks_like_code(m[0]) else m[0], text)
    return clean(text)


def looks_like_code(word: str) -> bool:
    """`TestBA`, `TiếnBV`: a capitalised word ending in one to three capitals. `GameUI` matches too (small cost)."""
    end = len(word)
    while end > 0 and word[end - 1].isupper():
        end -= 1
    head, tail = word[:end], word[end:]
    return 1 <= len(tail) <= 3 and len(head) >= 2 and head[0].isupper() and head[1:].isalpha() and head[1:].islower()


def place(sheet: SprintSheet, draft: OrderDraft, people: frozenset[str], day: date, now: datetime) -> Placed:
    """The order of the file in the sprint: the root with its `ID`, else the one root with the same title, else a
    new empty root filed on `day`, numbered after the roots (subtasks and bugs move one STT down)."""
    description = scrub(draft.description, people)
    roots = [row for row in sheet.rows if row.kind == "Task"]
    if draft.order_id:
        found = next((row for row in roots if row.id == draft.order_id), None)
        if found is None:
            raise InputError(f"Không có đơn gốc ID '{draft.order_id}' trong {sheet.name}.")
        return Placed(_described(sheet, found, description), found.stt, Placement.BY_ID)
    same = [row for row in roots if text_key(row.title) == text_key(draft.title)]
    if len(same) > 1:
        raise InputError(f"Có {len(same)} đơn tên '{draft.title}' trong {sheet.name}; ghi ID của đơn vào file đơn.")
    if same:
        return Placed(_described(sheet, same[0], description), same[0].stt, Placement.BY_TITLE)
    stt = max((row.stt for row in roots), default=0) + 1
    cells = (stt, "", draft.title, draft.app, "", "", draft.priority_raw, draft.due, day, 0, 0)
    row = SprintRow(
        stt, draft.title, "Task", draft.app, (), "", draft.priority_raw, draft.due, day, description, cells,
        created_at=now,
    )  # fmt: skip
    moved = tuple(item if item.kind == "Task" or item.stt < stt else _moved(item) for item in sheet.rows)
    rows = (*(item for item in moved if item.kind == "Task"), row, *(item for item in moved if item.kind != "Task"))
    bugs = tuple(_moved(item) if item.stt >= stt else item for item in sheet.bugs)
    return Placed(replace(sheet, rows=rows, bugs=bugs), stt, Placement.NEW)


def order_report(result: Result, placed: Placed, team: Team, history: tuple[HistoryOrder, ...]) -> OrderReport:
    """What the order report shows (bot spec §7.3)."""
    item = next(entry for entry in result.assignments if entry.order.row.stt == placed.stt)
    codes = set(item.pic_codes)
    risks = tuple(
        risk
        for risk in result.risks
        if risk.stt == placed.stt or (risk.stt is None and (risk.where in codes or risk.where == result.sheet_name))
    )
    app = item.order.row.app
    fam = FamiliarityIndex.build(history, team.pool)
    roles = {code: "Dự phòng " + str(number) for number, code in enumerate(item.backups, start=1)}
    roles.update({code: "PIC" if item.source is Source.PROPOSED else "Người làm" for code in item.pic_codes})
    roles.update({dev.code: "Nghỉ hết các ngày còn lại" for dev in team.off_rest})
    roles.update({dev.code: "Nghỉ cả sprint" for dev in team.removed})
    devs = tuple(
        DevLine(
            summary.dev.code,
            summary.dev.level,
            _familiarity(fam, summary.dev, app),
            summary.preassigned + summary.proposed,
            summary.open_hours,
            summary.capacity,
            summary.carry_over,
            summary.leave_days,
            roles.get(summary.dev.code, ""),
        )
        for summary in result.devs
    )
    others = {f"Đơn STT {entry.order.row.stt}" for entry in result.assignments if entry.order.row.stt != placed.stt}
    findings = tuple(finding for finding in result.findings if finding.where not in others)
    return OrderReport(item, placed.how, risks, devs, findings)


def _familiarity(fam: FamiliarityIndex, dev: Dev, app: str) -> str:
    if not app_key(app):
        return "—"
    found = fam.get(dev, app)
    if found.rank == 0:
        return "Làm version gần nhất"
    if found.rank == 1:
        return f"Từng làm ({found.versions} version)"
    return "Chưa làm"


def _described(sheet: SprintSheet, row: SprintRow, description: str) -> SprintSheet:
    if not description:
        return sheet
    rows = tuple(replace(item, description=description) if item is row else item for item in sheet.rows)
    return replace(sheet, rows=rows)


def _moved(row: SprintRow) -> SprintRow:
    return replace(row, stt=row.stt + 1, cells=(row.stt + 1, *row.cells[1:]))


def _link(url: str) -> str:
    lowered = url.casefold()
    kind = next((label for needle, label in LINK_KINDS if needle in lowered), "")
    return f"[link {kind}]" if kind else "[link]"


def _labelled(label: str, url: str) -> str:
    """A Markdown link keeps its label unless the label is itself a link."""
    text = clean(label)
    return _link(url) if not text or _URL.match(text) else f"{text} {_link(url)}"
