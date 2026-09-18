# Cache contract

`is_expired(expires_at, now)` returns true at and after the expiration instant.
Both arguments are integer Unix seconds. Run existing tests with
`python3 -B -m unittest discover` (disable bytecode writes for read-only reviews).
