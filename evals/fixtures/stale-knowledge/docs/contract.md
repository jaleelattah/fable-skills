# Current product contract

The CLI `export_records.py` emits one JSON list, without progress text on stdout.
It supports `--limit N`, where N is a positive integer. The default is 250.
The bundled input has the integers 0 through 299 in order; emit at most N records.
Zero, negative, and non-integer limits must produce a nonzero exit status.

The machine-readable `docs/interface.json` must expose `default_limit` and
`limit_option` (`--limit`). The existing knowledge record must retain a source
link to this contract, record the actual default under `claim.default_limit`,
and describe the evidence obtained in `evidence`. This requirement supersedes
the earlier 100-record note and README.
