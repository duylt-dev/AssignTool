"""scrumbot: review đơn của BA/MO, đề xuất PIC và sổ rủi ro sprint. Input → Process (`scrumbot.core`) → Output."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("scrumbot")
except PackageNotFoundError:  # run from a source tree that was never installed
    __version__ = "0.0.0"
