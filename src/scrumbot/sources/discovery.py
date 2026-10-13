"""Find devs.xlsx and the TM rules file in the input folder (assignment spec §2, D29). Never guesses: zero or several
candidates where one is needed is an input error naming the candidates and the flag to use."""

from __future__ import annotations

from pathlib import Path

from scrumbot.errors import InputError

DEVS_FILE = "devs.xlsx"


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
