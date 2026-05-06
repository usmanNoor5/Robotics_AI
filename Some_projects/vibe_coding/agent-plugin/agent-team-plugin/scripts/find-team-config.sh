#!/bin/bash
# Find team.json by walking up from the current directory.
# Outputs the absolute path if found, exits 1 if not.

DIR="$PWD"
while [[ "$DIR" != "/" ]]; do
  [[ -f "$DIR/team.json" ]] && { echo "$DIR/team.json"; exit 0; }
  DIR="$(dirname "$DIR")"
done

[[ -f "$PWD/.agent-team/team.json" ]] && { echo "$PWD/.agent-team/team.json"; exit 0; }

echo "No team.json found. Run /agent-team:setup to create one." >&2
exit 1
