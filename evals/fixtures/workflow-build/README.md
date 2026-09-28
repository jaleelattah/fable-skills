# Local draft-and-check workflow

Call `workflow.run_workflow(items, draft, verify, max_attempts=2)` with local Python
callbacks. The current prototype implements the single-pass design in SPEC.md.

Run smoke coverage with `python3 -B -m unittest discover`.
