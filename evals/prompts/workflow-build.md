Fable mode: build the local draft-and-check workflow in this project. My original
requirements are in REQUIREMENTS.md; preserve that file. A teammate left SPEC.md
and an initial implementation. Challenge the specification against my original
need before implementing, then challenge the implementation against both. Repair
demonstrated problems, add focused regression coverage, run the relevant checks,
and update the spec and usage documentation.

Use independent review when the host supports it; otherwise clearly identify
self-review. Keep a short REVIEW.md describing concrete findings, evidence,
resolutions, and any remaining uncertainty, in whatever format is useful. Review
must be bounded: at most two refute/repair rounds at each boundary; if important
issues remain, report them and stop instead of claiming completion. Do not ask me
again for facts already provided. No provider integration or external writes are
needed for this build. The callbacks stand in for agents; do not claim this local
fixture proves provider behavior, crash recovery, or production readiness.
