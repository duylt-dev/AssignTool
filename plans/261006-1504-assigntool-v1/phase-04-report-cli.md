# Task: phase 4 — Excel report, CLI wiring, acceptance test on the real sample, opt-in AI smoke test

Repo: `/Users/macbook/Desktop/AssignTools` (Python 3.13, uv). Read first: `docs/assignment-spec.md` §2, §10, §11,
§12; `docs/python-best-practices.md` §4–§8, §10; `LLM.md` §2, §7, §8.

## Context (verified by the orchestrator)

- Done in earlier phases: `sprint_reader.read_workbook(path, sheet) -> (target, prev | None, prev_name)`,
  `dev_reader.read_devs(path)`, `history_reader.read_history(path)`,
  `rules.validate.orders_and_findings(target) -> (orders, findings)`,
  `rules.sizing.build_prompt(orders, history)`, `rules.sizing.default_sizes(orders)`,
  `rules.sizing.parse_reply(reply, orders) -> (sizes, findings, note)`,
  `ai_cli.run_ai(tool, prompt, *, model, timeout) -> AiReply`,
  `rules.pipeline.build_result(*, target, prev, prev_name, orders, findings, devs, history, sizes, sizing_note)
  -> model.Result`. `pyproject.toml` already declares `assigntool = "assigntool.cli:main"`; `__main__.py` calls
  `main()`.
- The real sample `input/Maintain_update_Sprint_10_va_9.xlsx` exists locally (not committed). Sheet `Sprint 10` has
  6 orders (STT 1, 7, 10, 14, 18, 24); sheet `Sprint 9` has 12 orders (rows with `Loại` = `Task`) and the columns
  `STT, …, App Name., Trạng thái, Người làm, …, Ước lượng (h), …, Ngày tạo, Mô tả`.

## Change

1. `src/assigntool/xlsx_report.py`: `write_report(result: Result, headers: tuple[str, ...], out_dir: Path,
   now: datetime) -> Path` (spec §10).
   - File `out_dir / f"assignment_{slug}_{now:%Y%m%d-%H%M%S}.xlsx"`, slug = sheet name lower-cased, whitespace → `-`,
     characters outside `[a-z0-9._-]` → `_` (`Sprint 10` → `sprint-10`). `out_dir.mkdir(parents=True,
     exist_ok=True)`. Save to the same path + `.tmp`, then `os.replace`.
   - Sheet `Phân công`: `headers` + `Độ lớn, Giờ ước tính, Lý do độ lớn, PIC, Mã PIC, Nguồn, Lý do, Dự phòng 1,
     Dự phòng 2`; one row per assignment: `order.row.cells` (padded/truncated to `len(headers)`), then
     `size.name` + `" (mặc định)"` when default, `size.value`, the AI reason, `", ".join(pic_names)`,
     `", ".join(pic_codes)`, `source.value`, `reason`, backup 1, backup 2 (empty strings when absent).
   - Sheet `Cảnh báo`: `Mức, Mã, Vị trí, Nội dung`, one row per finding in the given order; no finding → one row with
     `Không có cảnh báo` in column A.
   - Sheet `Tải dev`: `Mã, Tên, Level, Việc dở sprint trước, Ngày nghỉ, Đơn giao sẵn, Đơn tool đề xuất, Tổng đơn,
     Tổng giờ ước tính, Danh sách đơn, App đã làm`; level written `junior`, `junior+`, `middle`, `middle+`,
     `senior`; `Danh sách đơn` joined with newlines (wrap text); `App đã làm` joined with `", "`; a dev on leave all
     sprint gets `Nghỉ cả sprint` in `Danh sách đơn`.
   - Bold header row, frozen first row, sensible column widths. Nothing else.
2. `src/assigntool/cli.py`: `main(argv: list[str] | None = None) -> int` (spec §2, §11).
   - `argparse` options exactly as spec §2 (`--ai` choices `gemini`, `agy`, `off`, default `gemini`;
     `--ai-timeout` int default 180).
   - Reconfigure `sys.stdout`/`sys.stderr` to `encoding="utf-8", errors="replace"` when possible (Windows consoles).
     `logging.basicConfig(level=DEBUG if -v else WARNING)`.
   - Discovery in `--input` (spec §2, A2): ignore names starting with `~$` or `.`; sprint = the only `*.xlsx`
     other than `devs.xlsx` (case-insensitive); devs = `<input>/devs.xlsx`; history = the only `*.csv`. Zero or
     several → `InputError` naming the candidates and the flag to use. A flag given explicitly must exist.
   - Flow: read the three files → `orders_and_findings` → sizing (`--ai off`: `default_sizes`, no finding, note
     `"tắt AI (mọi đơn M)"`; else print `f"Đang ước lượng độ lớn bằng {tool}…"`, `build_prompt`, `run_ai`,
     `parse_reply`) → `build_result` → `write_report(result, target.headers, out, datetime.now())` → print.
   - Print (spec §11): `Sprint: {sheet}`, `Độ lớn: {note}`, `Đơn: {n} · giao sẵn: {a} · tool đề xuất: {b} · cảnh
     báo: {w} WARN, {i} INFO`, one line per proposed order
     `STT {stt} · {app} {title} [{size}] → {code} (dự phòng: {b1}, {b2})`, then `Báo cáo: {path}`.
   - `AssignError` → `f"Lỗi: {message}"` on stderr, return 2 (traceback too with `-v`); `KeyboardInterrupt` →
     return 130; success → 0. Only `cli.py` prints.
3. `tests/test_cli.py`: discovery errors (none, several, explicit missing), exit 2 with the message, `--ai off` run on
   a small workbook built with `tests/conftest.py` builders producing a report with the three sheets; and a run with
   `--ai gemini` where `ai_cli.run_ai` is given a fake through a monkeypatched module attribute **only if** the CLI
   calls it through the module (`ai_cli.run_ai`); otherwise use `tests/fake_ai.py` on `PATH` via a temporary
   `gemini` wrapper script — whichever keeps the CLI code free of test hooks.
4. `tests/test_real_input.py`, marker `real_input`, skipped with a reason when the sample is absent:
   - build `devs.xlsx` (the 4 devs: `Ngọc Văn Linh` LinhNV middle+, `Nguyễn Nhật Minh` MinhNM middle, `Trần Đức An`
     AnTD junior+, `Bùi Văn Tiến` TiếnBV junior, all `Y`) and the history CSV (spec §5 columns) from the sample's
     `Sprint 9` `Task` rows, both in `tmp_path` — never committed, names read from the sample at run time;
   - run A: `main([... "--ai", "off"])` → 0; in the report: STT 10 → `MinhNM`, `Tool đề xuất`, backups `LinhNV`,
     `TiếnBV`; the other 5 `Đã giao sẵn`; `Cảnh báo` = `Không có cảnh báo`; `Tải dev` hours LinhNV 32, MinhNM 32,
     AnTD 32, TiếnBV 16, carry-over 1/0/0/2, `App đã làm` as in spec §12's derived-facts table;
   - run B: a copy of the workbook with `Người làm` cleared on the 6 `Task` rows of `Sprint 10` (openpyxl, normal
     mode) → PICs 7→MinhNM, 24→AnTD, 14→LinhNV, 10→MinhNM, 1→LinhNV, 18→TiếnBV; hours 32/32/16/16
     (Linh/Minh/An/Tiến).
5. `tests/test_ai_smoke.py`, marker `ai`: skipped unless env `ASSIGNTOOL_TEST_AI` is `gemini` or `agy` and the sample
   exists; builds the prompt from the sample (Sprint 10 orders, Sprint 9 history as in 4), calls `run_ai(tool,
   prompt, model=None, timeout=300)`, and asserts `parse_reply` gives 6 non-default sizes and no findings.

## Constraints

- Files you may create: `xlsx_report.py`, `cli.py`, `tests/test_cli.py`, `tests/test_real_input.py`,
  `tests/test_ai_smoke.py`. Anything else: stop and report.
- Must not change any other module, `pyproject.toml` or docs. No new dependencies.
- Never write into `input/`; tests write only into `tmp_path`. No real AI call outside `test_ai_smoke.py`.

## Done when

- `uv run --frozen pytest` passes with `real_input` tests **run, not skipped**; ruff check and format pass.
- `uv run --frozen assigntool --ai off --out <tmp>` fails with exit 2 and a clear message (there is no
  `input/devs.xlsx` yet) — that is expected.

## Build/test commands you may run

- `uv run --frozen pytest`, `uv run --frozen ruff check .`, `uv run --frozen ruff format .`,
  `uv run --frozen assigntool --help`
