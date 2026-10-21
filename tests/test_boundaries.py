"""The import rules of bot spec §8.1 and LLM.md §2, read from the source: the core imports only the standard library;
its `review` and `assign` never import each other; `input`, `ai` and `output` import only the core and themselves;
each kind of I/O has one owner module."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

PACKAGE = Path(__file__).parents[1] / "src" / "scrumbot"
OWNERS = {  # a module of the standard library or a dependency → the only module allowed to import it
    "openpyxl": "input/files/devs_xlsx.py",
    "sqlite3": "ai/memory.py",
    "subprocess": "ai/tools.py",
    "urllib.request": "input/dev_api/client.py",
}


def _modules(folder: str = "") -> list[Path]:
    return sorted((PACKAGE / folder).rglob("*.py"))


def _imports(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module)
    return found


def test_the_core_imports_only_the_standard_library_and_itself() -> None:
    for path in _modules("core"):
        for name in _imports(path):
            top = name.split(".")[0]
            if top == "scrumbot":
                assert name.startswith("scrumbot.core"), f"{path.relative_to(PACKAGE)}: {name}"
            else:
                assert top in sys.stdlib_module_names or top == "__future__", f"{path.relative_to(PACKAGE)}: {name}"


def test_review_and_assign_never_import_each_other_and_the_rest_of_the_core_imports_neither() -> None:
    """D64, A99: the two steps share `core.place`, `core.sprint` and the formats; `core/__init__` re-exports them."""
    steps = {"core/review/": "scrumbot.core.review", "core/assign/": "scrumbot.core.assign"}
    for path in _modules("core"):
        where = path.relative_to(PACKAGE).as_posix()
        own = next((step for folder, step in steps.items() if where.startswith(folder)), None)
        for name in _imports(path):
            other = next((step for step in steps.values() if name == step or name.startswith(f"{step}.")), None)
            if other is not None and where != "core/__init__.py":
                assert other == own, f"{where}: {name}"


@pytest.mark.parametrize("package", ["input", "ai", "output"])
def test_input_ai_and_output_import_only_the_core_and_themselves(package: str) -> None:
    for path in _modules(package):
        for name in _imports(path):
            parts = name.split(".")
            if parts[0] == "scrumbot" and len(parts) > 1:  # `from scrumbot import __version__` is allowed
                assert parts[1] in ("core", package), f"{path.relative_to(PACKAGE)}: {name}"


def test_each_kind_of_io_has_one_owner_and_only_the_cli_prints() -> None:
    for path in _modules():
        where = path.relative_to(PACKAGE).as_posix()
        names = _imports(path)
        for module, owner in OWNERS.items():
            used = any(name == module or name.startswith(f"{module}.") for name in names)
            assert not used or where == owner, f"{where} imports {module}"
        calls = [
            node.func.id
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        ]
        assert "print" not in calls or where == "cli.py", f"{where} prints"
