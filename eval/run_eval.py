"""Run the tool on the evaluation cases and write a score sheet (confirm.md A36, A37, A41). From the repo root:

    uv run python eval/run_eval.py                      # every case: 1 run --ai off + 3 runs --ai gemini
    uv run python eval/run_eval.py --cases 1,3 --ai agy --ai-runs 1 --label thu

Writes eval/results/<YYYYMMDD-HHMM>[-label]/: one folder per case and run holding the tool's report and its terminal
output, then bang-diem.md (for people) and scores.json. The tool is run as a black box, as the TM runs it.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from score import Report, Score, read_report, score

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / "eval"


def main() -> int:
    parser = argparse.ArgumentParser(description="Chạy bộ đánh giá eval/ và chấm điểm.")
    parser.add_argument("--cases", help="số case, cách nhau bằng dấu phẩy (mặc định: tất cả)")
    parser.add_argument("--ai", choices=("gemini", "agy"), default="gemini")
    parser.add_argument("--ai-runs", type=int, default=3, help="số lần chạy có AI mỗi case (mặc định: 3)")
    parser.add_argument("--label", help="hậu tố cho thư mục kết quả")
    parser.add_argument("--ai-timeout", type=int, default=180, help="giây chờ AI mỗi lần (agy cần ~300)")
    args = parser.parse_args()
    wanted = {f"case-{n.strip()}-" for n in args.cases.split(",")} if args.cases else None
    cases = [p for p in sorted(EVAL.glob("case-*")) if not wanted or any(p.name.startswith(w) for w in wanted)]
    stamp = datetime.now().strftime("%Y%m%d-%H%M") + (f"-{args.label}" if args.label else "")
    out = EVAL / "results" / stamp
    runs = [("off", "off")] + [(f"{args.ai}-{i}", args.ai) for i in range(1, args.ai_runs + 1)]
    results = []
    for case in cases:
        answer = json.loads((case / "dap-an.json").read_text(encoding="utf-8"))
        for name, mode in runs:
            print(f"{case.name} · {name} …", flush=True)
            results.append(_run(case, answer, name, mode, out / case.name / name, args.ai_timeout))
    (out / "scores.json").write_text(json.dumps([_jsonable(r) for r in results], ensure_ascii=False, indent=2))
    (out / "bang-diem.md").write_text(_sheet(results, args, stamp), encoding="utf-8")
    print(f"Bảng điểm: {out / 'bang-diem.md'}")
    return 0


def _run(case: Path, answer: dict, name: str, mode: str, out: Path, ai_timeout: int) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-m", "scrumbot", "run", "--source", "file", "--input", str(case / "input")]
    command += ["--out", str(out), "--ai", mode]
    command += ["--ai-timeout", str(ai_timeout)]
    started = time.monotonic()
    done = subprocess.run(
        [*command, *answer["args"]],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=ai_timeout + 120,
    )
    seconds = round(time.monotonic() - started, 1)
    (out / "terminal.txt").write_text(done.stdout + done.stderr, encoding="utf-8")
    sizing = next((line[8:] for line in done.stdout.splitlines() if line.startswith("Độ lớn: ")), "")
    reports = sorted(out.glob("assignment_*.xlsx"))
    report = read_report(reports[-1]) if done.returncode == 0 and reports else None
    result = score(report, answer, ai_run=mode != "off") if report else None
    return {"case": case.name, "answer": answer, "run": name, "mode": mode, "exit": done.returncode,
            "seconds": seconds, "sizing": sizing, "report": report, "score": result}  # fmt: skip


def _frac(pair: tuple[int, int]) -> str:
    return f"{pair[0]}/{pair[1]}" if pair[1] else "—"


def _commit() -> str:
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout
    dirty = subprocess.run(["git", "status", "--porcelain", "src"], cwd=ROOT, capture_output=True, text=True).stdout
    return head.strip() + (" (src/ có thay đổi chưa commit)" if dirty.strip() else "")


def _sheet(results: list[dict], args: argparse.Namespace, stamp: str) -> str:
    lines = [f"# Bảng điểm eval {stamp}", "", f"Commit: `{_commit()}` · AI: `{args.ai}` × {args.ai_runs} lần · "
             "đáp án và cách chấm: `confirm.md` A37, A40.", ""]  # fmt: skip
    lines += [
        "| Case | Lần chạy | PIC khớp TM | PIC theo spec | Dự phòng theo spec | Giữ đơn giao sẵn | Độ lớn cùng hạng "
        "| Lệch ≤ 1 hạng | Độ lớn mặc định | Cảnh báo thiếu / thừa | Giây | Độ lớn |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        s: Score | None = r["score"]
        if s is None:
            lines.append(f"| {r['case']} | {r['run']} | lỗi, exit {r['exit']} | | | | | | | | {r['seconds']} | |")
            continue
        findings = f"{len(s.missing)} / {len(s.extra)}" if r["mode"] == "off" else "—"
        defaults = s.size_default if r["mode"] != "off" else "—"
        lines.append(
            f"| {r['case']} | {r['run']} | {_frac(s.tm)} | {_frac(s.spec_pic)} | {_frac(s.spec_backups)} | "
            f"{_frac(s.kept)} | {_frac(s.size_exact)} | {_frac(s.size_near)} | {defaults} | "
            f"{findings} | {r['seconds']} | {r['sizing']} |"
        )
    for case in dict.fromkeys(r["case"] for r in results):
        lines += _case_detail([r for r in results if r["case"] == case])
    return "\n".join(lines) + "\n"


def _case_detail(runs: list[dict]) -> list[str]:
    answer = runs[0]["answer"]
    ok = [r for r in runs if r["report"] is not None]
    ai = [r for r in ok if r["mode"] != "off"]
    lines = ["", f"## {answer['slug']}: {answer['title']}", ""]
    header = "| STT | App | Đơn | Đáp án | " + " | ".join(r["run"] for r in ok) + " | Hạng thật / nhắm tới |"
    lines += [header, "|" + "---|" * (5 + len(ok))]
    changed_size = changed_pic = 0
    for order in answer["orders"]:
        cells = []
        sizes, pics = set(), set()
        for r in ok:
            row = (r["report"]).rows.get(order["stt"])
            if row is None:
                cells.append("bỏ qua")
                continue
            cells.append(f"{row.pic or '—'} [{row.size}{'*' if row.default else ''}]")
            if r["mode"] != "off":
                sizes.add(row.size)
                pics.add(row.pic)
        if len(sizes) > 1:
            changed_size += 1
        if len(pics) > 1 and not order["pre_assigned"]:
            changed_pic += 1
        expected = ", ".join(order["tm"] or []) if answer["kind"] == "real" else (order.get("spec_pic") or "")
        expected = expected or ("giao sẵn" if order["pre_assigned"] else "")
        truth = order.get("size_true") or (f"({order['size_target']})" if order.get("size_target") else "")
        title = str(order["title"]).replace("|", "/")[:48]
        lines.append(
            f"| {order['stt']} | {order['app'] or ''} | {title} | {expected} | " + " | ".join(cells) + f" | {truth} |"
        )
    lines += [
        "",
        "`*` = độ lớn mặc định (AI lỗi hoặc tắt). Hạng trong ngoặc là hạng mình nhắm tới khi viết mô tả, "
        "không phải giờ thật.",
    ]
    if ai:
        lines += ["", f"Dao động giữa {len(ai)} lần chạy AI: {changed_size} đơn đổi độ lớn, {changed_pic} đơn đổi PIC."]
    for r in ok:
        s: Score = r["score"]
        notes = [*s.misses]
        if r["mode"] == "off" and (s.missing or s.extra):
            notes += [f"cảnh báo thiếu: {', '.join(s.missing) or 'không'}; thừa: {', '.join(s.extra) or 'không'}"]
        if notes:
            lines += ["", f"Lệch ở lần `{r['run']}`:", "", *(f"- {n}" for n in notes)]
    if answer["watch"]:
        lines += ["", "Cần quan sát:", "", *(f"- {item}" for item in answer["watch"])]
    return lines


def _jsonable(result: dict) -> dict:
    report: Report | None = result["report"]
    s: Score | None = result["score"]
    return {
        **{k: result[k] for k in ("case", "run", "mode", "exit", "seconds", "sizing")},
        "rows": {stt: vars(row) for stt, row in report.rows.items()} if report else None,
        "findings": report.findings if report else None,
        "score": vars(s) if s else None,
    }


if __name__ == "__main__":
    sys.exit(main())
