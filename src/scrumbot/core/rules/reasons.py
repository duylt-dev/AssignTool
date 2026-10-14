"""Human-readable reasons for proposed assignments."""

from __future__ import annotations

from scrumbot.core.model import Level, Priority, RuleKind, TeamRule
from scrumbot.core.normalize import app_key
from scrumbot.core.rules.familiarity import AppFamiliarity

PREASSIGNED_REASON = "Đã có người làm trên hệ thống"


def proposed_reason(
    *,
    app: str,
    familiarity: AppFamiliarity,
    level: Level,
    senior_cause: str | None,
    priority: Priority,
    load_hours: int,
    load_orders: int,
    carry_over: int,
    prev_name: str,
    leave_days: int,
    cap_excluded: tuple[tuple[str, int], ...],  # (code, orders held) of devs outside the load cap
    cap_excluded_senior: tuple[tuple[str, int], ...] = (),
    lead: str = "",  # part 0: rule_lead() of the pin or preference that chose the PIC
    cap_excluded_preferred: tuple[tuple[str, int, int], ...] = (),  # (code, rule line, orders held)
    blocked: tuple[str, ...] = (),  # part 9: blocked_text() of devs the TM rules kept off the order
) -> str:
    """Build the spec section 8 reason in its required order."""
    parts = [lead] if lead else []
    parts.append(familiarity_text(app, familiarity))
    if senior_cause == "priority" and level >= Level.MIDDLE:
        parts.append(f"Đơn {priority.name.lower()} → ưu tiên middle trở lên")
    elif senior_cause == "new_app" and level >= Level.MIDDLE:
        parts.append("App chưa ai trong team làm → ưu tiên middle trở lên")
    parts.append(f"Tải sprint này: {load_hours}h ({load_orders} đơn)")
    parts.append(f"Việc dở {prev_name}: {carry_over}")
    if leave_days > 0:
        parts.append(f"Nghỉ {leave_days} ngày")
    parts.extend(f"{code} quen app hơn nhưng đang có {count} đơn (cân tải)" for code, count in cap_excluded)
    parts.extend(f"{code} là middle trở lên nhưng đang có {count} đơn (cân tải)" for code, count in cap_excluded_senior)
    parts.extend(
        f"{code} được ưu tiên (luật TM dòng {line}) nhưng đang có {count} đơn (cân tải)"
        for code, line, count in cap_excluded_preferred
    )
    parts.extend(blocked)
    return " · ".join(parts)


def rule_lead(rule: TeamRule, code: str, app: str) -> str:
    """Part 0: the pin or preference that chose the PIC, with the TM's note."""
    verb = "chỉ định" if rule.kind is RuleKind.PIN else "ưu tiên"
    text = f"Luật TM dòng {rule.line}: {verb} {code} cho {app}"
    return f"{text} ({rule.note})" if rule.note else text


def blocked_text(code: str, rule: TeamRule, held: int) -> str:
    """Part 9: a dev a `Không giao` or `Tối đa đơn` rule kept off the order."""
    if rule.kind is RuleKind.EXCLUDE:
        return f"{code} không nhận đơn (luật TM dòng {rule.line})"
    return f"{code} đã đủ {held} đơn (luật TM dòng {rule.line})"


def familiarity_text(app: str, familiarity: AppFamiliarity) -> str:
    if not app_key(app):
        return "Đơn không có App Name"
    if familiarity.rank == 0 and familiarity.latest is not None:
        latest = familiarity.latest
        when = latest.sprint or f"Tháng {latest.created.month}/{latest.created.year}"
        return f"Làm version gần nhất của {app} ({when}: {latest.title})"
    if familiarity.rank == 1:
        return f"Từng làm {app} ({familiarity.versions} version)"
    return f"Chưa làm {app}"
