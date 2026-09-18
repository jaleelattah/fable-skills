# Shorter core and observed behavioral trials

Date: 2026-09-16. Scope: this repository's local working tree.

## Changes

The [core skill](../../skills/fable-mode/SKILL.md) was reduced from **1,831 to
1,054 words** (42%). Repeated guidance is consolidated into one conditional
working loop and a table of guide triggers. Ordinary tasks no longer imply a
knowledge search. The six optional guides and two bundled helpers are retained;
there is one canonical skill, with no new product modules or provider dependency.

An independent comparison with the saved prior core found no material lost
safeguards: scope, authorization, review-only boundaries, evidence, recovery,
refutation, and stopping rules remain. That inspection supports the edit's
coverage; actual trials below provide the behavioral evidence.

The [evaluation harness](../../scripts/behavioral.py) now accepts observer-recorded
elapsed time, tool calls, and available token usage. Measurements bind to the
run, artifacts, and captured trace, and distinguish complete, partial, and
unavailable observations. They do not turn declared budgets into measurements.

Two cases were added: a routine edit that should stay small, and a three-session
learning cycle. See the [evaluation guide](../../evals/README.md) for commands,
observation schemas, and the sealed learning-stage protocol.

## Actual comparisons

Fresh actors used ordinary host instructions, the previous skill, or the
shortened skill. Host logs identify the model as `gpt-6-astra`. Each actor began
without prior trial history. The same task/checker snapshots, declared conditions,
and scoring program were used within each comparison.

| Task / condition | Artifact checks | Host duration, seconds | Tool invocations | Input / output tokens |
| --- | --- | ---: | ---: | ---: |
| Routine edit / baseline | Pass | 37.614 | 5 | 149,064 / 677 |
| Routine edit / previous | Pass | 46.799 | 7 | 215,649 / 946 |
| Routine edit / shortened | Pass | 36.641 | 5 | 154,782 / 642 |
| Stale knowledge v2 / baseline | Pass | 123.625 | 8 | 235,561 / 3,300 |
| Stale knowledge v2 / previous | Pass | 160.955 | 10 | 332,974 / 3,716 |
| Stale knowledge v2 / shortened | Pass | 148.368 | 8 | 260,976 / 3,985 |

These are observations from one run per condition and task, not estimates of an
average or evidence of a general speed/quality advantage. Input tokens include
cached and repeated context; they are not a price estimate. Tool counts are
host-level invocations, including failed calls, without double-counting nested
command events. Metrics cover the primary actor only. Concurrent host load and
available delegation slots varied; all three v2 stale-knowledge actors attempted
delegation, encountered the capacity limit, and continued locally.

The previous skill's extra routine calls were a hidden-file listing and an
explicit content comparison, not a demonstrated process problem. All three
routine actors limited edits to the requested word. The shortened version
preserved the checked outcomes here; broader performance remains unestablished.
An independent reviewer assessed the actual traces and artifacts; all manual
dimensions passed for these six runs.

## Learning across fresh sessions

One shortened-skill run used three independent actor contexts:

1. Fix the inclusive pricing boundary, verify it, and create a source-backed
   lesson in a project that initially had no knowledge entry.
2. Read and retain that generated lesson, then add batch behavior and verify it.
3. After an evaluator-only policy change, reconcile the stale lesson, tests, and
   saved examples with the authoritative source.

The evaluator copied and fingerprinted the first two completed workspaces before
starting the next actors. Those snapshots remained unchanged. Actual host action
exports show the retained note being read and the changed policy being checked.
The final actor preserved the policy and correctly updated stale tests and data;
the implementation already read the current policy and needed no change.

The stage-2 actor also used a separate reviewer that inherited its history. That
review was not blind. Its actual actions and public conclusion were retained
separately from the three fresh primary actor traces.

This is a directed knowledge-transfer test: the tasks explicitly request capture,
reuse, and correction. It does not establish spontaneous learning or general
improvement across unrelated projects.

## Evaluator defects found by real trials

The first stale-knowledge comparison and the learning run exposed an unstated
string-only restriction on knowledge evidence. Several actors produced useful
structured JSON instead. Independent review confirmed that the task contracts
allowed it. The graders now accept descriptive text within structured JSON and
reject empty or nontextual evidence. The learning grader also permits extra
explanatory claim fields while checking every required value. Manual review
continues to assess whether the evidence is true and useful.

Both cases were bumped to version 2. Original seals and version-1 scores were
preserved. Stale knowledge was rerun with three fresh actors; the table shows
those new v2 results. The learning run's frozen submissions were re-evaluated
under the corrected checker after verifying unchanged actor tasks and fixtures.
All three corrected artifact dimensions pass. This re-evaluation is recorded
separately and is not counted as another model run. The original v1 failure stays
visible. See the [durable lesson](../knowledge/evaluation-contracts.md).
The learning run's manual dimensions also passed after the reviewer inspected
all three actor traces, frozen stages, operator records, and auxiliary conclusion.

The trials also showed that Git commands in a fixture nested inside a real
checkout can expose parent status or return an empty diff for ignored files.
Subsequent direct content checks supported the reported edits. The guides now
recommend preparing outside existing repositories and archiving completed runs
afterward. Directory separation remains an organizational boundary, not a sandbox.

## Evidence retention and limits

Local raw runs, independently exported host actions, reviewer assessments,
measurements, comparison JSON, and the separately bound learning re-evaluation
are retained under `.fable/runtime/lean-eval/`, outside versioned knowledge and the
skill ZIP. Exports select only relevant tool/actions, timing/usage metadata, and
the auxiliary reviewer's public final response; reasoning and system prompts are
excluded. There were twelve fresh primary actor tasks across ten prepared runs,
plus the auxiliary review. Three initial runs exposed the grader issue.

The skill is designed to be provider-neutral, but these trials exercised one
model and host configuration. The tests establish specific observed behavior,
not the universal value of every optional feature. The installed Claude copy was
not changed by this repository update.

## Repository verification

All **86 regression tests** passed after the evaluator corrections. The new
coverage includes observer provenance, partial and unknown measurements, stale
bindings, routine-task artifact boundaries, stage history, retained knowledge,
changed policy behavior, and valid structured evidence. Skill metadata validation
and whitespace checks also passed. The distribution contains the same 9 bundled
files; evaluation code, trial logs, prior snapshots, and project knowledge stay
outside the skill package.
