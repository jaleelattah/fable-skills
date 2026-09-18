# The refuter process

The refuter's job is to test whether a material claim survives a serious attempt
to disprove it. It can examine a plan before execution, an implementation, a
workflow boundary, or a final conclusion. Focus on claims whose failure would
change the decision. Do not manufacture objections or require a quota of findings.

## Set up a bounded challenge

State the claim and its scope, the evidence currently offered for it, and the
observation that would falsify it. For example, "restarting the import preserves
exactly one row per source record" is falsified by a missing or duplicated record
after an interrupted run. "Looks robust" is too vague to test.

For an independent pass, give the reviewer:

- The user's actual requirements and constraints, including prior decisions and
  the authorized scope of work.
- The claim or candidate plan, plus direct access to the relevant artifact,
  version, inputs, and checks or outputs. Separate observed results from the
  builder's interpretation; the favorable summary is not sufficient evidence.
- A bounded review scope, available tools, permitted side effects, and any
  material time or resource limit.

Let the reviewer choose its strongest challenge before suggesting your own
suspected defect. Supply necessary context without steering it toward agreement
or a predetermined failure. The reviewer should inspect the artifact and use
safe isolated probes where useful; it should return findings rather than edit
the builder's shared files. Independent review does not require a different
model, and multiple agreeing agents are not a substitute for evidence.

Without delegation, take a fresh self-review pass using the original requirements
and actual artifact. Seek a concrete alternative explanation or counterexample.
Call it self-review; do not simulate several personas and claim independence.
Without execution tools, use inspectable examples or logical contradictions and
state which checks were not run.

## Probe and report

Choose the cheapest safe test that could overturn the claim. Examples include a
second invocation, a partially completed step, mismatched inputs at a handoff,
or a case where a successful command still produces the wrong result. Use the
case implied by the actual design; do not run an exhaustive generic checklist.

For each material result, report:

- **Claim challenged and consequence:** what could be wrong and why it matters.
- **Evidence:** the relevant artifact or location, input and observed result,
  reproduction, or explicit contradiction. State the version or state reviewed.
- **Status:** refuted, supported within the checks performed, or unresolved.
  A suspected failure that was not demonstrated is unresolved, not a confirmed bug.
- **Next discriminating check:** when unresolved, the smallest additional
  observation that would settle it and any required access.

Report material findings first. If no counterexample was found, state the scope
of inspection or testing and any consequential gaps. Avoid unqualified claims
that the artifact is correct, safe, or production-ready.

## Resolve findings and finish

The builder or coordinating agent evaluates each material finding against the
evidence. Reproduce it where practical; otherwise inspect the cited contradiction.
Resolve it by fixing the problem, rejecting the finding with a concrete reason,
or retaining it as unresolved with its impact on the conclusion. Do not dismiss
it through confidence or accept it merely because a reviewer sounds certain.

After a fix, run the relevant check and revisit the affected claim. If a workflow
assumption changed, revisit dependent steps and the integrated result as needed.
Earlier approval of a different artifact or state does not validate the revision.

If a finding exposes a stale project note or an incorrect documented assumption,
include the affected documentation in the resolution. Capture a reusable lesson
only after its evidence is settled, following [knowledge.md](knowledge.md). A
review-only refuter returns this as a finding for the owner; reviewer agreement
alone does not establish a fact or authorize a knowledge-base write.

One focused pass and targeted rechecks normally suffice. Stop when the material
findings are resolved with evidence or when further investigation cannot proceed
within the available access, scope, or resource limit. Reopen a settled finding
only for changed artifacts, new evidence, or a specific unresolved risk. Repeated
disagreement without new information should be reported as unresolved rather than
turned into an endless debate. An unresolved material claim limits completion or
readiness claims; report that limit and the next needed evidence.
