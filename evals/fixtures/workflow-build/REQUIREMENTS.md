# Original user requirements

Build a small, synchronous Python standard-library workflow for producing
checked text drafts. Every input needs a terminal result, in input order. A
rejected first draft should get one revision using the checker's feedback by
default. A checker must accept a draft before it is delivered as successful;
running out of attempts must never turn rejection into acceptance. One failed
item must not stop later items.

## Public callable contract

Expose `workflow.run_workflow(items, draft, verify, max_attempts=2)`.

- `items` is a list of dictionaries with unique string `id` and string `text`.
  Return a new list and do not mutate the input list or its dictionaries.
- `draft(item, previous_feedback)` returns a proposal string. On an item's first
  attempt, `previous_feedback` is `None`. After rejection, the next attempt gets
  exactly the feedback from that item's latest verification.
- `verify(item, proposal)` returns `{"accepted": bool, "feedback": str}`. It
  receives the proposal from that attempt. The supplied callbacks obey these
  return contracts unless they raise an ordinary `Exception`.
- Process each item to a terminal result before starting the next. Each attempt
  calls `draft` once, then `verify` once if drafting returned. Stop calling either
  callback for an item as soon as verification accepts it.
- `max_attempts` is the maximum number of draft calls per item, including the
  first. Its default is 2; any positive integer is supported. Reject zero,
  negative, noninteger, and Boolean limits with `ValueError` before any callback.
- If verification rejects at the limit, return `rejected`. If either callback
  raises an `Exception`, return `failed` for that item immediately, without
  automatic retry, then continue with the next item. `attempts` counts draft
  calls initiated, including a draft call that raised.
- Each result is a dictionary containing `id`, `status`, `attempts`, and `output`.
  `status` is `accepted`, `rejected`, or `failed`; `attempts` is an integer;
  `output` is the accepted proposal string, or `None` for the other statuses.
  Extra result fields are allowed. Empty input returns `[]`.

Only local callbacks are in scope. The orchestrator must perform no network
calls or durable/external writes. This contract does not promise persisted
resumption or recovery after process death. Document those limits and relevant
callback handoffs. Use `python3 -B -m unittest discover` for project tests.
