"""`scrumbot replay --clone DIR` (bot spec §8): never calls the API."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from scrumbot.actions.replay_report import write_replay
from scrumbot.actions.state_store import StateStore
from scrumbot.flows.common import Options, Say, load_team, rules_note, sizes_for
from scrumbot.flows.fetch import load_everything
from scrumbot.model import SizeEstimate
from scrumbot.rules.board import history_orders, maintain_sprints, sprint_sheet
from scrumbot.rules.replay import percent, replay_assignments
from scrumbot.rules.replay_risks import replay_risks, scores
from scrumbot.rules.validate import orders_and_findings
from scrumbot.sources.raw_store import StoredSource


def replay(options: Options, clone_dir: Path, say: Say, now: datetime) -> Path:
    devs, rules, rules_file = load_team(options)
    source = StoredSource(clone_dir, None)
    board = load_everything(source, source.fetched_at or now)
    sprints = maintain_sprints(board.sprints)
    sizes: dict[str, SizeEstimate] = {}
    if options.ai != "off":
        store = StateStore(options.state_dir)
        examples = history_orders(board)
        for sprint in sprints:
            orders, _ = orders_and_findings(sprint_sheet(board, sprint))
            estimates, _, _ = sizes_for(orders, examples, options, store, say, now)
            sizes.update({order.row.id: estimates[order.row.stt] for order in orders})
    ai_note = "mọi đơn M" if options.ai == "off" else f"độ lớn AI {options.ai}, có bộ nhớ"
    say(f"Replay: {source.label}, {len(sprints)} sprint ({ai_note})")
    say(rules_note(rules_file, rules, "áp theo ngày giao lại"))
    assignments = replay_assignments(board, devs, rules, sizes)
    risks = replay_risks(board, devs, rules, sizes, ended_before=board.fetched_at.date())
    by_label = {sprint.label: sprint for sprint in risks}
    for sprint in assignments:
        matched = sum(item.matched for item in sprint.orders)
        rate = (
            f"khớp {matched}/{len(sprint.orders)} đơn ({percent(matched, len(sprint.orders))}%)"
            if sprint.orders
            else "không có đơn để so"
        )
        risk = by_label.get(sprint.label)
        tail = ""
        if risk is not None:
            bad = [item for item in risk.outcomes if item.bad]
            tail = (
                f" · kết cục xấu {len(bad)}/{len(risk.outcomes)}, báo trước {sum(bool(item.flagged) for item in bad)}"
            )
        say(f"{sprint.label.name}: {rate}{tail}")
    total = sum(len(sprint.orders) for sprint in assignments)
    matched = sum(item.matched for sprint in assignments for item in sprint.orders)
    score_rows = scores(risks)
    with_history = scores(tuple(sprint for sprint in risks if sprint.has_history))
    say(f"Tổng: khớp {matched}/{total} đơn ({percent(matched, total) if total else 0}%)")
    for name, rows in (("mọi sprint đã kết thúc", score_rows), ("sprint có lịch sử trạng thái", with_history)):
        overall = rows[-1]
        say(
            f"Rủi ro (Cao/Trung bình), {name}: báo đúng {overall.flagged_bad}/{overall.flagged}, "
            f"báo đủ {overall.bad_flagged}/{overall.bad}"
        )
    path = write_replay(assignments, risks, score_rows, with_history, options.out_dir, now)
    say(f"Báo cáo: {path}")
    return path
