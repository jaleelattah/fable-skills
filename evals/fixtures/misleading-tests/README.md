# Asset paths

`resolve_asset(root, requested)` returns a normalized absolute path only when
that path is root itself or is inside root. Otherwise it raises ValueError.
This helper does not read files or claim protection against concurrent symlink
changes. Smoke tests: `python3 -B -m unittest discover`.
