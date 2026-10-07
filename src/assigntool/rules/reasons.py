"""Human-readable reasons for proposed assignments."""

from __future__ import annotations

from assigntool.model import Level, Priority
from assigntool.normalize import app_key
from assigntool.rules.familiarity import AppFamiliarity

PREASSIGNED_REASON = "Đã giao sẵn trong file"


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
) -> str:
    """Build the spec section 8 reason in its required order."""
    parts = [_familiarity_text(app, familiarity)]
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
    return " · ".join(parts)


def _familiarity_text(app: str, familiarity: AppFamiliarity) -> str:
    if not app_key(app):
        return "Đơn không có App Name"
    if familiarity.rank == 0 and familiarity.latest is not None:
        latest = familiarity.latest
        when = latest.sprint or f"Tháng {latest.created.month}/{latest.created.year}"
        return f"Làm version gần nhất của {app} ({when}: {latest.title})"
    if familiarity.rank == 1:
        return f"Từng làm {app} ({familiarity.versions} version)"
    return f"Chưa làm {app}"
