"""The Input step of scrumbot (bot spec §8.1): adapters that build the core's standard input, `core.Inputs`.

`dev_api` reads the internal system's dev server, `files` the dev list, the TM rules and the order file, and `local`
joins them for `scrumbot assign`. Another source (the production API, a JSON file, a database) is another adapter that
builds the same `Inputs`; the core does not change.
"""
