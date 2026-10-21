"""Deterministic PIC selection (assignment spec section 7), with the TM rules of section 14."""

from __future__ import annotations

from scrumbot.core.assign.familiarity import FamiliarityIndex
from scrumbot.core.assign.reasons import PREASSIGNED_REASON, blocked_text, proposed_reason, rule_lead
from scrumbot.core.model import Assignment, Dev, Level, Order, Priority, SizeEstimate, Source, TeamRule
from scrumbot.core.normalize import text_key
from scrumbot.core.sprint.team_rules import blocking_rule, names, pin_rule, prefer_rule

GAP_ORDERS = 1  # D26: a dev may hold at most one order more than the least-loaded dev

_Key = tuple[int, int, int, int, int, int, int, str]


def assign(
    orders: tuple[Order, ...],
    sizes: dict[int, SizeEstimate],
    pool: tuple[Dev, ...],
    fam: FamiliarityIndex,
    carry: dict[str, int],
    leave: dict[str, int],
    prev_name: str,
    rules: tuple[TeamRule, ...] = (),
) -> tuple[Assignment, ...]:
    """Keep pre-assignments, then choose PICs lexicographically for the rest. `rules` are the TM rules in force."""
    loads = {dev.code: 0 for dev in pool}
    counts = {dev.code: 0 for dev in pool}
    assignments: dict[int, Assignment] = {}

    for order in orders:
        if not order.row.assignees:
            continue
        assignee_keys = {text_key(name) for name in order.row.assignees}
        pic_codes = tuple(dev.code for dev in pool if text_key(dev.name) in assignee_keys)
        for code in pic_codes:
            loads[code] += sizes[order.row.stt].size.value
            counts[code] += 1
        assignments[order.row.stt] = Assignment(
            order, sizes[order.row.stt], Source.PREASSIGNED, order.row.assignees, pic_codes, PREASSIGNED_REASON, ()
        )

    pending = sorted((order for order in orders if not order.row.assignees), key=_processing_key)
    for order in pending:
        size = sizes[order.row.stt]
        chosen = _choose(order, size, pool, fam, carry, leave, prev_name, rules, loads, counts)
        assignments[order.row.stt] = chosen
        loads[chosen.pic_codes[0]] += size.size.value
        counts[chosen.pic_codes[0]] += 1
    return tuple(assignments[stt] for stt in sorted(assignments))


def _choose(
    order: Order,
    size: SizeEstimate,
    pool: tuple[Dev, ...],
    fam: FamiliarityIndex,
    carry: dict[str, int],
    leave: dict[str, int],
    prev_name: str,
    rules: tuple[TeamRule, ...],
    loads: dict[str, int],
    counts: dict[str, int],
) -> Assignment:
    """One order of spec §7 step 3, given the loads and order counts so far."""
    app = order.row.app
    blocked = {dev.code: rule for dev in pool if (rule := blocking_rule(rules, dev, app, counts[dev.code]))}
    candidates = tuple(dev for dev in pool if dev.code not in blocked)
    relaxed = not candidates  # A31: the rules left nobody, so EXCLUDE and MAX_ORDERS are ignored for this order
    if relaxed:
        candidates, blocked = pool, {}
    is_new_app = fam.is_new_app(app)
    needs_senior = order.priority in (Priority.URGENT, Priority.HIGH) or is_new_app

    def key(dev: Dev) -> _Key:
        return (
            0 if prefer_rule(rules, dev, app) else 1,
            fam.get(dev, app).rank,
            0 if not needs_senior or dev.level >= Level.MIDDLE else 1,
            loads[dev.code],
            carry[dev.code],
            leave[dev.code],
            -dev.level,
            dev.code,
        )

    def backups(pic: Dev) -> tuple[str, ...]:
        return tuple(dev.code for dev in sorted((dev for dev in candidates if dev != pic), key=key)[:2])

    def reason(pic: Dev, **parts: object) -> str:
        return proposed_reason(
            app=app,
            familiarity=fam.get(pic, app),
            level=pic.level,
            priority=order.priority,
            load_hours=loads[pic.code],
            load_orders=counts[pic.code],
            carry_over=carry[pic.code],
            prev_name=prev_name,
            leave_days=leave[pic.code],
            **parts,
        )

    pin = pin_rule(rules, app)
    pinned = next((dev for dev in candidates if pin is not None and names(pin, dev)), None)
    if pin is not None and pinned is not None:
        text = reason(pinned, senior_cause=None, cap_excluded=(), lead=rule_lead(pin, pinned.code, app))
        return Assignment(
            order, size, Source.PROPOSED, (pinned.name,), (pinned.code,), text, backups(pinned), (pin.line,), relaxed
        )

    cap_limit = min(counts[dev.code] for dev in candidates) + GAP_ORDERS
    capped = tuple(dev for dev in candidates if counts[dev.code] <= cap_limit)
    pic = min(capped, key=key)
    pic_key = key(pic)
    beaten = [(dev, _first_better(key(dev), pic_key)) for dev in sorted(set(candidates) - set(capped), key=key)]
    preferred = tuple(
        (dev.code, rule.line, counts[dev.code])
        for dev, part in beaten
        if part == 0 and (rule := prefer_rule(rules, dev, app)) is not None
    )
    shut_out = [
        (dev, blocked[dev.code])
        for dev in sorted(pool, key=key)
        if dev.code in blocked and (key(dev) < pic_key or (pin is not None and names(pin, dev)))
    ]
    lead_rule = prefer_rule(rules, pic, app)
    senior_cause = (
        "priority" if order.priority in (Priority.URGENT, Priority.HIGH) else "new_app" if is_new_app else None
    )
    text = reason(
        pic,
        senior_cause=senior_cause,
        cap_excluded=tuple((dev.code, counts[dev.code]) for dev, part in beaten if part == 1),
        cap_excluded_senior=tuple((dev.code, counts[dev.code]) for dev, part in beaten if part == 2),
        lead=rule_lead(lead_rule, pic.code, app) if lead_rule is not None else "",
        cap_excluded_preferred=preferred,
        blocked=tuple(blocked_text(dev.code, rule, counts[dev.code]) for dev, rule in shut_out),
    )
    lines = {line for _, line, _ in preferred} | {rule.line for _, rule in shut_out}
    if lead_rule is not None:
        lines.add(lead_rule.line)
    return Assignment(
        order, size, Source.PROPOSED, (pic.name,), (pic.code,), text, backups(pic), tuple(sorted(lines)), relaxed
    )


def _first_better(candidate: _Key, pic: _Key) -> int | None:
    """Index of the first key part where `candidate` beats the PIC, or None when it does not beat the PIC."""
    if candidate >= pic:
        return None
    return next(index for index, (mine, theirs) in enumerate(zip(candidate, pic, strict=True)) if mine != theirs)


def _processing_key(order: Order) -> tuple[Priority, bool, object, bool, object, int]:
    row = order.row
    return order.priority, row.due is None, row.due, row.created is None, row.created, row.stt
