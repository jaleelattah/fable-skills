# Fable Skills project knowledge

Start with [the README](../../README.md) for usage and installation. These notes
retain reusable project lessons and link to their evidence. Check applicability
and freshness before using a note as a basis for a change.

| Note | Use when |
|---|---|
| [Delivering the whole skill](skill-delivery.md) | Adding skill references, refreshing the ZIP, or changing installers. Search terms: archive, packaging, nested resources, portability. |
| [Grade the stated contract](evaluation-contracts.md) | Changing behavioral checkers or investigating a rejected alternative representation. Search terms: false failure, evidence schema, structured JSON. |
| [Executable cases](cases.json) | Rechecking installer preservation and distribution validation after relevant changes. Run the [casebook helper](../../skills/fable-mode/scripts/casebook.py) to search, preview, or explicitly replay a case. |

See [replayable learning](../replayable-learning.md) for end-to-end examples. Static
case definitions are versioned here; fresh execution records live separately under
the project's ignored `.fable/runtime/` directory. A saved passing result becomes
stale when its declared sources or case definition change.

Update the relevant entry when its sources change; add a new topic only for
durable knowledge that would help future work. Follow the skill's
[knowledge guide](../../skills/fable-mode/references/knowledge.md).
