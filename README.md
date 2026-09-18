# Fable Skills

[`fable-mode`](skills/fable-mode/SKILL.md) is a model-agnostic skill for evidence-driven work: inspect before changing, debug with testable hypotheses, verify the requested outcome, and report what the evidence supports. It scales effort to the task and works with the tools and permissions the host actually provides.

Fable Mode is a set of instructions. It does not change the underlying model, unlock tools, or establish equivalence with another model. The name is retained for existing users; the skill does not depend on a particular model or provider.

## Replayable learning tools

The [practical guide](docs/replayable-learning.md) connects three working tools:

- **Behavioral suite:** prepare fresh baseline/candidate tasks, evaluate artifacts with held-out checks, and compare compatible results and observer-recorded effort. Reviewer judgments remain visibly pending until assessed. Eight cases, including routine work and learning across fresh sessions, live in [evals](evals/README.md).
- **Executable knowledge:** search past failure lessons, explicitly replay their regression checks, and detect stale evidence. Two [real cases](docs/knowledge/cases.json) cover installer and package failures.
- **Portable checkpoints:** save a task's goal, decisions, dependencies, and file fingerprints; detect stale completed work before resuming elsewhere. See the [checkpoint guide](skills/fable-mode/references/checkpoints.md).

The casebook and checkpoint helpers ship with the skill. The evaluation harness is a repository development tool. All three use Python 3.9+ and the standard library; no provider credentials or background services are required. They execute trusted local code only when explicitly invoked for that purpose and do not provide an operating-system sandbox.

## Workflows and refutation

- **Workflow design:** turns the desired result into steps with inputs, dependencies, outputs, acceptance checks, and recovery paths. For substantial or reusable work, the [workflow guide](skills/fable-mode/references/workflows.md) covers execution, delegation, and resuming after interruption.
- **Refuter process:** challenges an important claim with a concrete counterexample. The [refutation guide](skills/fable-mode/references/refutation.md) covers independent review, a self-review fallback, evidence-based findings, and bounded rechecks.

For example: “Fable mode: design a workflow for this import and refute its retry assumptions before we implement it.” The requested scope determines whether the result is a design or an executed workflow. Small tasks keep a light process; extra guides are loaded when relevant.

## Project knowledge and maintenance

Fable Mode retrieves relevant project knowledge before making decisions, checks it against current evidence, and captures durable learning after verification. The [knowledge guide](skills/fable-mode/references/knowledge.md) covers a searchable Markdown index, source-backed notes, stale claims, and selective updates. It reuses an existing project store or starts with `docs/knowledge/index.md` when a new store is warranted. Project knowledge stays separate from the installed skill.

Implementation work also includes affected documentation updates and relevant repository code health checks. The [maintenance guide](skills/fable-mode/references/maintenance.md) explains how to select checks and complete the change without expanding into unrelated cleanup. Review-only requests remain read-only.

This repository's [knowledge index](docs/knowledge/index.md) links the distribution lesson and executable regression cases. This is knowledge that future runs can retrieve and recheck; it does not train the model or guarantee automatic recall.

## Installation

Choose one destination. The installers copy the skill folder without changing host configuration. Running them without options keeps the original Claude Code destination.

### macOS / Linux

From this repository:

```sh
# Claude Code, all projects (default)
sh install.sh

# Codex, all projects
sh install.sh --target codex

# Another host or a project: provide its skills parent directory
sh install.sh --skills-dir "/path/to/project/.agents/skills"
```

You can also invoke the script by its absolute path from any working directory. Relative custom destinations are resolved from your working directory.

### Windows (PowerShell)

```powershell
# Claude Code, all projects (default)
.\install.ps1

# Codex, all projects
.\install.ps1 -Target codex

# Another host or a project
.\install.ps1 -SkillsDir 'C:\My Project\.agents\skills'
```

If your PowerShell execution policy blocks the script, use the manual copy below or your organization's approved script-running method.

Both installers stop if `fable-mode` already exists. Review any local changes before updating with `--force` (shell) or `-Force` (PowerShell). This overwrites bundled files and preserves additional files; it refuses linked destinations and checks overlapping file/directory types before copying. Later I/O failures can still leave a partial update. `--target`/`-Target` and `--skills-dir`/`-SkillsDir` are alternatives. For a literal directory named like an option, use a path such as `./--force`.

### Manual copy and paths

Copy the whole `skills/fable-mode/` folder into the applicable parent directory:

| Host | Personal skills parent | Project skills parent |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `<project>/.claude/skills/` |
| Codex | `~/.agents/skills/` | `<project>/.agents/skills/` |
| Another host with `SKILL.md` support | Use that host's documented skills directory | Use that host's documented project directory |

The final path must end in `fable-mode/SKILL.md`. Claude Code's installer respects `CLAUDE_CONFIG_DIR` when set. For a custom or legacy Codex location, pass its skills directory explicitly. The standard destinations follow [Claude Code's skill documentation](https://code.claude.com/docs/en/skills) and [OpenAI's local skill documentation](https://learn.chatgpt.com/docs/build-skills).

[`dist/fable-mode.zip`](dist/fable-mode.zip) contains the `fable-mode/` folder for hosts that accept uploaded skill archives. Use your host's documented upload flow; archive support and availability vary.

## Activation

- **Claude Code:** invoke `/fable-mode` or ask it to use Fable Mode.
- **Codex:** mention `$fable-mode` or select it in the skill picker.
- **Other skill hosts:** use the host's skill selector or explicit invocation syntax.

Natural-language phrases such as `fable mode`, `fable it`, `think like fable`, and the legacy alias `mythos mode` remain useful once the host can discover the skill. Automatic selection and persistence across turns depend on the host; repeat the invocation in a new session if needed. `Fable mode off` ends the session preference described in the skill.

### Without native skill support

Paste the Markdown body of [`SKILL.md`](skills/fable-mode/SKILL.md), starting at `# Fable Mode` and omitting the YAML metadata, into the conversation with:

> Use the following Fable Mode working instructions for this task, within your existing tools and permissions.

For workflows, refutation, project knowledge, or maintenance, also include the relevant linked guide if the host cannot read it. Then provide the task and relevant inputs. Pasting instructions supplies the working habits; it does not install a discoverable skill or provide persistent memory.

## Check that it works in your host

Confirm the host can find `fable-mode`, then invoke it on a small task with an observable result. For example, ask it to diagnose a failing test and explain the evidence. Check that its report distinguishes what it ran from what it inferred. A mode acknowledgment alone does not demonstrate improved behavior. If the skill is missing from the selector, restart the host and check the destination against its documentation.

The content is designed to be portable; it has not been benchmarked across model providers. Instruction following, tool access, discovery, and session behavior vary by host and model.

## Development checks

Python 3.9 or newer is required for these repository tools. It is not required to read or use the skill instructions.

```sh
# Check the existing ZIP against source files and local documentation links
python3 scripts/package_skill.py --check

# After editing the skill, validate sources and rebuild the ZIP
python3 scripts/package_skill.py --build

# Run evaluator, casebook, checkpoint, packaging, and installer regressions
python3 -m unittest discover -s tests -v
```

The packager includes the whole skill directory and keeps project knowledge outside it. It uses stable archive metadata, rejects missing or changed members and unsafe member types/names, and checks inline local Markdown link targets. It does not validate external URLs, Markdown anchors, or model behavior. The default action is a read-only check. Builds validate source links and the staged ZIP before replacing the archive; a link to the intended ZIP is allowed during build preflight so a missing archive can be recreated.

Installer tests use an available POSIX shell. Set `FABLE_TEST_SHELL` to another shell executable to exercise it; PowerShell runtime testing remains separate. See the [RAID review](docs/reviews/2026-09-15-raid.md) for the audit scope, findings, and remaining limits.

The [learning-tools review](docs/reviews/2026-09-16-learning-tools.md) records the new helpers' regression coverage and the actual paired smoke trial, including its unassessable dimensions.

The later [lean-core evaluation](docs/reviews/2026-09-16-lean-evaluation.md) records the shorter core, actual host measurements, routine-task comparisons, and a three-session learning trial, including grader corrections and interpretation limits.

## License

MIT — see [LICENSE](LICENSE).
