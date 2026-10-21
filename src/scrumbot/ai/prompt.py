"""The AI exchanges (assignment spec §6.4, bot spec §2.6, §7.3): the sizing prompt of `assign`, its reply read into
sizes, types, items and technical risks; the review prompt of `review`, its reply read into the order's type, the
template points its description lacks and questions. Pure: the same prompts and replies work with any AI."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from scrumbot.core.assign.sizing import default_sizes
from scrumbot.core.model import (
    ORDER_KINDS,
    ORDER_TYPES,
    Finding,
    HistoryOrder,
    Order,
    OrderKind,
    Severity,
    Size,
    SizeEstimate,
    SprintRow,
)
from scrumbot.core.normalize import app_key, clean
from scrumbot.core.outcome import AiReview
from scrumbot.core.review.templates import OTHER, TEMPLATES

PROMPT_BUDGET = 30_000
DESC_LIMITS = (600, 200, 0)
MAX_EXAMPLES = 30
MAX_ITEMS = 5
MAX_TECH_RISKS = 2
MAX_QUESTIONS = 2
QUESTION_DESC_LIMIT = 2000  # A102


@dataclass(frozen=True, slots=True)
class AiReply:
    """One AI call: either the model's reply text or a short Vietnamese failure reason."""

    tool: str  # "gemini", "agy", or the name of another AI
    text: str | None
    failure: str | None


_URL = re.compile(r"https?://\S+")
_SIZES = {size.name: size for size in Size}
_FAILED_MESSAGE = "Không ước lượng được độ lớn bằng AI ({}); mọi đơn tính là M (16h)."

_PROMPT = """You estimate the size of change orders for an Android app team.
An order is one release (version) of one app, e.g. "1.1.2 - Fix ads/Fix luồng/Fix UI": the developer who takes it
does every item in the title and the description, then the release goes through QA.
Classify every order below into exactly one class, by the total effort of all its items:
- S (about 4 hours): one small item only: a single crash, a single policy or store change, a text or config change.
- M (about 16 hours): two to three days: one feature-sized item, or two or three small items.
- L (about 32 hours): about a week: several items, e.g. ads or IAP changes together with flow (luồng) or UI changes.
- XL (about 64 hours): more than a week: a new feature, a new SDK, a new app, or many items at once.
Items written as "Fix" (Fix ads, Fix luồng, Fix UI) rework existing screens; each still takes days, not hours.
Judge from the text only. Do not open links, do not use any tool, do not read files.

Past orders of this team with the hours they took (for calibration):
{examples}

Orders to size:
{orders}

For every order also give its type (ads, iap, flow_ui, policy, crash, sdk, feature or other), its work items (at most
5, a few words each, as written in the order) and at most 2 technical risks visible from the text (a new SDK, a store
or policy deadline, a new app), in Vietnamese; give an empty list when none is visible.

Reply with only a JSON array, no prose and no code fence, one element per order:
[{{\"stt\": <STT number>, \"size\": \"S|M|L|XL\", \"reason\": \"<at most 20 words, in Vietnamese>\",
  \"type\": \"<type>\", \"items\": [\"<item>\"], \"tech_risks\": [\"<risk>\"]}}]
"""

_REVIEW_PROMPT = """You review a change order of an Android app team before it is assigned to a developer.
An order is one release (version) of one app: the developer who takes it does every item in the title and the
description, then the release goes through QA.
Judge from the text only. Do not open links, do not use any tool, do not read files. Links appear as [link …] and
people as [người].

The order:
- {app} · {priority} · {title}
- Description: {description}

{templates}
A point is covered when the description gives that information, in any words and any order. A point that starts with
"Sửa thì" or ends with "(nếu có)" counts only when it applies to this order.

Give at most 2 short questions in Vietnamese to the person who filed the order, about what the description leaves
unclear for doing the work. Give an empty list when nothing is unclear.

Reply with only a JSON object, no prose and no code fence:
{{\"type\": \"<type>\", \"missing\": [<point number>], \"questions\": [\"<question>\"]}}
"""
_ALL_TEMPLATES = """The team's process has 8 order types; the description of each must cover the points of its template:
{templates}
Pick the one type that fits the order, or "other" when none fits (for example a new app, which follows its own SRS).
In "missing", list the numbers of the points of that type's template that the description does not cover: an empty
list when it covers them all, and for "other"."""
_ONE_TEMPLATE = """The order's type is {kind} ({label}); its description must cover the points of this template:
{points}
Give "type": "{kind}". In "missing", list the numbers of the points the description does not cover: an empty list
when it covers them all."""


def build_prompt(orders: tuple[Order, ...], history: tuple[HistoryOrder, ...]) -> str:
    """Build a bounded prompt without links or people names."""
    examples = _example_lines(orders, history)
    for limit in DESC_LIMITS:
        prompt = _PROMPT.format(examples=examples, orders=_order_lines(orders, limit))
        if len(prompt) <= PROMPT_BUDGET:
            return prompt
    return prompt


def parse_reply(reply: AiReply, orders: tuple[Order, ...]) -> tuple[dict[int, SizeEstimate], tuple[Finding, ...], str]:
    """Parse a model response, falling back to M for every invalid order."""
    if reply.failure:
        return _failed(reply.tool, reply.failure, orders)

    parsed = _json_array(reply.text)
    if parsed is None:
        return _failed(reply.tool, "không đọc được mảng JSON trong trả lời", orders)

    order_stts = {order.row.stt for order in orders}
    counts: dict[int, int] = {}
    for item in parsed:
        stt = _stt(item)
        if stt in order_stts:
            counts[stt] = counts.get(stt, 0) + 1

    sizes = default_sizes(orders)
    for item in parsed:
        stt = _stt(item)
        if not isinstance(item, dict) or stt not in order_stts or counts.get(stt) != 1:
            continue
        raw_size = item.get("size")
        if not isinstance(raw_size, str) or (size := _SIZES.get(raw_size.strip().upper())) is None:
            continue
        reason = clean(item.get("reason", ""))[:120]
        sizes[stt] = SizeEstimate(
            size,
            reason,
            False,
            _order_type(item.get("type")),
            _strings(item.get("items"), MAX_ITEMS),
            _strings(item.get("tech_risks"), MAX_TECH_RISKS),
        )

    missing = sorted(stt for stt, estimate in sizes.items() if estimate.is_default)
    findings: tuple[Finding, ...] = ()
    if missing:
        listed = ",".join(str(stt) for stt in missing)
        findings = (
            Finding(
                Severity.WARN,
                "SIZE-AI-INVALID",
                reply.tool,
                f"AI không trả độ lớn hợp lệ cho đơn STT {listed}; các đơn này tính là M (16h).",
            ),
        )
    valid = len(orders) - len(missing)
    return sizes, findings, f"AI ({reply.tool}, {valid}/{len(orders)} đơn)"


def build_review_prompt(row: SprintRow, kind: OrderKind | None) -> str:
    """The filed order alone, its description already scrubbed of names and links (bot spec §7.2), with the template
    of `kind`, or all 8 for the AI to pick the type (§7.3, A107)."""
    if kind is not None:
        points = "\n".join(f"{number}. {point}" for number, point in enumerate(TEMPLATES[kind], 1))
        templates = _ONE_TEMPLATE.format(kind=kind.value, label=ORDER_KINDS[kind], points=points)
    else:
        lines = (
            f"- {each.value} ({ORDER_KINDS[each]}): "
            + "; ".join(f"{number}. {point}" for number, point in enumerate(points, 1))
            for each, points in TEMPLATES.items()
        )
        templates = _ALL_TEMPLATES.format(templates="\n".join(lines))
    return _REVIEW_PROMPT.format(
        app=row.app or "(không có app)",
        priority=clean(row.priority_raw) or "(không có ưu tiên)",
        title=row.title,
        description=clean(_URL.sub("[link]", row.description))[:QUESTION_DESC_LIMIT] or "(không có)",
        templates=templates,
    )


def parse_review(reply: AiReply, kind: OrderKind | None) -> AiReview:
    """The type (`kind` when the file gives it), the missing point numbers and at most 2 questions (A102, A107). A
    failure checks nothing; a reply without a `missing` list, or, without `kind`, without a known type, checks
    nothing; one without a `questions` list asks nothing."""
    if reply.failure:
        return AiReview(note=reply.failure)
    found = _json_object(reply.text)
    if found is None:
        return AiReview(note="không đọc được trả lời của AI")
    named = _review_type(found.get("type"))
    missing = _numbers(found.get("missing"))
    known = kind is not None or named not in ("", OTHER)
    questions = found.get("questions")
    answered = isinstance(questions, list)
    return AiReview(
        kind=named,
        checked=known and missing is not None,
        missing=missing or (),
        questions=_strings(questions, MAX_QUESTIONS, width=200),
        answered=answered,
        note=f"AI ({reply.tool})" if answered else "không đọc được câu hỏi trong trả lời của AI",
    )


def _review_type(value: object) -> str:
    """One of the 8 types or `other`; anything else gives "" (A107)."""
    key = clean(value).casefold() if isinstance(value, str) else ""
    return key if key == OTHER or key in {kind.value for kind in OrderKind} else ""


def _numbers(value: object) -> tuple[int, ...] | None:
    """Point numbers, once each and sorted; None when `value` is not a list."""
    if not isinstance(value, list):
        return None
    return tuple(sorted({number for number in map(_number, value) if number is not None}))


def _order_type(value: object) -> str:
    """One of ORDER_TYPES; anything else gives "" and leaves the size untouched (A79)."""
    key = clean(value).casefold() if isinstance(value, str) else ""
    return key if key in ORDER_TYPES else ""


def _strings(value: object, limit: int, width: int = 80) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(text[:width] for text in (clean(item) for item in value if isinstance(item, str)) if text)[:limit]


def _example_lines(orders: tuple[Order, ...], history: tuple[HistoryOrder, ...]) -> str:
    target_apps = {app_key(order.row.app) for order in orders}
    examples = [order for order in history if order.hours is not None and order.hours > 0]
    examples.sort(key=lambda order: (app_key(order.app) not in target_apps, -order.created.toordinal()))
    lines = [f"- {order.app} · {order.title} · {order.hours:g}h" for order in examples[:MAX_EXAMPLES]]
    return "\n".join(lines) if lines else "- (none)"


def _order_lines(orders: tuple[Order, ...], limit: int) -> str:
    lines: list[str] = []
    for order in orders:
        row = order.row
        description = clean(_URL.sub("[link]", row.description))[:limit]
        line = f"- STT {row.stt} · {row.app or '(không có app)'} · {order.priority.name.lower()} · {row.title}"
        if limit and description:
            line += f" · {description}"
        lines.append(line)
    return "\n".join(lines) if lines else "- (none)"


def _json_array(text: str | None) -> list[object] | None:
    if text is None:
        return None
    lines = text.strip().splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    cleaned = "\n".join(lines)
    start, end = cleaned.find("["), cleaned.rfind("]")
    if start < 0 or end < start:
        return None
    try:
        value = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, list) else None


def _json_object(text: str | None) -> dict[str, object] | None:
    if text is None:
        return None
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        value = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _stt(item: object) -> int | None:
    return _number(item.get("stt")) if isinstance(item, dict) else None


def _number(value: object) -> int | None:
    """A whole number, or its digits as text; a boolean is not one."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _failed(
    tool: str, reason: str, orders: tuple[Order, ...]
) -> tuple[dict[int, SizeEstimate], tuple[Finding, ...], str]:
    return (
        default_sizes(orders),
        (Finding(Severity.WARN, "SIZE-AI-FAILED", tool, _FAILED_MESSAGE.format(reason)),),
        f"mặc định M ({reason})",
    )
