# Draft-and-check design

The coordinator passes each item to a drafter, then hands the resulting proposal
to a verifier. The verifier returns an acceptance flag and feedback. Results
preserve item order and use the public result format in REQUIREMENTS.md.

To keep costs bounded, process each item once. A rejected first proposal is a
terminal rejection; feedback is kept for the operator instead of another draft.
Accept `max_attempts` as a positive-integer budget for future expansion, but this
version does not use the extra attempts. A callback exception fails only its
item, and the coordinator proceeds to the next item.

Callbacks are local, synchronous stand-ins for agents. There are no durable
side effects or process-recovery guarantees.
