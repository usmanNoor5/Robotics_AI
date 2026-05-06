#!/bin/bash
# Install the agent-team post-commit hook so the plugin auto-syncs
# from source to the Claude Code installed cache after every commit.
#
# Run once after cloning the repo:
#   bash plugins/agent-team/scripts/install-hook.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
HOOK_SRC="$SCRIPT_DIR/../.git-hooks/post-commit"
HOOK_DEST="$REPO_ROOT/.git/hooks/post-commit"

if [[ ! -f "$HOOK_SRC" ]]; then
  echo "ERROR: Hook source not found at $HOOK_SRC" >&2
  exit 1
fi

cp "$HOOK_SRC" "$HOOK_DEST"
chmod +x "$HOOK_DEST"

echo "post-commit hook installed at $HOOK_DEST"
echo "Next commit will auto-sync plugins/agent-team/ to ~/.claude/plugins/cache/"
