# Delivering the whole skill

Type: failure lesson and procedure
Status: current
Applies to: this repository's Fable Mode distribution, ZIP creation, and shell installation

## Knowledge

Fable Mode loads detailed guidance from files beside its entrypoint. Adding or
editing a reference requires updating the distribution ZIP as well as the source.
The ZIP should contain the entire `fable-mode/` directory with forward slashes in
entry names. A source-only change can leave archive users with stale or missing
instructions. Keep this project knowledge directory outside that distribution.

## Evidence and limits

- [Skill entrypoint](../../skills/fable-mode/SKILL.md) links the required references.
- [Shell installer](../../install.sh) copies the entire skill directory recursively.
- [PowerShell installer](../../install.ps1) also specifies recursive copying;
  its execution has not been tested in this environment.
- [Package tool](../../scripts/package_skill.py) builds and checks source/ZIP
  parity and inline local Markdown targets. Use `python3 scripts/package_skill.py
  --check` from the repository root for a read-only check, or `--build` after
  source edits. See [development checks](../../README.md#development-checks).
- [Regression tests](../../tests/test_package_skill.py) exercise missing or changed
  resources, malformed archives, and failed-build preservation; the
  [installer tests](../../tests/test_install.py) cover destination updates in
  temporary directories.
- [Distribution archive](../../dist/fable-mode.zip) is a generated copy, not the
  canonical editing location. The original archive at repository commit
  `5af95c6` used a backslash in its sole member name, `fable-mode\SKILL.md`.

Last checked: 2026-09-16, the local uncommitted working tree. The package build and
read-only check compared ZIP member names and bytes against all 9 bundled files.
The shell installer regression suite compared a temporary installation against
the source, including the nested references and Python helpers. These checks
cover delivered files, not model behavior or Windows execution.

## Recheck when

Any file under `skills/fable-mode/`, either installer, or the packaging approach
changes. Run the package check and relevant regression tests; rebuild when source
changes require it. Do not refresh this note's check date without performing the
relevant checks. Structural installer conflicts are rejected before copying, but
later I/O errors can still leave partial updates.
