# Python best practices for `scrumbot`

[`LLM.md`](../LLM.md) says **where** code goes; this file says **how** it is written. Read the section that matches
what you are touching before writing code, and run §11 before reporting a change as done.

Every rule states what breaking it costs. A rule with no reason gets ignored, then deleted.

| § | Contents |
|---|---|
| 1 | Toolchain |
| 2 | Modules and files |
| 3 | Reading `devs.xlsx` and the TM rules |
| 4 | Calling the AI tool (subprocess) |
| 5 | Cross-platform |
| 6 | Files on disk |
| 7 | Errors and exit codes |
| 8 | Terminal output and logging |
| 9 | Types and value objects |
| 10 | Testing |
| 11 | Checklist before reporting done |
| 12 | The internal system's API and the memory |

---

## 1 · Toolchain

- Python `>=3.11`, `.python-version` 3.13, environment and lock file managed by **uv** (A1). Commands: `uv sync`,
  `uv run scrumbot …`, `uv run pytest`, `uv run ruff check .`, `uv run ruff format .` (ruff skips `*.md`: it would
  rewrap the Python examples in the docs).
- Runtime dependency: `openpyxl` only; HTTP is `urllib`, the memory `sqlite3` (A52).
  Dev dependencies: `pytest`, `ruff`. Nothing else without a reason written in
  `confirm.md`: pandas, for instance, would add tens of MB to read a few hundred rows, and its type inference turns
  an empty `Hạn` into `NaN` and a `STT` into a float. No AI SDK either: the AI is reached through the user's own CLI
  (A17), which already holds the user's authentication.
- Lower bounds only in `pyproject.toml`; `uv.lock` holds exact versions.
- `agy` and `gemini` are installed by the user. Never bundle, download or install them.

## 2 · Modules and files

- Module names are `snake_case.py`, never kebab-case: a module named with `-` cannot be imported.
- Keep files under about 200 lines. A file that grows past that is usually doing two jobs.
- **Pure core, thin edges** (bot spec §8). `core/` does no I/O and imports only the standard library, and
  `ai/prompt.py` is pure too (LLM.md §2). Input adapters turn files and API replies into the values of
  `core/inputs.py` and contain no decisions; `ai/tools.py` runs a command and returns text; output adapters only
  format an `Outcome`. If a decision creeps into an adapter, move it into `core/rules/`: a rule inside a reader can
  only be tested with a real file shaped for it, and a website that replaces the reader would lose it.
- **The two standard formats are the contract** (`core/inputs.py`, `core/outcome.py`, bot spec §8.3–§8.4). A field
  added to one is added to the spec's table in the same change, with its JSON form; a field nobody reads is removed,
  not kept "for later": the TM maps every field of the table.
- No module-level mutable state. A cache or a counter at module level leaks between test cases and makes their result
  depend on order.

## 3 · Reading `devs.xlsx` and the TM rules

- **Columns by header name, never by index.** A column added in the middle of a hand-edited file silently shifts every
  index. Header names are compared after NFC, trim, trailing-`.` removal and casefold (assignment spec §4).
- **Open workbooks with `load_workbook(path, read_only=True, data_only=True)`.** `data_only` returns cached values,
  so the footer's `=COUNTIF(…)` never arrives as text; `read_only` keeps memory flat. Close the workbook in a
  `finally` (or use `contextlib.closing`): on Windows an unclosed read-only workbook keeps the file locked.
- **Normalise text once, at the reader boundary,** with `core/normalize.py`: `unicodedata.normalize("NFC", …)`, trimmed,
  whitespace collapsed. Excel on macOS and copy-pasted names can be NFD; two spellings of "Linh" in different forms
  compare unequal, and a dev's load is then silently wrong.
- **Dates:** a cell may hold a `datetime`, a `date`, a string or nothing. The reader converts all of them to
  `datetime.date | None` and raises `InputError` naming the sheet, row and column for an unreadable string. The
  API's times are strings too (§12). Never
  compare a `datetime` with a `date`; it raises `TypeError` at runtime in the middle of a sort.
- **The TM rules `.md`: tables by header, everything else ignored.** `input/files/rules_md.py` opens the file with
  `encoding="utf-8-sig"` (editors on Windows add a BOM), finds tables by their delimiter row and keeps those whose
  header has `Loại` and `Dev`; columns go by header name like `devs.xlsx`. Text outside the tables is the TM's
  notes. A parser that read the file line by line as rules would turn a note into an input error, and one that read
  columns by position would swap `App` and `Ghi chú` the first time the TM reorders the table.

## 4 · Calling the AI tool (subprocess)

All child processes go through `ai/tools.py`. Rules it enforces:

- **Arguments are a list, never `shell=True`.** The prompt carries text BA typed: quotes, `$`, backticks, `&`.
  Through a shell, an order description becomes a command on the TM's machine.
- **Never pass order text as an argument to a `.cmd` or `.bat` file.** On Windows, arguments to a batch file are
  re-parsed by `cmd.exe` and the same injection returns even without `shell=True`. `gemini` (an npm shim on Windows)
  therefore gets the prompt on **stdin**; if the resolved `agy` is a batch file, `ai/tools.py` refuses it and the run
  falls back to `M`.
- **Start the child in its own process group, and on timeout or Ctrl+C kill the whole group** (`_run_child`:
  `Popen(start_new_session=True)` + `os.killpg` on POSIX, `CREATE_NEW_PROCESS_GROUP` + `taskkill /F /T` on Windows),
  reading with `communicate(input, timeout=…)` and `text=True, encoding="utf-8", errors="replace"`. `gemini` 0.57.0
  re-spawns itself as a second node process; `subprocess.run` kills only the direct child, and on 2026-10-06 that
  second process kept calling the API after the report was written. `communicate` reads both pipes together (no
  full-pipe deadlock), and `errors="replace"` keeps one bad byte from turning a good reply into `UnicodeDecodeError`.
  No other `Popen` code: `_run_child` is the one place.
- **Run in `tempfile.TemporaryDirectory()` as `cwd`.** The agent's workspace is then empty: it cannot read `input/`
  or the repo, and nothing it might write survives.
- **Pass the user's environment through unchanged.** Authentication lives there and in the tool's own config. Never
  read, log or copy an API key.
- **Log the prompt and reply only at DEBUG** (`-v`). They contain internal order text; a default log line ends up in
  a terminal screenshot.
- **Every failure becomes a value, not an exception:** `ai/tools.py` returns either the reply text or a short failure
  reason (`không tìm thấy gemini`, `hết thời gian 180s`, `mã thoát 41: <error.message>`), and `ai/prompt.py` turns that
  into sizes and a finding (spec §6.4, §9). Another `ask` (an HTTP AI) must do the same: a sizer never raises for an
  AI failure (bot spec §8.5).

## 5 · Cross-platform

The tool runs on Windows, Linux and macOS (A2).

- Paths are `pathlib.Path` end to end; convert to `str` only at the subprocess boundary.
- Open every text file with an explicit `encoding=`. Windows defaults to the ANSI code page, and every file here is
  Vietnamese.
- Find executables with `shutil.which`, which applies `PATHEXT` on Windows; then check `~/.gemini/bin/` for `agy`.
- Never rely on ANSI colours or `\r` redraws in the terminal; plain lines work in every console.
- File names written by the tool use only `[A-Za-z0-9._-]`. The sprint `Sprint 10` becomes `sprint-10`; a `:` or `/`
  from a sprint name is replaced, because `:` is illegal in Windows file names.

## 6 · Files on disk

- **Atomic writes.** The report goes to `<name>.tmp`, is saved, then `os.replace`d. A crash mid-write must leave no
  half report that looks complete.
- **One report name, `output/output.md`** (A85). It is plain text, so an editor holding it open never locks it the way
  Excel locked the old workbook on Windows; whoever wants to keep one copies it or passes `--out`.
- **Never write into `input/`.** It holds the user's hand-kept files (`devs.xlsx`, the TM rules); a tool that
  "normalises" one in place destroys the only copy.

## 7 · Errors and exit codes

- Errors the user can act on are `AssignError` subclasses in `errors.py` (today `InputError`), each with a Vietnamese
  message that names the file and, when known, the sheet, row and column. The CLI prints the message, not a
  traceback; `-v` shows the traceback.
- **A finding is not an exception.** A missing app name or a failed AI call is a `Finding` in the result (spec §9).
  Exceptions are for "cannot assign at all": unreadable file, missing column, empty pool.
- **Never catch and ignore.** `except Exception: pass` around a rule makes it silently decide nothing, which reads as
  a valid proposal. The AI call's failures are caught on purpose, and each one becomes a reason in `SIZE-AI-FAILED`.
- Exit codes: `0` report written, `2` input or usage error, `130` interrupted (spec §11).

## 8 · Terminal output and logging

- Library code logs with `logging.getLogger(__name__)` and never calls `print`. Only `cli.py` prints.
- The terminal shows the sprint, how sizing went, the counts, one line per proposed order and the report path. The
  full detail belongs in the workbook.
- The AI call takes seconds to a minute. Print one line before it (`Đang ước lượng độ lớn bằng gemini…`), so the TM does
  not think the tool hung.

## 9 · Types and value objects

- Type hints on every function signature. Use `X | None`, `list[str]`, not `Optional`/`List`.
- Value objects in `core/` are `@dataclass(frozen=True, slots=True)`, with tuples instead of lists inside them.
  Rules then cannot mutate their inputs, and the order in which rules run cannot change a result. The types of the
  standard input with optional fields are `kw_only=True`: a field's default is its JSON default, and a call names
  every field it sets.
- `Level`, `Priority` and `Size` are `enum.IntEnum`: `Level.JUNIOR` (0) … `Level.SENIOR` (4); `Priority.URGENT` (0) …
  `Priority.LOW` (3), smaller first; `Size` values are the hours (`S = 4` … `XL = 64`), so a load is a plain sum.
- **Test a parsed enum with `is None`, never with truthiness.** `Priority.URGENT` and `Level.JUNIOR` are 0, so
  `parse_priority(raw) or Priority.NORMAL` turns every urgent order into a normal one without an error. This happened
  on 2026-10-07: urgent orders lost their place in the queue until an independent recount
  disagreed on Sprint 10.
- `Severity` is an `enum.Enum` ordered WARN > INFO.

## 10 · Testing

- **Pure modules: table tests, no mocks.** Each finding code has a test that triggers it and one that does not; each
  key part of spec §7 has a case where it alone decides (LLM.md §8).
- **Readers: real files.** Build `devs.xlsx` with `openpyxl` inside the test (one name stored as NFD) and write the
  rules `.md` with each supported shape (BOM, CRLF, fenced blocks).
- **`ai/tools.py`: a real child process** (`tests/fake_ai.py`), never a mocked `subprocess` (LLM.md §8).
- **The core through its API** (`tests/test_engine.py`): an `Inputs` built in Python, as a website would, no HTTP and
  no file. **The boundaries from the source** (`tests/test_boundaries.py`): imports read with `ast`, so a forbidden
  import fails the build instead of waiting for a review.
- **The API client: a real local HTTP server** (`tests/http_server.py`), never a mocked urllib. **No test reaches the
  dev server:** `tests/conftest.py` points `SCRUMBOT_API_BASE` at a closed local port for every test; a test that
  forgets to start the fake server fails in milliseconds instead of calling the dev server with the real token.
- **No network in the default run.** The one real AI test is marker `ai`, opt-in through `ASSIGNTOOL_TEST_AI=gemini`
  (or `=agy` on the dev machine).
- Never weaken an assertion or add a skip to make a run green. If a test is wrong, fix it and say why in the change.

## 11 · Checklist before reporting done

1. `uv run ruff check .` and `uv run ruff format --check .` pass.
2. `uv run pytest` passes; report the counts.
3. Changed a rule, a finding or the prompt: spec §6–§9 updated, with a test that fails without the change.
4. Changed the API source, a rule, a risk, the review or the flow: ran `uv run scrumbot assign
   input/don/<file>.md --ai off --out <scratch dir> --state <scratch dir>` against the dev server and read
   `output.md`.
5. Changed `ai/tools.py` or `ai/prompt.py`: ran `ASSIGNTOOL_TEST_AI=gemini uv run pytest -m ai` (or `=agy`) once with a real AI tool,
   or the report says plainly that it did not run.
6. No `shell=True`; no file opened without `encoding=`; no column read by index; no `datetime` compared with a
   `date` (§3–§5).
7. `LLM.md`, the spec and `confirm.md` updated as `LLM.md` §10 requires, in the same change.
8. Nothing contradicts a `D` decision in `confirm.md`. A changed `A` default is updated there with the reason.

## 12 · The internal system's API and the memory

- **One HTTP client, GET only** (`input/dev_api/client.py`): `Authorization: Bearer`, `User-Agent: scrumbot/<version>`,
  timeout 60 s, `429` waits 30 s and retries three times, every other failure an `ApiError` with a Vietnamese message.
  Measured 2026-10-13: urllib's default User-Agent gets a Cloudflare 403 (code 1010), and 4,816 history rows need 97
  requests against a limit of 120 a minute; a client without the header or the retry fails on the first run.
- **The token never leaves its header.** `ApiConfig.token` is `repr=False`; error messages, logs and
  reports never carry it. A token in a log line ends up in a screenshot or a committed file.
- **Read the configuration from the environment first, then `.env`, leniently** (spaces around `=`, quotes). The
  user's `.env` had `KEY = value`; a strict parser reported a missing token that was there.
- **Decide from standard-input values, never from API JSON.** `input/dev_api/cache.py` gets the raw replies (with the
  list cache) and `input/dev_api/reader.py` turns them into `core/inputs.py` values; rules never see the API's JSON,
  so they are tested with plain values.
- **The AI answers are one SQLite file with one owner** (`ai/memory.py`); each method opens, writes and commits
  on its own. A long-lived connection would hold a lock while `agy` thinks for two minutes.
- **Times are naive local times,** like the API's (`YYYY-MM-DD HH:MM:SS`, server time = the team's time zone).
  Mixing an aware `datetime` with the API's naive ones raises `TypeError` in the middle of a comparison.

