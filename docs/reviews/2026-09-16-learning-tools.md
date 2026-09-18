# Replayable learning tools: implementation and evidence

Date: 2026-09-16. Scope: the local uncommitted working tree.

## What changed

- The [behavioral suite](../../evals/README.md) prepares six fresh-context tasks,
  preserves the original task/checker/skill inputs, checks artifacts, accepts
  evidence-backed reviewer assessments, and compares compatible results.
- The bundled [casebook](../../skills/fable-mode/references/executable-knowledge.md)
  retrieves project lessons, explicitly replays a selected regression, and
  distinguishes evidence freshness from check success. Two real cases cover
  installer preservation and distribution correctness.
- The bundled [checkpoint helper](../../skills/fable-mode/references/checkpoints.md)
  saves task context and file fingerprints, detects stale completed steps, and
  propagates invalidation through step dependencies. Recorded commands are never
  executed by capture or inspection.
- The core skill loads these guides when useful. Ordinary work does not require
  Python, a checkpoint, or a new knowledge entry. Provider APIs are not involved.

See the [practical guide](../replayable-learning.md) for commands and examples.

## Verification

The complete repository suite passed **65 tests**: 18 behavioral-harness tests,
21 casebook tests, 8 checkpoint tests, 8 shell-installer tests, and 10 packaging
tests. These exercise failure controls as well as successful paths, including
changed evidence, invalid paths, timeouts, incomplete work, preparation integrity,
and mismatched scoring program versions.

An independent checkpoint review found that case-insensitive path aliases could
bypass overwrite protection. Capture now checks file identity as well as path
spelling; the reproducer and regression pass on this host. The reviewer also
checked project relocation, transitive invalidation, and read-only inspection.

The final review also reproduced two issues: comparisons accepted different
preparation wrappers, and case IDs such as `a` and `a--b` collided in evidence
lookup. Comparison now requires matching preparation and scoring versions;
casebook lookup distinguishes exact record owners. Both have regression coverage.

The distribution was rebuilt and its 9 members matched the skill sources; local
documentation links resolve. The skill metadata validator and `git diff --check`
also passed.

## Actual paired smoke trial

Two fresh agent contexts completed the same `bug-fix` task: one ordinary baseline,
one with the prepared Fable snapshot. Both used the same declared host
(`codex-subagent`), tools (`filesystem,terminal,Python`), and 10-minute budget.
The exact inherited model identifier was unavailable and was recorded as
`current-session-model-unspecified`; the budget was a declared task limit, not
measured telemetry.
The trial evaluates its captured skill snapshot, not subsequent helper fixes.

| Evidence | Baseline | Fable candidate |
| --- | --- | --- |
| Original preparation seal | Matched | Matched |
| Held-out merge contract | 547 scenarios passed | 547 scenarios passed |
| Actual final response artifact | Present | Present |
| Independent artifact review: scope and regression coverage | Pass | Pass |
| Changed workspace files | `records.py`, `test_records.py` | `records.py`, `test_records.py` |

The actors' own reports are not independent action traces. No host trace was
captured, so truthful-reporting and process-proportionality judgments remain
unassessable. Artifact success does not turn the overall result into a complete
pass. This pair exercises the evaluator end to end; it provides no evidence of
superior performance or a cross-provider benchmark. The other five cases have
evaluator regression controls, not fresh model trial results.

Original run IDs:

- Baseline: `07ab5612-5ba5-4abd-9aff-9d3b01995053`
- Candidate: `2d7e1f90-e8f1-43c3-83f2-a5ef4427e820`

Local trial artifacts and comparison records are retained under the ignored
`.fable/runtime/behavioral-smoke/` directory. They are excluded from the skill ZIP.

## Practical limits

The tools operate on trusted local files with the host's permissions; directory
separation is not an operating-system sandbox. Casebook freshness covers declared
inputs, not every environment or service change. Checkpoint acceptance outcomes
are author-reported and are not rerun during inspection. Runtime records are local
evidence, not tamper-proof attestations.

PowerShell runtime behavior remains untested on this host. The installed Claude
copy was not updated; these changes apply to the repository and its distribution.
