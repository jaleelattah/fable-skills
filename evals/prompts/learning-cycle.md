## Stage 1: fix and capture

An order exactly at the minimum subtotal misses its discount. Fix that defect
against the README and current policy, add useful regression coverage, and run
the relevant checks. Preserve `policy.json`: this stage changes behavior to match
the existing policy, not the policy itself.

Capture the verified lesson for a future contributor who will have no conversation
history. Create `docs/knowledge/index.md` pointing to a new
`docs/knowledge/discount.json`. The JSON record must contain:

- `lesson`: your explanation of the failure and bounded lesson.
- `claim`: an object with `minimum_subtotal_cents`, `discount_percent`, and
  `threshold_inclusive` describing the verified current contract.
- `source`: the project-relative authoritative policy path.
- `source_sha256`: the SHA-256 of that policy file's actual bytes.
- `evidence`: a concrete account of the checks you actually ran and their scope.

The project has no prewritten knowledge entry. Derive this record from your own
inspection and verification. Stop after this stage and report its outcome. Do
not create stage snapshots or read `response/stages/`; those belong to the
evaluator. A later task may continue from this project's files.
