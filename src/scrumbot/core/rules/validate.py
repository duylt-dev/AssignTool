"""Check the standard input (bot spec §8.3), and turn the sprint's rows into orders with the data findings of
assignment spec §9. Pure."""

from __future__ import annotations

from scrumbot.core.errors import InputError
from scrumbot.core.inputs import Inputs
from scrumbot.core.model import Finding, Order, Priority, Severity, SprintView
from scrumbot.core.normalize import app_key, parse_priority, text_key
from scrumbot.core.rules.team_rules import check_rules


def check_inputs(inputs: Inputs) -> None:
    """What every input must hold, whatever adapter built it: devs, each name and code once, rules naming known devs
    and not in conflict (assignment spec §14.2)."""
    if not inputs.devs:
        raise InputError("Dữ liệu đầu vào không có dev nào.")
    names: set[str] = set()
    codes: set[str] = set()
    for dev in inputs.devs:
        if text_key(dev.name) in names:
            raise InputError(f"Dữ liệu đầu vào trùng tên dev '{dev.name}'.")
        if text_key(dev.code) in codes:
            raise InputError(f"Dữ liệu đầu vào trùng mã dev '{dev.code}'.")
        names.add(text_key(dev.name))
        codes.add(text_key(dev.code))
    check_rules(inputs.rules, inputs.devs, inputs.rules_source)


def orders_and_findings(view: SprintView) -> tuple[tuple[Order, ...], tuple[Finding, ...]]:
    """The orders of the sprint (rows of kind "Task") and their data findings."""
    orders: list[Order] = []
    findings: list[Finding] = []
    for row in view.rows:
        if row.kind != "Task":
            continue
        priority = parse_priority(row.priority_raw)
        where = f"Đơn STT {row.stt}"
        if priority is None:
            findings.append(
                Finding(
                    Severity.WARN,
                    "PRIORITY-UNKNOWN",
                    where,
                    f'Đơn STT {row.stt} có Ưu tiên "{row.priority_raw}" không hợp lệ; coi như normal.',
                )
            )
            priority = Priority.NORMAL
        if not app_key(row.app):
            findings.append(
                Finding(
                    Severity.WARN,
                    "APP-MISSING",
                    where,
                    f"Đơn STT {row.stt} không có App Name; coi như app chưa ai làm.",
                )
            )
        if row.due is None and priority in (Priority.URGENT, Priority.HIGH):
            findings.append(
                Finding(
                    Severity.WARN,
                    "DUE-MISSING",
                    where,
                    f"Đơn STT {row.stt} là đơn {priority.name.lower()} nhưng chưa có Hạn.",
                )
            )
        if row.due is not None and row.created is not None and row.due < row.created:
            findings.append(
                Finding(
                    Severity.WARN,
                    "DUE-BEFORE-CREATED",
                    where,
                    f"Đơn STT {row.stt} có Hạn {row.due:%d/%m/%Y} trước Ngày tạo {row.created:%d/%m/%Y}.",
                )
            )
        orders.append(Order(row, priority))
    return tuple(orders), tuple(findings)
