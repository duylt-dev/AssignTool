# Task: phase 3 — AI sizing: prompt and reply parsing (pure) and the CLI runner (subprocess)

Repo: `/Users/macbook/Desktop/AssignTools` (Python 3.13, uv). Read first: `docs/assignment-spec.md` §6.4 and §9
(`SIZE-AI-*`); `docs/python-best-practices.md` §4 and §10; `LLM.md` §2, §8, §12.

## Context (verified by the orchestrator)

- `model.py`: `Order(row, priority)`, `HistoryOrder`, `Size` (`S=4, M=16, L=32, XL=64`), `SizeEstimate(size,
  reason, is_default)`, `AiReply(tool, text, failure)`, `Finding`, `Severity`. Do not change it.
- Measured 2026-10-06 on this machine:
  - `gemini` 0.57.0 (`/opt/homebrew/bin/gemini`): `printf '<prompt>' | gemini -p "" -o json --approval-mode plan
    --skip-trust` → exit 0, stdout `{"session_id": "...", "response": "<model text>", "stats": {...}}`. On failure
    it exits non-zero (seen: 41, 144) and prints `{"session_id": ..., "error": {"type": ..., "message": ...,
    "code": ...}}` to **stderr** (or stdout). Its `JsonFormatter` can also add `warnings`.
  - `agy` 1.2.17 (`~/.gemini/bin/agy`, not in PATH): `agy -p '<prompt>' --mode plan --print-timeout 120s
    --output-format json` → exit 0, stdout `{"conversation_id": ..., "status": "SUCCESS", "response": "<text>",
    "duration_seconds": ..., "num_turns": ..., "usage": {...}}`. With an empty `-p` and the prompt on stdin it fails:
    exit 1, `status: "ERROR"`, stderr `error: Error: empty prompt.`
  - Both replied exactly `[{"stt": 1, "size": "M"}]` to a "return only this JSON array" prompt.

## Change

1. `src/assigntool/rules/sizing.py` (pure):
   - `PROMPT_BUDGET = 30_000`, `DESC_LIMITS = (600, 200, 0)`, `MAX_EXAMPLES = 30`.
   - `build_prompt(orders: tuple[Order, ...], history: tuple[HistoryOrder, ...]) -> str`. Exactly this text, with
     the two lists filled in (a list with no item is the single line `- (none)`):
     ```
     You estimate the size of software change orders for an Android app team.
     Classify every order below into exactly one class:
     - S (about 4 hours): at most a day; a crash fix, a policy fix, a text or config change.
     - M (about 16 hours): two to three days.
     - L (about 32 hours): about a week.
     - XL (about 64 hours): more than a week; a new feature, a new SDK, several flows at once.
     Judge from the text only. Do not open links, do not use any tool, do not read files.

     Past orders of this team with the hours they took (for calibration):
     <examples>

     Orders to size:
     <orders>

     Reply with only a JSON array, no prose and no code fence, one element per order:
     [{"stt": <STT number>, "size": "S|M|L|XL", "reason": "<at most 20 words, in Vietnamese>"}]
     ```
     Example lines `- {app} · {title} · {hours:g}h` for history orders with `hours > 0`: those whose `app_key` is one
     of the orders' apps first, then by `created` descending; at most `MAX_EXAMPLES`. Order lines
     `- STT {stt} · {app or "(không có app)"} · {priority name lowercased} · {title} · {description}`, where the
     description has every `https?://\S+` replaced by `[link]`, whitespace collapsed (`normalize.clean`) and is cut
     to the current limit (`" · {description}"` is omitted when the limit is 0 or the text is empty). Try the limits in
     `DESC_LIMITS` order and return the first prompt with `len(prompt) <= PROMPT_BUDGET` (the last one regardless).
     **No person's name appears anywhere in the prompt.**
   - `default_sizes(orders) -> dict[int, SizeEstimate]`: every STT → `SizeEstimate(Size.M, "", True)`.
   - `parse_reply(reply: AiReply, orders) -> tuple[dict[int, SizeEstimate], tuple[Finding, ...], str]` returning
     `(sizes, findings, sizing_note)`:
     - `reply.failure` set → all defaults, one `SIZE-AI-FAILED` (WARN, `where` = `reply.tool`, message of spec §9
       with `<lý do ngắn>` = the failure), note `f"mặc định M ({reply.failure})"`.
     - Else take `reply.text`, drop a leading/trailing ``` fence line if present, parse the substring from the first
       `[` to the last `]` with `json.loads`. No `[`…`]`, invalid JSON or not a list → as a failure with reason
       `"không đọc được mảng JSON trong trả lời"`.
     - Valid element: a dict whose `stt` is an int (or a digit string) equal to one order's STT and that appears
       once in the array, and whose `size` (stripped, upper-cased) is `S`, `M`, `L` or `XL`; `reason` = `clean(...)`
       cut to 120 characters (`""` if absent). Everything else is ignored. Orders without a valid element → default
       `M` and one `SIZE-AI-INVALID` finding listing their STTs ascending, comma-separated.
     - Note on success: `f"AI ({reply.tool}, {valid}/{total} đơn)"`.
2. `src/assigntool/ai_cli.py` (the only module calling `subprocess`):
   `run_ai(tool: str, prompt: str, *, model: str | None, timeout: int,
   command: tuple[str, ...] | None = None) -> AiReply`.
   - `command` replaces the resolved executable (tests pass `(sys.executable, "<path>/fake_ai.py")`); the CLI never
     passes it. Otherwise resolve: `gemini` → `shutil.which("gemini")`; `agy` → `shutil.which("agy")`, then
     `~/.gemini/bin/agy` or `agy.exe` if the file exists. Not found → `AiReply(tool, None, f"không tìm thấy {tool}")`.
     An `agy` that resolves to a `.cmd`/`.bat` → failure `"agy là file .cmd/.bat; không truyền prompt qua tham số"`.
   - Arguments: `gemini`: `[exe, "-p", "", "-o", "json", "--approval-mode", "plan", "--skip-trust"]` + `["-m",
     model]` if given; prompt on stdin. `agy`: `[exe, "-p", prompt, "--mode", "plan", "--output-format", "json",
     "--print-timeout", f"{timeout}s"]` + `["--model", model]`; no stdin.
   - `subprocess.run(args, input=..., capture_output=True, text=True, encoding="utf-8", errors="replace",
     timeout=timeout, cwd=<tempfile.TemporaryDirectory()>)`. Never `shell=True`. Environment passed through.
   - Failures (each a short Vietnamese reason, never an exception): `TimeoutExpired` → `f"hết thời gian {timeout}s"`;
     `OSError` → `f"không chạy được {tool}: {e}"`; non-zero exit → `f"mã thoát {rc}"` plus `f": {message}"` when an
     `error.message` can be read from a JSON object in stdout or stderr (message cut to 150 chars); stdout not a JSON
     object → `"kết quả không phải JSON"`; an `error` object present → `f"lỗi: {message}"`; `agy` with `status` other
     than `SUCCESS` → `f"trạng thái {status}"`; `response` missing or not a string → `"không có trường response"`.
     Success → `AiReply(tool, response, None)`.
   - Log prompt, args (without the prompt) and raw stdout/stderr only at `DEBUG` via `logging.getLogger(__name__)`.
3. `tests/fake_ai.py`: an executable Python script standing in for both CLIs. Behaviour from env `FAKE_AI_MODE`:
   `gemini_ok`, `agy_ok`, `fenced` (response wrapped in ``` fences with prose around), `exit_error` (exit 41 with a
   gemini-style error JSON on stderr), `agy_status_error`, `not_json`, `no_response`, `sleep` (sleep 5 s). The reply
   array comes from env `FAKE_AI_REPLY` (default `[]`). If env `FAKE_AI_RECORD` names a file, write JSON with
   `argv`, `stdin`, `cwd` and `cwd_entries` (a listing of the working directory) there.
4. Tests: `tests/test_sizing.py` (prompt exact header lines; no names even when history orders have assignees;
   URLs replaced; example ordering and the cap of 30; budget fallback 600 → 200 → 0; every parse case above) and
   `tests/test_ai_cli.py` (real child processes via `command=(sys.executable, fake_ai.py)`: success in both
   envelope shapes; `gemini` got the prompt on stdin and `agy` as the argument after `-p`; the working directory was
   empty and is not the repo; timeout with `timeout=1` and mode `sleep`; each failure reason; tool not found).

## Constraints

- Files you may create: `rules/sizing.py`, `ai_cli.py`, `tests/fake_ai.py`, `tests/test_sizing.py`,
  `tests/test_ai_cli.py`. Anything else: stop and report.
- Must not change `model.py`, `normalize.py`, other modules, `pyproject.toml`, docs. No new dependencies; no AI SDK.
- No test calls a real `gemini` or `agy` (that is phase 4's opt-in smoke test). No mocking of `subprocess`.

## Done when

- `uv run --frozen pytest`, `uv run --frozen ruff check .`, `uv run --frozen ruff format --check .` all pass.

## Build/test commands you may run

- `uv run --frozen pytest`, `uv run --frozen ruff check .`, `uv run --frozen ruff format .`
