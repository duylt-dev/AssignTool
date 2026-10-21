"""The filed order in the running sprint (bot spec §7.2): the description the AI may read and where the order sits in
the sprint. Pure; both steps use it."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import date

from scrumbot.core.errors import InputError
from scrumbot.core.model import OrderDraft, Placement, SprintRow, SprintView
from scrumbot.core.normalize import clean, text_key

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


@dataclass(frozen=True, slots=True)
class PlacedOrder:
    view: SprintView
    stt: int
    how: Placement

    @property
    def row(self) -> SprintRow:
        """The filed order as placed in the sprint."""
        return next(row for row in self.view.rows if row.stt == self.stt)


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


def place_order(view: SprintView, draft: OrderDraft, people: frozenset[str], day: date) -> PlacedOrder:
    """The filed order in the sprint: the root with its `ID`, else the one root with the same title, else a new empty
    root filed on `day`, numbered after the roots (subtasks and bugs move one STT down)."""
    description = scrub(draft.description, people)
    roots = [row for row in view.rows if row.kind == "Task"]
    if draft.order_id:
        found = next((row for row in roots if row.id == draft.order_id), None)
        if found is None:
            raise InputError(f"Không có đơn gốc ID '{draft.order_id}' trong {view.name}.")
        return PlacedOrder(_described(view, found, description), found.stt, Placement.BY_ID)
    same = [row for row in roots if text_key(row.title) == text_key(draft.title)]
    if len(same) > 1:
        raise InputError(f"Có {len(same)} đơn tên '{draft.title}' trong {view.name}; ghi ID của đơn vào file đơn.")
    if same:
        return PlacedOrder(_described(view, same[0], description), same[0].stt, Placement.BY_TITLE)
    stt = max((row.stt for row in roots), default=0) + 1
    row = SprintRow(stt, draft.title, "Task", draft.app, (), "", draft.priority_raw, draft.due, day, description)
    moved = tuple(item if item.kind == "Task" or item.stt < stt else _moved(item) for item in view.rows)
    rows = (*(item for item in moved if item.kind == "Task"), row, *(item for item in moved if item.kind != "Task"))
    bugs = tuple(_moved(item) if item.stt >= stt else item for item in view.bugs)
    return PlacedOrder(replace(view, rows=rows, bugs=bugs), stt, Placement.NEW)


def _described(view: SprintView, row: SprintRow, description: str) -> SprintView:
    if not description:
        return view
    rows = tuple(replace(item, description=description) if item is row else item for item in view.rows)
    return replace(view, rows=rows)


def _moved(row: SprintRow) -> SprintRow:
    return replace(row, stt=row.stt + 1)


def _link(url: str) -> str:
    lowered = url.casefold()
    kind = next((label for needle, label in LINK_KINDS if needle in lowered), "")
    return f"[link {kind}]" if kind else "[link]"


def _labelled(label: str, url: str) -> str:
    """A Markdown link keeps its label unless the label is itself a link."""
    text = clean(label)
    return _link(url) if not text or _URL.match(text) else f"{text} {_link(url)}"
