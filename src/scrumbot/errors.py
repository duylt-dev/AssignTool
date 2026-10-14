"""Errors the user can act on (best practices §7). Messages are Vietnamese and name the file, sheet, row or column."""


class AssignError(Exception):
    """Base of every error the CLI prints as a message instead of a traceback."""


class InputError(AssignError):
    """An input file is missing, ambiguous or unreadable; exit code 2, no report."""


class NoRunningSprint(InputError):
    """No Maintain sprint is running on the run day (bot spec §2.3)."""


class ApiError(AssignError):
    """The internal system's API refused or failed a call (bot spec §2.2); exit code 2, no report."""
