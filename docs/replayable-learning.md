# Replayable learning: a practical first run

Fable now has three local tools: a behavioral suite for evaluating agent work, an
executable casebook for checking past lessons, and checkpoints for resuming tasks.
They use Python 3.9+ and the standard library. They do not contact a model provider,
create a background service, or install themselves into a host.

Run the repository examples below from the repository root. The casebook and
checkpoint scripts also ship inside the skill, so another project can invoke
them from its installed `fable-mode/scripts/` directory with `--project` pointing
to that project. Runtime records belong to the project, not the skill bundle.

## 1. Replay a real lesson

This repository includes two [case definitions](knowledge/cases.json), backed by
the installer and packaging regression tests from the RAID review.

```sh
python3 skills/fable-mode/scripts/casebook.py --project . search installer
python3 skills/fable-mode/scripts/casebook.py --project . show installer-preserves-existing-files
python3 skills/fable-mode/scripts/casebook.py --project . replay installer-preserves-existing-files
python3 skills/fable-mode/scripts/casebook.py --project . status installer-preserves-existing-files
```

Search, show, and status are read-only. Replay explicitly executes the displayed
check and appends evidence under `.fable/runtime/casebook/`. The seeded installer
case works only in temporary installation fixtures. It rejects empty or skipped
test runs instead of recording them as success.

If a declared source, test, case definition, or observed dependency changes, the
previous record becomes stale. Replay the applicable check against the changed
project before relying on it. `current` describes freshness; inspect
`latest_outcome` separately to see whether the check passed.

A nonzero exit is a failed check, not automatic proof that a historical defect
returned. Diagnose the failure before writing a new lesson. See the
[executable knowledge guide](../skills/fable-mode/references/executable-knowledge.md)
for schemas, applicability, and execution limits.

## 2. Evaluate actual agent behavior

The [behavioral suite](../evals/README.md) includes eight tasks covering reviews,
bug fixes, stale knowledge, interrupted work, misleading tests, conflicting
requirements, a routine edit, and learning across fresh sessions. It prepares
task folders and scores the resulting artifacts. The learning-cycle case uses
three fresh actors and evaluator-controlled stage snapshots; follow its sealed
stage protocol instead of asking one actor to simulate multiple sessions.

```sh
python3 scripts/behavioral.py list
python3 scripts/behavioral.py prepare bug-fix --out /tmp/fable-bug-fix-candidate --variant candidate --skill skills/fable-mode --host YOUR_HOST --model YOUR_MODEL --tools 'filesystem, Python, terminal' --budget '10 minutes'
```

Give a fresh agent the generated `TASK.md` and only the task workspace and
candidate context described there. Keep evaluator data out of its working
context. Save its actual final answer in the run's `response/final.md`; retain a
tool trace separately when available. The generated folder separation is not an
operating-system sandbox. Use the host's permissions to constrain execution.
Choose a fresh temporary location outside existing repositories: Git commands in
a nested fixture can otherwise discover the enclosing repository and produce
misleading diffs. Completed runs can be archived under `.fable/runtime/` afterward.

```sh
python3 scripts/behavioral.py score /tmp/fable-bug-fix-candidate
```

Automated checks test observable artifacts and file boundaries. Human assessment
of the final answer and trace remains pending until supplied with supporting
evidence. A passing artifact check alone cannot certify honest reporting,
efficient work, or the absence of attempted external side effects.

An otherwise passing run returns exit code 3 while manual assessment is pending
or unassessable. Record the preparation seal outside the run and pass it to
`score --seal` and `compare --left-seal/--right-seal` to detect altered preparation
metadata as well as changed files. See the suite guide for the assessment format.

Prepare a separate baseline run without `--skill`, using `--variant baseline` and
the same case, host, model, tool access, and budget. Execute it in another fresh
context, then score and compare:

```sh
python3 scripts/behavioral.py compare /tmp/fable-bug-fix-baseline /tmp/fable-bug-fix-candidate
```

The comparison reports individual dimensions and context compatibility. It does
not produce an invented overall quality score. Repeat matched runs before
claiming an improvement, and reserve some tasks from iterative tuning. Preparing
fixtures or testing the evaluator does not count as running a model benchmark.

To assess overhead, preserve an actual host action trace and record observed
elapsed time, tool calls, and token usage when the host exposes them. The suite's
`measure` command accepts observer-supplied JSON, keeps unavailable values unknown,
and binds measurements to the current run artifacts and trace. Its guide documents
the format and distinguishes partial observations from complete totals. A declared
budget or an agent's retrospective is not a measurement. Compare ordinary tasks
as well as difficult ones before adding more process to the skill.

## 3. Capture and resume substantial work

Start with a task plan:

```sh
python3 skills/fable-mode/scripts/checkpoint.py --project . template
```

Save and fill in the JSON with actual goals, constraints, decisions, step
dependencies, source/output paths, and observed checks. The
[checkpoint guide](../skills/fable-mode/references/checkpoints.md) includes a
complete example and field definitions. Then capture it:

```sh
python3 skills/fable-mode/scripts/checkpoint.py --project . capture task-plan.json --out .fable/checkpoints/task.json
python3 skills/fable-mode/scripts/checkpoint.py --project . inspect .fable/checkpoints/task.json
```

The same checkpoint works after copying the project to another directory or host.
Inspection identifies changed or missing files and invalidates completed steps
that depend on them. It returns remaining work and the original context without
running stored commands. Exit code 2 means completed steps need rechecking.

`unchanged` means declared files match their recorded fingerprints; it does not
mean checks ran again. The task author reports acceptance outcomes. External
systems, undeclared dependencies, and the new host's permissions require separate
consideration. Keep checkpoints private or versioned according to the project's
own policy; the tool does not publish them.

## The feedback loop

Use a relevant past case during investigation. Implement and verify the requested
change. Resolve useful refuter findings, update affected docs, and preserve only
lessons with durable value. If the skill itself changes, evaluate its behavior
using comparable fresh runs. Capture a checkpoint when a handoff would benefit
from explicit context and evidence.

These tools make parts of that loop executable. Whether a particular skill
revision improves a model's work remains an empirical question for the suite.
