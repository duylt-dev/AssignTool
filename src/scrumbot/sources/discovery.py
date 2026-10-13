"""Find the input files by content (assignment spec §2, A2, D29). Never guesses: zero or several candidates where one
is needed is an input error naming the candidates and the flag to use."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scrumbot.errors import InputError
from scrumbot.sources.sprint_reader import has_sprint_sheets

DEVS_FILE = "devs.xlsx"


@dataclass(frozen=True, slots=True)
class FileInputs:
    sprint: Path
    devs: Path
    history: Path | None
    rules: Path | None


def file_inputs(
    input_dir: Path, sprint: str | None, devs: str | None, history: str | None, rules: str | None
) -> FileInputs:
    """The export files of a `--source file` run."""
    workbooks = [path for path in files(input_dir, ".xlsx") if path.name.lower() != DEVS_FILE]
    sprint_books = [path for path in workbooks if has_sprint_sheets(path)]
    sprint_path = explicit(sprint, "--sprint") or only_one(
        sprint_books, "file .xlsx export sprint (có sheet Sprint N)", "--sprint"
    )
    history_path = explicit(history, "--history") or at_most_one(
        [*files(input_dir, ".csv"), *(path for path in workbooks if path not in sprint_books)],
        "file lịch sử",
        "--history",
    )
    return FileInputs(sprint_path, devs_path(input_dir, devs), history_path, rules_path(input_dir, rules))


def devs_path(input_dir: Path, value: str | None) -> Path:
    return explicit(value, "--devs") or only_one(
        [path for path in files(input_dir, ".xlsx") if path.name.lower() == DEVS_FILE], f"file {DEVS_FILE}", "--devs"
    )


def rules_path(input_dir: Path, value: str | None) -> Path | None:
    return explicit(value, "--rules") or at_most_one(files(input_dir, ".md"), "file luật .md", "--rules")


def files(directory: Path, suffix: str) -> list[Path]:
    if not directory.is_dir():
        raise InputError(f"Không có thư mục input '{directory}'.")
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() == suffix and not path.name.startswith(("~$", "."))
    )


def only_one(found: list[Path], what: str, flag: str) -> Path:
    if len(found) == 1:
        return found[0]
    if not found:
        raise InputError(f"Không tìm thấy {what}. Chỉ định bằng {flag}.")
    names = ", ".join(path.name for path in found)
    raise InputError(f"Có nhiều {what}: {names}. Chỉ định một file bằng {flag}.")


def at_most_one(found: list[Path], what: str, flag: str) -> Path | None:
    return only_one(found, what, flag) if found else None


def explicit(value: str | None, flag: str) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if not path.is_file():
        raise InputError(f"Không có file '{path}' ({flag}).")
    return path
