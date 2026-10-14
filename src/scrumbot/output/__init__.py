"""The Output step of scrumbot (bot spec §8.1): adapters that turn the core's standard outcome, `core.Outcome`, into a
format. `markdown` writes `output.md`, `terminal` gives the lines `scrumbot assign` prints. Another format (a web page,
a message, JSON through `Outcome.to_dict`) is another adapter; the core does not change.
"""
