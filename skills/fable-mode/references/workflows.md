# Building and running workflows

Use this guide when the user asks for a workflow or when dependencies, handoffs,
or recovery make a short task plan insufficient. A task plan organizes this run;
a reusable workflow also explains what changes between runs and how to resume
after failure. Build only the form the user needs: a concise plan, runbook, or
executable implementation in the existing system.

## Build backward from the result

1. Establish the intended output, scope, constraints, and observable acceptance
   criteria. Identify required inputs and access; mark missing prerequisites.
   Define how a run starts and which inputs it includes, such as a reporting date
   or data cutoff. Retrieve relevant project knowledge and check the evidence
   behind any assumptions the workflow will rely on; see [knowledge.md](knowledge.md).
2. Find the assumptions that could invalidate the approach. Investigate or refute
   those before committing dependent work. Use
   [refutation.md](refutation.md) for a substantial challenge.
3. Split the work at meaningful output or decision boundaries. Order steps by
   their actual dependencies, not by a generic lifecycle template. Each handoff
   must have enough information for the next step to proceed. Name the conditions
   that select a branch or block downstream work.
4. Specify checks at the boundaries where mistakes would propagate. Include a
   check of the integrated result; passing each step in isolation may miss a
   mismatch between their outputs.
5. For steps that can fail or change state, decide how to recognize partial
   completion and whether to retry, resume, undo, or stop. Scale this detail to
   the consequences of failure.

For implementation workflows, include affected documentation updates and relevant
code health checks in completion, using [maintenance.md](maintenance.md). After
verification and any refuter findings are resolved, capture only durable learning
in the project knowledge base. These can be part of an existing step; they do not
require extra stages or a new note on every run.

## Describe steps as contracts

Use these fields where they clarify execution; omit irrelevant fields and do
not create a large table for a trivial task:

| Field | What it establishes |
|---|---|
| Step and purpose | What outcome this step contributes. |
| Inputs and prerequisites | Artifacts, access, prior outputs, or conditions it needs. |
| Action and owner | What happens and which worker or tool is responsible, when relevant. |
| Output | The concrete artifact, decision, or state handed to the next step. |
| Acceptance evidence | The observable result required to consider the step complete. |
| Failure and recovery | How to detect partial work and choose a safe next action. |

For repeated runs, identify parameters, stable interfaces, and run identifiers
where they prevent mixing outputs. Keep secrets out of the workflow definition.
Use the host's existing workflow format if one is established; do not invent an
orchestration framework just to express these fields.

## Execute, delegate, and resume

- Run only work covered by the request. If the deliverable is a design, return
  the workflow with assumptions and untested steps clearly marked. Do not create
  recurring jobs, contact others, or run the workflow merely to validate a design.
- Keep enough state to distinguish planned, running, blocked, and completed
  steps, with output locations and observed checks. Tool unavailability or an
  unverified assumption is not a completed execution step. For substantial work,
  use a small record in the authorized workspace or the host's task tracker.
  [checkpoints.md](checkpoints.md) describes an optional portable file format and
  a helper that detects changed files and invalidates dependent completed steps.
- Parallelize only when inputs are ready and workers will not race over shared
  artifacts or external state. Give each worker a bounded outcome, inputs,
  constraints, permitted side effects, and acceptance criteria. The coordinating
  agent integrates outputs and checks their compatibility.
- After a failure or interruption, inspect the actual state before retrying.
  Determine whether the prior attempt took effect. Reuse still-valid outputs;
  recheck or rerun dependent steps whose inputs changed. A timeout alone does
  not show that an operation failed to happen.
- Retry when there is evidence a retry can help and it cannot duplicate harmful
  effects. Use bounded retries appropriate to the operation. Resume from the
  last valid boundary when possible. If recovery needs new authorization or
  unavailable information, finish independent work and report that constraint.

## A small example

For a workflow that combines two source files into a report:

- Validate each source's schema and reporting period; these checks can run in
  parallel when both inputs are available.
- Merge only the validated inputs using an explicit record identity rule.
- Check totals and identities against source data, then render the report.
- Inspect the rendered result and record which input versions produced it.

If one source changes, invalidate its validation and the outputs derived from it.
A failed render can reuse the unchanged validated merge. If the task is to design
this workflow, these are proposed steps, not evidence that a report was generated.
