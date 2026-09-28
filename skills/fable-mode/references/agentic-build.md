# Guided agentic workflow build

Use this recipe when the user wants help starting, designing, or building an
agentic workflow. “Fable mode: start an agentic workflow” is a natural-language
entry point, not a new slash command. Work with the host's actual tools and the
project's existing runtime. The skill supplies a method, not an execution engine.

## Start with the questions that change the build

Read the request and available project context first. Reuse supplied answers.
If the user has only asked to get started, lead with the goal rather than a
technical questionnaire. Ask one to three short questions in a round, using the
host's question interface when available or ordinary conversation otherwise.
Offer concrete choices when useful and let the user describe the goal freely.

Choose from these prompts; this is a question bank, not a form to complete:

- **Outcome:** “What work should this handle, and what would a useful finished
  result look like?” Ask for one representative input/output example if abstract.
- **Flow:** “What starts a run, where does its information come from, and where
  should the result go?” Inspect discoverable details instead of asking for them.
- **Deliverable:** When unclear, “Do you want a design, a working local prototype,
  or integration into an existing system?” A request to build already establishes
  implementation scope; do not make the user select it again.
- **Decisions and limits:** “Which decisions may it make on its own, and which
  need your review?” Ask about a concrete action in this workflow, then any
  consequential deadline, cost, privacy, or access constraint still unknown.

Translate answers into technical choices. Do not ask the user to choose a model,
framework, agent count, or orchestration pattern unless an actual constraint makes
that choice theirs. Recommend a simple approach with its reason when they are
unsure. Use deterministic steps where a rule suffices and agents where judgment
or variable inputs warrant them.

Continue useful independent inspection while waiting. Do not invent the goal or
use silence as authorization. When sufficient information exists, summarize a
short build brief: outcome, example, inputs/outputs, scope, acceptance evidence,
and unresolved decisions. Proceed within existing authorization; a brief does not
create a new approval gate. Carry answers forward rather than restarting intake.

## Connect the two refutation boundaries

For a substantive build, use this cycle. A design-only request stops with the
challenged specification and a proposed execution/verification plan. It does not
authorize implementation or operation.

**Brief → specification → spec challenge and revision → build → implementation
challenge and repair → integrated verification → documentation and learning.**

1. **Specify the workflow.** Use [workflow step contracts](workflows.md): inputs,
   responsible worker/tool, output, acceptance evidence, and recovery. Identify
   decisions that select the next step, shared state, and which actions need
   authorization. Define how a run starts, ends, or hands unresolved work back.
   Split workers by useful boundaries, not a mandatory cast of agent personas.

2. **Refute the specification against the original need.** Follow the
   [refuter process](refutation.md). Ask what would fail even if the design were
   implemented perfectly: missing outcomes, an invalid business rule, ambiguous
   ownership, an unsafe retry, or an acceptance check that rewards the wrong
   result. Supply the original requirements and actual candidate spec. A reviewer
   must not treat the spec as its own authority. Revise demonstrated defects;
   ask the user only for decisions the available evidence cannot settle. Preserve
   original requirements and make changed assumptions identifiable.

3. **Build from the revised specification.** Delegate independent steps when
   useful, integrate their outputs, and keep shared edits coordinated. Implement
   relevant timeout, retry, and partial-completion behavior using the existing
   system. Use [checkpoints](checkpoints.md) when the work needs resumable state.
   A built workflow and a successful live run are separate claims.

4. **Refute the implementation against both the need and the revised spec.**
   Give the reviewer actual artifacts and check results. Exercise a concrete
   failure at a consequential handoff, such as missing evidence, duplicate input,
   an interrupted tool call, or a worker returning success with unusable output.
   Use the strongest relevant case, not an exhaustive failure checklist. If the
   finding exposes a spec defect, revise it and recheck dependent work too.

5. **Repair, integrate, and finish.** Resolve findings with evidence and rerun
   affected checks. Check the complete path from representative input to the
   user's accepted result, including relevant recovery. Update affected docs and
   run relevant [code health checks](maintenance.md). Preserve a demonstrated,
   reusable failure as a regression and, when useful, a source-backed
   [knowledge entry](knowledge.md); ordinary successful runs need no new note.

At either review boundary, prefer an independent reviewer with direct artifacts;
without delegation, identify the pass as self-review. Record the challenged
claim, counterexample or evidence, affected version, and resolution in the
existing task/spec record when useful. Review agreement is not proof.

Keep repair cycles bounded: one focused review plus targeted rechecks normally
suffices. Stop when acceptance evidence holds and material findings are resolved.
If repeated attempts add no evidence, or a required check needs unavailable
access, leave the affected claim unresolved and identify the next needed input.
Complete independent work; do not silently pass that boundary or claim readiness.
Use task-appropriate retry/resource limits, not an endless builder/refuter debate.

## Small example: draft support replies

The user wants draft replies for review and every ticket accounted for. A proposed
spec says to auto-send confident replies and discard uncertain tickets. The spec
challenge rejects both rules against the original outcome before building.

The revised workflow hands a draft or an explicit review-needed result to the
human for every ticket. An implementation challenge then interrupts a worker
after saving a draft but before recording progress: resuming must account for
that ticket without creating a duplicate draft. Check the actual artifact and
recovery behavior, update the affected procedure, and retain the regression.
These are proposed challenges, not evidence that a support integration was run.
