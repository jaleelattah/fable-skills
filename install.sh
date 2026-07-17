#!/usr/bin/env sh
# Installs the fable-mode skill into the user-level Claude Code skills directory.
set -e
DEST="$HOME/.claude/skills/fable-mode"
SRC="$(cd "$(dirname "$0")" && pwd)/skills/fable-mode"
mkdir -p "$DEST"
cp -R "$SRC/." "$DEST/"
echo "Installed fable-mode to $DEST"
echo "Start a new Claude Code session and say 'fable mode' to activate."
