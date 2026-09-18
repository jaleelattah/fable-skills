# Documentation and code health

Use this guide when an implementation affects documented behavior or requires
code health checks. Treat relevant documentation and verification as part of
delivering the requested change. For review-only work, identify gaps and report
evidence without editing files or creating knowledge records.

## Keep documentation aligned with the change

Trace the change to the people and interfaces it affects. Inspect the existing
authoritative documentation near that surface: usage examples for a changed API,
setup instructions for new configuration, or a runbook for changed operations.
Use the repository's conventions to decide whether release notes are required.
Do not create a new documentation system for an ordinary implementation.

Update the affected documentation alongside the implementation, including obsolete
examples, defaults, constraints, and links. Describe the delivered behavior and
its relevant limits. A planned feature or untested procedure must not be presented
as available or verified. Keep generated documentation synchronized through its
established source and generator when available; avoid edits that regeneration
would discard.

Verify what the change could break: compare claims against the implementation,
check affected local links, render when layout matters, or run examples safely
when their executability is part of the deliverable. A spelling correction usually
needs inspection, not the application's entire test suite. Conversely, a docs-only
change to a command or configuration example can warrant a focused execution check.
If no documented contract changed, no documentation edit is needed merely to show
that this step happened.

## Choose code health checks from the repository

Read the relevant contributor guidance, package scripts, build configuration, and
CI definitions to find the established checks. Run task- or repository-required
checks and select additional checks according to the touched surface and claim:

- Formatting or linting for changed source and local conventions.
- Type or static checks when interfaces or supported language rules may be affected.
- Focused tests for changed behavior, with regression coverage when it protects a
  meaningful failure mode.
- Build or integration checks when packaging, dependencies, or cross-component
  behavior could change.

These are selection criteria, not a mandatory stack for every task. Prefer the
existing tools and supported scope selectors. Inspect the final diff for accidental
changes and obvious maintainability problems introduced by this work. Fix relevant
issues in scope; report material adjacent debt without initiating a cleanup project.
Do not introduce new analyzers, suppress failures, automatically upgrade dependencies,
or reformat unrelated files just to improve a health summary.

## Interpret failures and finish honestly

Record enough evidence to reproduce a relevant check: command, working context,
observed result, and the failure location. A failing check is not automatically
caused by this change or pre-existing. Compare against a suitable unchanged baseline
when practical, using comparable inputs and environment without overwriting user
work. If no reliable comparison exists, report attribution as unknown. Separate
test failures from missing tooling, unavailable services, or setup failures.

Fix failures caused by the requested change and rerun the affected checks. Required
checks that remain failing or unavailable limit completion claims; state the gap
and its impact. Once appropriate checks pass, stop unless new edits, failures, or
unresolved risks justify more work. Never describe an unrun check as passed.

Close out with the relevant documentation changes, check outcomes, and material
remaining limits. Preserve durable, verified discoveries through
[knowledge.md](knowledge.md) when they would help future work. Routine successful
checks, transient logs, and every completed task do not need knowledge entries.
