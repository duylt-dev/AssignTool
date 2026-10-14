"""Errors the user can act on (best practices §7). Messages are Vietnamese and name what to fix."""


class AssignError(Exception):
    """Base of every error the CLI prints as a message instead of a traceback."""


class InputError(AssignError):
    """An input is missing, ambiguous or does not fit; exit code 2, no report."""


class NoRunningSprint(InputError):
    """No Maintain sprint is running on the run day (bot spec §2.3)."""
