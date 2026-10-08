"""Build and parse the AI sizing exchange (assignment spec section 6.4)."""

from __future__ import annotations

import json
import re

from assigntool.model import AiReply, Finding, HistoryOrder, Order, Severity, Size, SizeEstimate
from assigntool.normalize import app_key, clean

PROMPT_BUDGET = 30_000
DESC_LIMITS = (600, 200, 0)
MAX_EXAMPLES = 30

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

Reply with only a JSON array, no prose and no code fence, one element per order:
[{{\"stt\": <STT number>, \"size\": \"S|M|L|XL\", \"reason\": \"<at most 20 words, in Vietnamese>\"}}]
"""


def build_prompt(orders: tuple[Order, ...], history: tuple[HistoryOrder, ...]) -> str:
    """Build a bounded prompt without links or people names."""
    examples = _example_lines(orders, history)
    for limit in DESC_LIMITS:
        prompt = _PROMPT.format(examples=examples, orders=_order_lines(orders, limit))
        if len(prompt) <= PROMPT_BUDGET:
            return prompt
    return prompt


def default_sizes(orders: tuple[Order, ...]) -> dict[int, SizeEstimate]:
    """Give every order the safe M fallback."""
    return {order.row.stt: SizeEstimate(Size.M, "", True) for order in orders}


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
        sizes[stt] = SizeEstimate(size, reason, False)

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


def _stt(item: object) -> int | None:
    if not isinstance(item, dict):
        return None
    value = item.get("stt")
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
