# Guided workflow kickoff and two review boundaries

Date: 2026-09-28. Scope: the local working tree after the merged portable-skill
update, plus isolated local behavioral trials.

## Change

The optional [agentic-build recipe](../../skills/fable-mode/references/agentic-build.md)
connects focused intake questions, a build brief, specification refutation,
implementation refutation, integrated checks, and relevant maintenance. The core
routes to it for a guided workflow request. Existing answers and authorization
carry forward; design-only work stops before implementation. The kickoff is
natural language, with no additional slash command or runtime dependency.

## Regression coverage

All **97 repository tests** pass, including 11 new workflow controls. Those
controls reject an unchanged fixture, a faithful implementation of a flawed
specification, and a corrected specification with an independent code defect.
They also cover feedback loss, false acceptance, excess attempts, failure
isolation, input preservation, and unchanged original requirements. Valid
artifacts cannot automatically pass judgments about the review process.

The distribution now contains **10 files**. Skill metadata validation, source/ZIP
parity, local documentation link checks, and whitespace checks pass. Installer
regressions exercise temporary shell installations; PowerShell execution remains
outside this validation.

## Fresh behavioral trials

Two fresh primary actors used the supplied skill snapshot. Actual host action
records identify the model as `gpt-6-astra`; no model or provider comparison was
performed.

- **Kickoff:** the actor asked three plain-language questions about useful work,
  an example result, and autonomous actions. It stopped for answers without
  changing the project or selecting a framework. Automated boundary checks and
  independent manual assessment passed. This tested the first question round,
  not a complete interactive intake.
- **Build:** an independent spec reviewer identified the no-revision rule that
  contradicted the original requirements. The actor corrected the spec and a
  separate implementation defect that skipped the final input. Its 10 project
  tests and documented example passed; the held-out checker passed 35 callback
  scenarios plus invalid-budget and empty-input checks. The original requirements
  remained unchanged. The implementation reviewer reported no demonstrated
  in-scope defect after additional isolated probes.

The spec reviewer began in a fresh context and retained that context for its
implementation review. Each boundary used one review round. A separate assessor
checked sequence and reporting against the actual primary and reviewer action
exports; it had inherited task context and was not a blind reviewer. Both trials
passed all automated and manual dimensions, bound to their unchanged task seals
and the submitted artifacts and evidence.

The first action export omitted the reviewer's public conclusions because the
host stored them separately from tool results. Assessment remained pending until
those public answers were exported with provenance and the unchanged submission
was rescored against the completed evidence. No actor rerun or grader change was
needed. The evaluation guide now explains this evidence requirement.

Raw runs, task seals, action exports, and bound assessments are retained locally
under `.fable/runtime/workflow-build-2026-09-28/`, outside versioned knowledge and
the skill archive. Runs were prepared outside existing repositories. Exports
retain relevant actions and results, excluding reasoning and system prompts.

These are small, directed trials. Deterministic callbacks stand in for agents;
they do not establish live provider behavior, durable process recovery,
production readiness, or a general advantage over other instructions.
