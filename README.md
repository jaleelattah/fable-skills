# fable-skills

Installable [Claude Code skills](https://code.claude.com/docs/en/skills) that make any Claude model — Opus 4.8 in particular — operate with the judgment, planning, verification, and reasoning habits of **Claude Fable 5**, Anthropic's Mythos-class model.

## What's in here

| Skill | What it does |
|---|---|
| [`fable-mode`](skills/fable-mode/SKILL.md) | The full operating discipline: when to act vs. ask, scouting before editing, hypothesis-driven debugging, demonstrated-not-assumed verification, and faithful outcome reporting. |

The skill is a set of working habits, not a persona. It changes *how* the model works — what it checks before destructive commands, what counts as "done", how it labels confidence — not how it sounds.

## Activation

Say any of these in a session where the skill is installed:

- `fable mode` / `fable mode on`
- `fable it`
- `think like fable` / `act like fable`
- `mythos mode`

It also triggers implicitly on work where a careless shortcut would be expensive to undo (production changes, data migrations, destructive operations, stubborn debugging), and deactivates with `fable mode off`.

## Installation

### Claude Code — personal (all projects)

Copy the skill folder into your user skills directory:

**Windows (PowerShell)** — invoked with `-ExecutionPolicy Bypass` because stock Windows blocks running `.ps1` scripts directly:
```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

**macOS / Linux**
```bash
sh install.sh
```

Or manually: copy `skills/fable-mode/` to `~/.claude/skills/fable-mode/`.

### Claude Code — per project

Copy `skills/fable-mode/` into `<your-project>/.claude/skills/fable-mode/`.

### Claude.ai / Claude Desktop

Zip the `skills/fable-mode/` folder (the zip should contain the `fable-mode` folder with `SKILL.md` inside it) and upload the `.zip` as-is via **Settings → Capabilities → Skills**. A ready-made `dist/fable-mode.zip` is included.

## Verifying it's installed

Start a new Claude Code session and type `fable mode`. The model should acknowledge with a short "Fable mode on." and visibly change how it works — leading answers with outcomes, verifying changes by running them, and labeling claims as confirmed vs. inferred.

## License

MIT — see [LICENSE](LICENSE).
