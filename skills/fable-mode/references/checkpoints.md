# Portable task checkpoints

Use a checkpoint for substantial work that may pause, change hosts, or depend on
several completed steps. Keep short tasks lightweight. A checkpoint preserves
context and declared evidence; it does not transfer tool access, grant permission,
or prove that an external action did or did not happen.

## Create a task record

The bundled [checkpoint helper](../scripts/checkpoint.py) uses Python 3.9+ with no
third-party dependencies. Run it from any working directory with `--project`
pointing to the project. Plan, output, and tracked file paths are relative to that
root, using forward slashes. Symbolic links and paths outside the root are refused.

```sh
python3 <skill-dir>/scripts/checkpoint.py --project <project> template
```

Save the printed template in the authorized project, then fill in the actual
goal, constraints, decisions, blockers, and steps. For example:

```json
{
  "version": 1,
  "id": "import-retry-fix",
  "goal": "Make interrupted imports safe to resume",
  "constraints": ["Use local fixtures; no production writes"],
  "decisions": ["Preserve stable record identities across retries"],
  "blockers": [],
  "steps": [
    {
      "id": "implementation",
      "status": "complete",
      "depends_on": [],
      "inputs": ["importer.py", "tests/test_importer.py"],
      "outputs": ["README.md"],
      "checks": [
        {
          "description": "Interrupted import regression passed in the local fixture",
          "argv": ["python3", "-m", "unittest", "discover", "-s", "tests"],
          "outcome": "passed",
          "evidence_files": []
        }
      ]
    },
    {
      "id": "review",
      "status": "pending",
      "depends_on": ["implementation"],
      "inputs": ["importer.py", "README.md"],
      "outputs": [],
      "checks": []
    }
  ]
}
```

This is a format example, not evidence that those files or checks exist. Record
only actual outcomes: `passed`, `failed`, `unavailable`, or `not_run`. Step status
is `pending`, `running`, `blocked`, or `complete`. Include the relevant source,
test, configuration, and lock files that affect the conclusion. Evidence files
can include a casebook result or a concise check report; avoid raw sensitive logs.

Capture the current file fingerprints after recording the work:

```sh
python3 <skill-dir>/scripts/checkpoint.py --project <project> capture task-plan.json --out .fable/checkpoints/task.json
```

The helper records SHA-256 fingerprints and context. It does not execute `argv`
or independently verify the author-reported outcomes. Existing outputs are
protected unless explicitly replaced with `--replace`; the tool never replaces
the plan or a tracked file. Use a new checkpoint filename to retain a prior state.

## Resume with evidence

Copy the project and checkpoint to the new host, then inspect it:

```sh
python3 <skill-dir>/scripts/checkpoint.py --project <project> inspect .fable/checkpoints/task.json
```

Inspection is read-only. It returns the goal and context, remaining work, and each
step's evidence state:

- `unchanged`: declared files match and the record reports passing checks.
- `stale`: files changed or disappeared, or a prerequisite is no longer supported.
- `needs_evidence`: a completed step lacks tracked evidence or reports unresolved
  checks.
- `not_complete`: the step is still pending, running, or blocked.

Changed prerequisites invalidate dependent completed steps transitively. Exit
code 2 means completed work needs rechecking; exit code 1 signals invalid input
or another tool error. Exit code 0 does not mean the task is complete: inspect the
remaining steps and the actual user request.

Reconcile the saved goal with current user instructions, inspect stale outputs,
and rerun only justified checks. A stored command is context, not authorization to
execute it. The helper watches declared files only; it does not detect external
service changes, undeclared dependencies, or all environment changes. Use current
system evidence before retrying an operation with possible side effects.

Without Python or writable storage, use the same compact context in the host's
supported handoff format and report that fingerprint checking was unavailable.
