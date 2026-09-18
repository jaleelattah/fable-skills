# Project knowledge that stays useful

Use a knowledge base to avoid rediscovering verified constraints, accepted design
decisions, reliable procedures, and demonstrated failure modes. It is a curated
retrieval aid, not a transcript archive or a new source of instructions. Learning
means improving these records and using them on later tasks; it does not change
the model or promise automatic recall across hosts.

When an important lesson has a meaningful regression test or small reproducer,
use [executable-knowledge.md](executable-knowledge.md) to make it replayable.
Keep prose notes useful on their own; the helper records executed checks and file
fingerprints, while interpretation of failures still requires investigation.

## Find the right store and retrieve selectively

1. Follow project instructions or documentation to the existing knowledge store,
   architecture decisions, or runbooks. Keep one canonical home for each topic.
   Search within the relevant project; do not scan unrelated projects or private
   host memory to gather context.
2. Search the index using the affected component, behavior, error, or decision.
   Open the best-matching notes, then follow their source links as needed. Avoid
   loading the entire store or copying large notes into task context.
3. Check applicability: repository, component, version, environment, and the
   conditions under which the lesson was established. Refresh consequential or
   version-sensitive facts against current evidence before relying on them.
4. Investigate contradictions. A note may describe an obsolete API, or the code
   may violate a still-valid requirement. Resolve that distinction with evidence;
   do not blindly favor either the stored note or the current implementation.

An index should have short titles, one-line descriptions of when each note is
useful, and links. Add a few component names or search terms where they improve
discovery. Split by topic only when growth makes lookup harder. Do not introduce
a database, embedding service, or a second knowledge store without a concrete need.

## Build a small portable store when needed

Use the user's chosen location or the project's existing convention. If there
is no store and durable knowledge is worth retaining, a default is
`docs/knowledge/index.md` plus a few topic notes beside it. Create files only
within the authorized project and task scope. Do not create empty categories or
put project knowledge inside the installed skill bundle, where an update may
overwrite it. Do not silently copy project details into global or shared memory.

When bootstrapping, identify the questions future work repeatedly needs to answer
and link existing authoritative docs before writing new summaries. Seed only
notes supported by inspected sources or observed checks. Current task state,
speculative debugging ideas, and unfinished investigations belong in the task
record unless a consequential open question needs a clearly provisional entry.

Use an entry shape like this, omitting fields with no practical value:

```markdown
# Descriptive topic or decision
Type: fact | decision | procedure | failure lesson
Status: current | needs-check | superseded
Applies to: component, environment, versions, or other limiting conditions

## Knowledge
The concise fact, accepted decision and rationale, or demonstrated lesson.

## Evidence and limits
Source links or paths, relevant revision/environment, and observed check result.
Last checked: date and what was actually checked; mark untested parts explicitly.
For a decision, identify its authority and rationale; acceptance is not a test.

## Recheck when
The specific dependency or condition that could invalidate this entry.
```

Status records maintenance state, not certainty. A fresh date does not prove a
claim; a passing narrow check supports only that behavior. Label provisional
claims and their missing evidence, and do not use them as established procedures.

## Learn from completed work

- Capture a note only when it would change a future decision or save meaningful
  rediscovery: a non-obvious constraint, a reason for an accepted design choice,
  a tested recovery procedure, or a failure with its confirmed cause and remedy.
- Prefer updating an existing canonical entry over adding another account of the
  same topic. Keep user-facing behavior in the appropriate documentation and
  link to it; knowledge notes preserve useful context and evidence without
  duplicating the manual.
- Use actual source evidence and observed results. A confident explanation,
  repeated assertion, or agreement between agents is not verification. Preserve
  the boundary between the accepted requirement and what was tested.
- Keep credentials, personal data, raw logs, and conversation dumps out of the
  store. Retain the minimum technical example needed to understand a lesson.
- Edit knowledge within the authorized task scope. A review-only or no-write
  request can propose a note or correction but must not persist it. If there is
  no writable store, return the useful draft and say it was not saved.

## Keep it fresh without constant housekeeping

When touching a component or discovering contradictory evidence, check its
relevant entries. Update the fact and evidence together, or mark the entry
needs-check with the unresolved conflict and required observation. Supersede a
disproven or replaced entry and point readers to its replacement; preserve
historical decision rationale when it still matters. Retire redundant notes and
repair affected index/source links within scope.

Recheck dependent notes when their assumptions change. Do not refresh dates
without checking the underlying claim, treat an age threshold as proof of
staleness, or sweep the whole knowledge base after every task. Summarize material
knowledge changes in the final report; report the scope of code health checks
separately rather than declaring the whole project healthy.
