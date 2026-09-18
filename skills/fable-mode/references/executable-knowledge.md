# Executable knowledge

Use a case when a recurring failure or costly assumption can be checked with a small, relevant regression test or reproduction. A case records a lesson and the evidence needed to check its applicability. It does not justify running code merely because a search returned it.

## Retrieve, inspect, replay

Prefer the project's existing knowledge location. The helper defaults to `docs/knowledge/cases.json`; pass `--cases` for another project-relative path. The script ships with this skill; use its installed location when working in another project.

```sh
python3 /path/to/fable-mode/scripts/casebook.py --project . search installer
python3 /path/to/fable-mode/scripts/casebook.py --project . show installer-preserves-existing-files
python3 /path/to/fable-mode/scripts/casebook.py --project . status installer-preserves-existing-files
python3 /path/to/fable-mode/scripts/casebook.py --project . replay installer-preserves-existing-files
```

`list [query]` and `search [query]` retrieve matching cases; all query words must match. `show` previews the exact resolved command, files, prerequisites, and timeout. `status [case-id]` compares the latest record with current definitions and observed files. These commands never execute a case or write records.

Replay only a selected, relevant check after inspecting its code and confirming execution is within the user's existing authorization. Project-local paths and argument arrays prevent accidental path escapes and shell expansion in the helper. **They do not isolate the executed code.** A check inherits the host's permissions and environment and may have effects outside its working directory. Untrusted or externally mutating checks require the same review and authorization as any other command. Do not add routine permission prompts for already-authorized local tests.

The helper requires Python 3.9+ and no third-party packages. `{python}` in the first argument resolves to the running interpreter. Other bare command names resolve through `PATH`; an executable path must be project-relative. Declared paths and working directories cannot contain `..`, absolute paths, backslashes, or symlinks. Arguments are passed literally; the helper cannot validate the behavior of arbitrary programs or interpret which arguments refer to files.

## Case definition

Keep static definitions under version control. Example:

```json
{
  "version": 1,
  "cases": [{
    "id": "retry-is-idempotent",
    "title": "Retries do not create duplicate records",
    "lesson": "Deduplicate using a stable operation key before persisting a retry.",
    "invariant": "The retry regression test passes for a repeated operation key.",
    "applicability": {
      "when": "Changing retry handling or write deduplication.",
      "paths": ["src/retry.py"]
    },
    "tags": ["retry", "duplicates"],
    "sources": [{"path": "tests/test_retry.py", "note": "Regression for repeated delivery."}],
    "dependencies": {
      "paths": ["src/retry.py", "tests/test_retry.py", "pyproject.toml"],
      "executables": []
    },
    "check": {
      "argv": ["{python}", "-m", "unittest", "discover", "-s", "tests", "-p", "test_retry.py"],
      "cwd": ".",
      "timeout_seconds": 30
    }
  }]
}
```

Use a stable slug for `id`. State a bounded invariant, the conditions where it matters, and a source explaining why. List all local files, configuration, lockfiles, fixtures, and implementation dependencies needed to interpret the result. Directory dependencies include their current file contents and membership, so later additions and removals make evidence stale. Source and applicability paths are also fingerprinted and required. `.git`, `__pycache__`, and the selected results directory are excluded. Executable dependencies are names resolved through `PATH`; runtime versions, services, environment variables, and remote state are not fully fingerprinted. Write environmental preconditions in `applicability.when` and check them explicitly in the test.

Prefer a regression that exits zero only when its invariant is satisfied. A reproduction must make the meaning of success explicit; a random crash is not evidence that the historical bug reproduced. Ensure a test discovery command actually selects tests and that skips do not masquerade as coverage. Keep checks local and bounded; use timeouts between 0 and 3600 seconds. The helper terminates the POSIX process group on timeout; on other platforms it terminates the direct process, so checks must manage their own descendants.

## Evidence and freshness

Each explicit replay appends a unique JSON record under `.fable/runtime/casebook/`. Add `.fable/runtime/` to the project's ignore rules, or pass an ignored project-relative `--results-dir`. That directory cannot equal or contain any explicitly declared input path; it may sit below a broader watched directory. Keep runtime results out of the skill bundle and static knowledge. Records contain the actual command, working directory, timestamp, duration, exit status, definition fingerprint, file hashes, and a bounded summary. Raw stdout/stderr are discarded; no environment variables are saved. Do not put secrets in definitions or arguments because these are recorded. Run a reviewed command separately through the host's normal tools when diagnostics are necessary.

| Replay outcome | Meaning |
| --- | --- |
| `check_passed` | The configured check exited zero, for the declared scope and observed inputs. |
| `check_failed` | The check exited nonzero. Diagnose whether this is an invariant failure, test defect, or environment problem. |
| `not_applicable` | A declared file, working directory, or executable is missing; nothing ran. |
| `inconclusive` | Execution could not start, timed out, or observed inputs changed during the check. |

CLI exit statuses are 0 for a passed replay/read command, 1 for a failed check, 2 for invalid definitions/paths or helper errors, and 3 for a not-applicable/inconclusive replay.

`status` reports `unrecorded`, `current`, `stale`, or `not_applicable`, plus the latest outcome. **Current is a freshness label, not a passing verdict.** A changed definition, observed file, selected project, command, or resolved executable location invalidates prior freshness. Changes detected during execution invalidate the result, including files changed and restored with different filesystem metadata. This is a before/after check, not a continuous filesystem monitor; undeclared inputs, undetectable intermediate changes, and environmental drift remain outside the evidence. Records are local observations, not tamper-proof attestations.

## Learn without accumulating rules

After diagnosing a useful failure, preserve the smallest regression, link its source, and add or update one case. Verify the check detects the defect using an isolated fixture or safe controlled change, then passes after the fix. Do not mutate the working project merely to manufacture a demonstration. Save only durable, scoped lessons; consolidate duplicate cases and retire those whose applicability no longer exists. When a replay contradicts an old note, resolve the contradiction before promoting either claim.
