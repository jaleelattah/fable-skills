# Grade the stated contract

Type: failure lesson
Status: current
Applies to: this repository's behavioral evaluators, especially knowledge evidence

## Knowledge

An example field representation is not automatically a required schema. Accept
valid alternatives allowed by the task. Separate a machine-checkable artifact
condition from the reviewer judgment that evidence is truthful and useful.

Three fresh `stale-knowledge` version-1 trials exposed this distinction. Two
actors saved commands, results, and observations in structured JSON objects;
the checker rejected them because the original fixture used an evidence string.
The task required descriptive evidence but did not constrain it to a string.
Independent review confirmed both structured submissions were valid.

Version 2 accepts nonempty descriptive text directly or within JSON structures.
Empty strings, empty structures, and numeric/boolean-only structures still fail.
Text presence does not certify correctness; trace-based manual review remains
required. Preserve old results when correcting a grader, increment its case
version, and prepare new comparable trials without changing the original seals.

The same restriction appeared in the three-session learning case. Its version-2
checker accepts structured narratives and additional explanatory claim fields
while still checking all required values. Frozen submissions can be re-evaluated
under a corrected checker if that result is separately bound to the original
inputs and labeled as re-evaluation, not a new model trial.

## Evidence and limits

- [Product contract](../../evals/fixtures/stale-knowledge/docs/contract.md) states
  what the task requires from saved knowledge.
- [Checker](../../evals/checkers/check.py) separates textual evidence presence
  from the manual evidence-quality judgment.
- [Regression controls](../../tests/test_behavioral_evidence.py) accept a realistic
  structured record and reject empty or nontextual alternatives.

Last checked: 2026-09-16 against the local working tree and the actual version-1
trial artifacts and host action traces. This lesson concerns this evaluator's
unstated type restriction; it does not waive an explicit schema in another task.

## Recheck when

The task contract, knowledge schema, or evidence grader changes. Run the focused
regressions and review whether each rejection corresponds to a stated requirement.
