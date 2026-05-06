#!/bin/bash
# Dispatch a task to GitHub Copilot.
# Tries three approaches in order:
#   1. Standalone Copilot CLI (copilot -p) — new GA CLI, subscription-based
#   2. gh copilot suggest — older gh extension (shell commands only, limited)
#   3. Fallback error with install instructions
# Usage: source copilot.sh; dispatch_copilot <prompt> <result-file>

dispatch_copilot() {
  local PROMPT="$1"
  local RESULT_FILE="$2"

  # ── Option 1: Standalone Copilot CLI (copilot -p) ─────────────────────────
  # The new GitHub Copilot CLI (GA Feb 2026): https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli
  # Install: gh extension install github/gh-copilot  OR  direct download from GitHub
  local COPILOT_BIN
  COPILOT_BIN=$(command -v copilot 2>/dev/null)

  # Validate it's the real CLI (not the VS Code stub which fails with "Cannot find")
  if [[ -n "$COPILOT_BIN" ]]; then
    local TEST_OUT
    TEST_OUT=$("$COPILOT_BIN" --version 2>&1)
    if echo "$TEST_OUT" | grep -qi "cannot find\|install\|not found"; then
      COPILOT_BIN=""  # stub, not real
    fi
  fi

  if [[ -n "$COPILOT_BIN" ]]; then
    "$COPILOT_BIN" -p "$PROMPT" --no-ask-user 2>&1 > "$RESULT_FILE"
    return $?
  fi

  # ── Option 2: gh copilot (deprecated but may still work for some users) ────
  if command -v gh &>/dev/null && gh copilot --version &>/dev/null 2>&1; then
    # gh copilot is limited to shell command suggestions — wrap the task
    local SHELL_PROMPT="You are a software engineer. ${PROMPT}. Describe the exact shell commands and code needed."
    gh copilot suggest -t shell "$SHELL_PROMPT" 2>&1 > "$RESULT_FILE"
    echo "" >> "$RESULT_FILE"
    echo "_Note: Response generated via gh copilot suggest (shell-command mode). For full code generation, install the Copilot CLI._" >> "$RESULT_FILE"
    return 0
  fi

  # ── Option 3: Not available ────────────────────────────────────────────────
  cat > "$RESULT_FILE" <<'EOF'
## Copilot Not Available

The GitHub Copilot CLI is not installed or authenticated on this machine.

**To install:**
1. Visit: https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli
2. Or install the gh extension: `gh extension install github/gh-copilot`
3. Authenticate: `copilot login` (uses your GitHub Copilot subscription)

**Workaround:** Change this agent's model to `codex`, `gemini`, or `claude` in your `team.json`.
EOF
  return 1
}
