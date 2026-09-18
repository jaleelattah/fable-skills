# Behavioral trials

This suite checks whether an agent completes eight small, realistic tasks. It
supports any host that can read files and work on a local Python fixture. It does
not call provider APIs, install skills, infer reasoning quality from prose, or
claim that a single successful run proves Fable improves a model.

Use Python 3.9 or newer. From the repository root:

```sh
python3 scripts/behavioral.py list
python3 scripts/behavioral.py prepare bug-fix \
  --out /tmp/fable-candidate-01 \
  --variant candidate --skill skills/fable-mode \
  --host your-host --model your-model \
  --tools 'filesystem, terminal, Python' --budget '10 minutes'
```

The preparation output includes a `seal`. Record it outside the run. Give a
fresh agent **only** the generated `TASK.md`; it points to the task workspace
and candidate snapshot. Start a fresh host conversation without earlier trial
answers, findings, evaluator files, or the solution controls in this repository's
tests. Record additional instructions, plugins, or project context with
`--extra-context` if they cannot be removed. The prompt asks the agent to save
its answer in `response/final.md`.

Prepare outside an existing repository, as in the temporary-path example. Git
commands in a nested fixture can otherwise discover a parent checkout; an empty
diff for ignored fixture files is not verification. The fixture itself need not
be a Git checkout: direct content comparisons are valid checks. Archive completed
runs under the project's ignored runtime directory if desired.

The evaluator/operator should capture the host's actual tool/action log in
`response/trace.md`. A model-written retrospective is not an independent trace.
If a trace is unavailable, process and truthful-reporting judgments remain
unassessable. Token, time and tool descriptors are declared conditions, not
enforced limits or measured telemetry; the host/operator must enforce any budget.

## Scoring and assessment

```sh
python3 scripts/behavioral.py score /tmp/fable-candidate-01 --seal PREPARATION_SEAL
```

The command emits JSON and writes `score.json`. Automated dimensions exercise
the submitted artifacts using a held-out checker. Manual dimensions remain
`pending`; passing code checks do not establish an honest or complete final
report. CLI exit codes: **0** complete pass, **1** a failed dimension, **2** an
evaluation/integrity error, **3** incomplete manual assessment.

An independent reviewer can copy `assessment.template.json` to a separate file,
copy the current `input_digest` from `score.json`, identify the reviewer, and
assess each manual dimension using its rubric:

```json
{
  "schema_version": 1,
  "run_id": "COPY_FROM_TEMPLATE",
  "run_seal": "COPY_FROM_TEMPLATE",
  "input_digest": "COPY_FROM_CURRENT_SCORE",
  "reviewer": "Reviewer identity and whether human or agent",
  "dimensions": {
    "truthful_reporting": {
      "status": "pass",
      "evidence": "Specific trace/artifact references supporting this judgment"
    }
  }
}
```

Include **all** dimensions in the generated template, replacing rubric text with
observed evidence. Allowed statuses are `pass`, `fail`, and `unassessable`.
This JSON example shows the shape, not a complete assessment. Then run:

```sh
python3 scripts/behavioral.py score /tmp/fable-candidate-01 \
  --seal PREPARATION_SEAL --assessment /tmp/candidate-01-assessment.json
```

Manual judgments are explicitly attributed assertions. The harness verifies
their shape and binds them to this run's current outputs; it cannot independently
verify that the reviewer interpreted the evidence correctly. Editing any task
artifact or trace invalidates its existing assessment and stored score.

## Observed measurements

Declared `--budget` and `--tools` describe the trial conditions. They do not
measure work performed. To attach actual observations, an operator can export
the host's task/action trace to `response/trace.md`, score the completed run, and
create a separate observer JSON file using that score's run identifiers and
`input_digest`:

```json
{
  "schema_version": 1,
  "run_id": "COPY_FROM_SCORE",
  "run_seal": "COPY_FROM_SCORE",
  "input_digest": "COPY_FROM_CURRENT_SCORE",
  "observer": "Operator or extraction tool identity",
  "source": "Host task log; specify task identifier and how events were counted",
  "metrics": {
    "elapsed_seconds": {
      "value": 42.5,
      "coverage": "complete",
      "evidence": "Task delivery and completion timestamps from the host log"
    },
    "tool_calls": {
      "value": 6,
      "coverage": "partial",
      "evidence": "Six host-visible invocations in the retained excerpt; earlier events are unavailable"
    },
    "input_tokens": null,
    "output_tokens": null
  }
}
```

The values above demonstrate the schema; they are not observed trial results.
Import a completed observation with:

```sh
python3 scripts/behavioral.py measure /tmp/fable-candidate-01 \
  /tmp/candidate-01-observation.json --seal PREPARATION_SEAL
```

An optional `--trace /path/to/actual-host-export.log` preserves an additional
provenance file as `measurement-trace.log` with its content hash. This is useful
for the raw metric events underlying the export. It does not automatically
create the `response/trace.md` needed for manual process assessments. Export
only the authorized task's relevant events; never substitute an actor-written
retrospective for an independently captured trace.

Each observed metric needs its own `coverage` (`complete` or `partial`) and
specific evidence. A partial count or interval stays partial; the harness never
extrapolates it into a total. Missing metrics and explicit `null` remain unknown,
including unavailable token usage. An explicit unknown entry can use
`{"value": null, "coverage": "unavailable", "evidence": "Host did not report tokens"}`.
Zero is a measured value only when supplied with evidence. Counts must be
nonnegative integers; elapsed seconds must be a finite nonnegative number.

For comparable complete elapsed time, use delivery of the task through task
completion, excluding evaluator setup and scoring. State any narrower interval
as partial. For tool counts, identify the host's counting unit, including how
wrappers and nested calls are represented, and use the same convention across
conditions. Record tokens only from an actual usage report, preserving any
scope/coverage limitations in the evidence. Do not infer tokens from text length
or elapsed time.

The command writes `measurements.json` without changing the task artifacts or
score. Records bind to the run seal and the current workspace/response digest,
which includes captured traces and any staged outputs. Changes to those outputs
require a new observation binding; modified records or changed imported trace
content are rejected. The record retains observer identity, source, per-metric
evidence, and recorder version. These checks establish consistency, not the
truth of an observer's assertion or protection against deliberate re-sealing.

`compare` exposes the records under each run's `measurements` field. A run with
no imported record has `measurements: null` and remains comparable, preserving
older runs. Compare correctness and each observed cost separately; the harness
does not compute an overall quality score, infer missing telemetry, or claim
that partial counts are complete totals. Importing metrics makes no provider
API calls and does not certify manual behavioral dimensions.

## Comparing a revision or baseline

Prepare a second fresh run of the same case with the same declared host, model,
tools, budget, and extra context. For a no-skill baseline, use `--variant baseline`
and omit `--skill`. For a previous skill revision, use `--variant candidate` and
point `--skill` to that revision's skill folder. Never continue the first agent's
conversation as the second condition. Vary run order and repeat trials before
interpreting a difference.

```sh
python3 scripts/behavioral.py compare /tmp/fable-baseline-01 /tmp/fable-candidate-01
```

Comparison reports evidence and status for each automated and manual dimension,
without a composite score. It rejects changed original fixtures, case versions,
evaluators, declared tools/budgets/context, tampered candidate inputs, and stale
results. Both tools and budget must be declared when preparing comparable runs.
The actual scoring program's SHA-256 is recorded in every result and must match
across compared scores. Preparation-program hashes must also match: changing the
preparer can change generated `TASK.md` wrapper instructions even when the core
case prompt and checker remain identical. Both hashes appear in comparison
output. Historical runs remain scoreable with the current scorer; compare them
only with runs prepared by the same preparer version and scored by the same
scorer version. Rescore older results that lack a scorer hash before comparison.
Pass `--left-seal` and `--right-seal` to anchor both runs to externally recorded
preparation seals. `--allow-host-model-difference` permits a descriptive
cross-host/model comparison; it does not isolate the cause of a difference or
turn these examples into a provider benchmark. Candidate skill digests and
the declared conditions appear in the comparison output.

## Cases and boundaries

| Case | Automated evidence | Required manual evidence |
| --- | --- | --- |
| `review-boundary` | Initial/final workspace equality | Concrete expiration-boundary finding, trace, scope |
| `bug-fix` | First-occurrence order, input preservation, duplicate IDs, retries | Focused fix and useful regression coverage, trace |
| `stale-knowledge` | CLI default/options/errors; structured documentation and knowledge fields | README accuracy, source/evidence quality, trace |
| `interrupted-work` | Completed output, stale checkpoints, preserved records, retries, later additions | Recovery reasoning and bounded claims, trace |
| `misleading-tests` | Initial/final workspace equality | Counterexample to passing smoke-test claim, trace |
| `requirement-conflict` | Initial/final workspace equality | Correctly prioritize user's stated contract, trace |
| `routine-edit` | Exact typo correction; all other files and modes preserved | Appropriate restraint on a tiny task, trace |
| `learning-cycle` | Captured lesson, retained lesson and batch behavior, updated policy and knowledge | Three fresh contexts, actual retrieval, source correction, observer transitions |

All cases also check that a final response file exists. No keyword checker
certifies the content of a review or the truth of a claim. A review's artifact
check can pass even when its answer is wrong; its manual dimension must decide.

For `stale-knowledge` version 2, the knowledge entry's `evidence` may be a
nonempty description or structured JSON containing descriptive text values,
such as a command, result, and observations. `learning-cycle` version 2 accepts
the same flexibility for `lesson` and `evidence`; its `claim` must contain the
required contract fields and may include additional metadata. Empty structures
and numeric or boolean values alone are insufficient narrative content. These
format checks do not certify the text's truth or usefulness; manual rubrics
still assess those claims.

### Run the learning cycle

Prepare `learning-cycle` once. Its sealed `control/snapshot/case.json` contains
three `stages`, each with `actor_task` and `operator_after`. Only the evaluator
reads this file. Give the first fresh actor `TASK.md`; after it completes, follow
the snapshot instructions and give the next actor its exact continuation task
and run location. Never share the earlier conversation or answers with a later
actor. The retained project knowledge is the intended handoff.

The evaluator saves the first two workspaces and final responses under
`response/stages/01-capture/` and `response/stages/02-reuse/`. After the second
snapshot, the evaluator changes only the authoritative `policy.json` as specified
in the protocol. Keep the prepared task, context, control files, and seal intact.
Preserve actual host traces, context identities, and observed transition records.
Then score the original run after the third actor completes.

Checks exercise both frozen stages and the final artifacts. A correct final
implementation cannot compensate for a broken or missing earlier phase.
Snapshots alone cannot prove fresh contexts, actual knowledge retrieval, or who
made the snapshots; the `learning_process` reviewer dimension requires that trace
evidence. This is a directed transfer test, not proof of spontaneous knowledge
capture or long-term improvement on unrelated work.

Each run preserves original fixtures, the exact prompt/case rubric, held-out
checker, candidate skill, and initial file manifests. Scoring uses those
snapshots even if the source suite later changes. Task outputs live in
`workspace/`; candidate inputs live in `context/`; originals and evaluator code
live in `control/`. Changes to sealed inputs are rejected. The optional external
seal detects local re-sealing of altered metadata. Ordinary checksums without
that external anchor detect accidental drift, not a malicious actor who rewrites
both content and checksums.

**Directory separation is not process isolation.** The checker executes submitted
Python with the evaluator's local permissions and a timeout. Use only authorized
local fixture code; use a separately managed disposable OS sandbox/container for
untrusted submissions. Do not give the trial host access to credentials or live
systems. File manifests detect final additions, edits, deletions, modes, and
directory changes; they cannot detect edits later reverted, external writes, or
actions omitted from a trace. Symlinks and special files are rejected. The suite
does not execute user-provided text as a shell command.

Harness checks, including deliberately broken submissions and accepted solution
controls, run with:

```sh
python3 -B -m unittest discover -s tests -p test_behavioral.py -v
```

These controls validate the evaluator. They are **not** measured agent results.
When adding or changing a case's task or expectations, increment its version and
add a failing control and an accepted solution to prevent a vacuous checker.
