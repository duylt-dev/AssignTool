"""What the run needs besides the API: options, devs and TM rules, AI sizes with memory, the "Tóm tắt" rows and the
terminal lines. The flow never prints; it hands lines to `say`, which `cli.py` binds to print (LLM.md §2)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from scrumbot.actions.state_store import StateStore
from scrumbot.model import Dev, Finding, HistoryOrder, Order, Result, Severity, SizeEstimate, Source, TeamRule
from scrumbot.model_risk import RiskLevel
from scrumbot.rules.team_rules import check_rules
from scrumbot.sources.dev_reader import read_devs
from scrumbot.sources.discovery import devs_path, rules_path
from scrumbot.sources.rules_reader import read_rules
from scrumbot.understanding import ai_cli
from scrumbot.understanding.sizing import build_prompt, default_sizes, parse_reply

Say = Callable[[str], None]


@dataclass(frozen=True)
class Options:
    """The command line, already parsed (bot spec §1)."""

    input_dir: Path = Path("input")
    devs: str | None = None
    rules: str | None = None
    state_dir: Path = Path("state")
    out_dir: Path = Path("output")
    today: date | None = None  # --today
    sprint_id: str | None = None  # --sprint-id
    ai: str = "gemini"
    ai_model: str | None = None
    ai_timeout: int = 180
    env_file: Path = Path(".env")


def load_team(options: Options) -> tuple[tuple[Dev, ...], tuple[TeamRule, ...], Path | None]:
    """devs.xlsx and the TM rules file checked against it (assignment spec §4, §14)."""
    devs = read_devs(devs_path(options.input_dir, options.devs))
    path = rules_path(options.input_dir, options.rules)
    rules: tuple[TeamRule, ...] = ()
    if path is not None:
        rules = read_rules(path)
        check_rules(rules, devs, str(path))
    return devs, rules, path


def rules_note(path: Path | None, rules: tuple[TeamRule, ...], detail: str) -> str:
    return "Luật TM: không có" if path is None else f"Luật TM: file {path.name} ({len(rules)} luật, {detail})"


def sizes_for(
    orders: tuple[Order, ...],
    examples: tuple[HistoryOrder, ...],
    options: Options,
    store: StateStore | None,
    say: Say,
    now: datetime,
) -> tuple[dict[int, SizeEstimate], tuple[Finding, ...], str]:
    """AI sizes, from the memory when an answer for the same order id and title exists (A67)."""
    if options.ai == "off":
        return default_sizes(orders), (), "tắt AI (mọi đơn M)"
    if not orders:
        return {}, (), "không có đơn"
    keys = [(order.row.id, order.row.title) for order in orders if order.row.id]
    remembered = store.ai_answers(keys) if store is not None else {}
    sizes = {
        order.row.stt: remembered[key] for order in orders if (key := (order.row.id, order.row.title)) in remembered
    }
    todo = tuple(order for order in orders if order.row.stt not in sizes)
    if not todo:
        return sizes, (), f"AI (bộ nhớ, {len(sizes)}/{len(orders)} đơn)"
    say(f"Đang ước lượng độ lớn bằng {options.ai}… ({len(todo)} đơn)")
    prompt = build_prompt(todo, examples)
    reply = ai_cli.run_ai(options.ai, prompt, model=options.ai_model, timeout=options.ai_timeout)
    fresh, findings, note = parse_reply(reply, todo)
    if store is not None and reply.failure is None:
        store.save_ai_answers({(o.row.id, o.row.title): fresh[o.row.stt] for o in todo if o.row.id}, options.ai, now)
    sizes.update(fresh)
    if remembered:
        valid = sum(not estimate.is_default for estimate in sizes.values())
        note = (
            f"{note}; {len(remembered)} đơn từ bộ nhớ"
            if reply.failure is not None
            else f"AI ({options.ai}, {valid}/{len(orders)} đơn; {len(remembered)} từ bộ nhớ)"
        )
    return sizes, findings, note


def description_note(result: Result) -> str:
    """D50: how many orders the AI sized from the title alone, since the API returns no description."""
    count = sum(
        not item.size.is_default and not item.order.row.description for item in result.assignments if item.order.row.id
    )
    return f"Hệ thống chưa trả mô tả: {count} đơn được ước lượng chỉ theo tiêu đề." if count else ""


def summary_rows(
    result: Result,
    *,
    label: str,
    start: date | None,
    end: date | None,
    run_at: datetime,
    today_given: bool,
    source: str,
    freshness: datetime | None,
    note: str,
    backlog: tuple[int, int] | None,
) -> tuple[tuple[str, str], ...]:
    """Rows of the "Tóm tắt" sheet (bot spec §6)."""
    proposed = [item for item in result.assignments if item.source is Source.PROPOSED]
    kept = sum(item.kept for item in proposed)
    warn = sum(finding.severity is Severity.WARN for finding in result.findings)
    dates = f" ({start:%d/%m/%Y} – {end:%d/%m/%Y})" if start and end else ""
    rows = [
        ("Sprint", f"{label}{dates}"),
        ("Ngày chạy", f"{run_at:%d/%m/%Y %H:%M}" + (" (--today)" if today_given else "")),
        ("Nguồn", source),
    ]
    if freshness is not None:
        rows.append(("Dữ liệu mới nhất", f"{freshness:%d/%m/%Y %H:%M}"))
    rows.append(("Độ lớn", result.sizing_note))
    if note:
        rows.append(("Mô tả đơn", note))
    rows += [
        (
            "Đơn",
            f"{len(result.assignments)} đơn · giao sẵn {len(result.assignments) - len(proposed)} · bot đề xuất "
            f"{len(proposed)} (mới {len(proposed) - kept}, giữ từ lần trước {kept})",
        ),
        ("Rủi ro", risk_counts(result)),
        ("Cảnh báo dữ liệu", f"{warn} WARN · {len(result.findings) - warn} INFO"),
        ("Thay đổi", f"{len(result.changes)} dòng" if result.change_note.startswith("So với") else result.change_note),
    ]
    if backlog is not None:
        rows.append(
            (
                "Đơn trống chưa vào sprint",
                f"{backlog[0]} đơn ở list Tech manager, {backlog[1]} đơn tạo trong 30 ngày gần đây",
            )
        )
    rows += [
        ("Rủi ro cao", f"{risk.code} · {risk.where}: {risk.problem}")
        for risk in result.risks
        if risk.level is RiskLevel.HIGH
    ]
    return tuple(rows)


def risk_counts(result: Result) -> str:
    counts = [sum(risk.level is level for risk in result.risks) for level in RiskLevel]
    return f"{counts[0]} cao · {counts[1]} trung bình · {counts[2]} thấp"


def result_lines(result: Result, path: Path | None) -> list[str]:
    """The terminal lines of assignment spec §11 and bot spec §6."""
    warn = sum(finding.severity is Severity.WARN for finding in result.findings)
    proposed = [item for item in result.assignments if item.source is Source.PROPOSED]
    lines = [
        f"Sprint: {result.sheet_name}",
        f"Độ lớn: {result.sizing_note}",
        f"Đơn: {len(result.assignments)} · giao sẵn: {len(result.assignments) - len(proposed)} · "
        f"tool đề xuất: {len(proposed)} · cảnh báo: {warn} WARN, {len(result.findings) - warn} INFO",
    ]
    for item in proposed:
        row = item.order.row
        backups = ", ".join(item.backups) or "không có"
        kept = " (giữ đề xuất)" if item.kept else ""
        lines.append(
            f"STT {row.stt} · {row.app or '(không có app)'} {row.title} [{item.size.size.name}] → "
            f"{item.pic_codes[0]}{kept} (dự phòng: {backups})"
        )
    lines += [f"WARN {f.code}: {f.message}" for f in result.findings if f.severity is Severity.WARN]
    lines.append(f"Rủi ro: {risk_counts(result)}")
    lines += [f"CAO {risk.code} {risk.where}: {risk.problem}" for risk in result.risks if risk.level is RiskLevel.HIGH]
    if result.change_note.startswith("So với"):
        lines.append(f"Thay đổi: {len(result.changes)} dòng")
    if path is not None:
        lines.append(f"Báo cáo: {path}")
    return lines
