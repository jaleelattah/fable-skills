#!/usr/bin/env sh
# Install into one selected host's skills directory.
set -eu

usage() {
    cat <<'EOF'
Usage: sh install.sh [--target claude|codex | --skills-dir PATH] [--force]

  --target claude   Claude Code (default); respects CLAUDE_CONFIG_DIR.
  --target codex    Codex: ~/.agents/skills.
  --skills-dir     Custom parent directory; adds fable-mode underneath it.
  --force          Overwrite bundled files in an existing installation.
                   Extra files are preserved. Linked destinations are refused.
  --help           Show this help.
EOF
}

fail() { printf '%s\n' "$*" >&2; exit 1; }

# Check structural conflicts before copying; other I/O errors can still fail later.
check_layout() (
    for source_path in "$1"/* "$1"/.[!.]* "$1"/..?*; do
        [ -e "$source_path" ] || [ -L "$source_path" ] || continue
        destination_path="$2/${source_path##*/}"
        [ -e "$destination_path" ] || continue
        if [ -d "$source_path" ]; then
            [ -d "$destination_path" ] || fail "Destination type conflict: $destination_path must be a directory."
            check_layout "$source_path" "$destination_path"
        else
            [ ! -d "$destination_path" ] || fail "Destination type conflict: $destination_path must be a file."
        fi
    done
)

target=claude
selected=false
skills_dir=
force=false
while [ "$#" -gt 0 ]; do
    case "$1" in
        --target|--skills-dir)
            [ "$#" -ge 2 ] && [ -n "$2" ] || fail "$1 needs a value."
            case "$2" in
                --target|--skills-dir|--force|--help|-h) fail "$1 needs a value before $2." ;;
            esac
            [ "$selected" = false ] || fail "Choose one --target or --skills-dir."
            selected=true
            if [ "$1" = --target ]; then target=$2; else skills_dir=$2; fi
            shift 2 ;;
        --force) force=true; shift ;;
        --help|-h) usage; exit 0 ;;
        *) fail "Unknown argument: $1. Use --help for usage." ;;
    esac
done

if [ -z "$skills_dir" ]; then
    case "$target" in
        claude) skills_dir="${CLAUDE_CONFIG_DIR:-${HOME:?HOME is not set}/.claude}/skills" ;;
        codex) skills_dir="${HOME:?HOME is not set}/.agents/skills" ;;
        *) fail "Unknown target: $target. Choose claude or codex." ;;
    esac
fi
case "$skills_dir" in /*) ;; *) skills_dir="$(pwd)/$skills_dir" ;; esac
src="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/skills/fable-mode"
[ -f "$src/SKILL.md" ] || fail "Skill source missing: $src/SKILL.md"
dest="$skills_dir/fable-mode"

[ ! -L "$dest" ] || fail "Refusing linked destination: $dest"
if [ -e "$dest" ]; then
    [ "$force" = true ] || fail "Already exists: $dest. Review it, then use --force to overwrite bundled files."
    [ -d "$dest" ] || fail "Destination is not a directory: $dest"
    [ -z "$(find "$dest" -type l -print -quit)" ] || fail "Refusing destination containing symbolic links: $dest"
    check_layout "$src" "$dest"
fi

mkdir -p "$dest"
cp -R "$src/." "$dest/"
printf 'Installed fable-mode to %s\n' "$dest"
printf '%s\n' "Select the skill in your host or ask it to use Fable Mode. See README.md for activation."
