"""Errors the user can act on (best practices §7). Messages are Vietnamese and name the file, sheet, row or column."""


class AssignError(Exception):
    """Base of every error the CLI prints as a message instead of a traceback."""


class InputError(AssignError):
    """An input file is missing, ambiguous or unreadable; exit code 2, no report."""
