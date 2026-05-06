---
name: agents
description: Show every agent in the current team — model, auth status, active model override, and last session activity. One-stop overview for managing the multi-agent team.
---

# /agent-team:agents

Display the master agent overview: every role in `team.json`, the model backing it, its auth/install status, and the active model (factoring in `team.local.json` overrides).

**Your first output must be:** `🤖 Agent Team — Provider Status`

## Steps

### 1. Find Team Config

```bash
TEAM_CONFIG=$(bash ${CLAUDE_PLUGIN_ROOT}/scripts/find-team-config.sh 2>/dev/null)
if [[ -z "$TEAM_CONFIG" ]]; then
  echo "No team.json found. Run /agent-team:setup first."
  exit 0
fi
```

### 2. Detect Providers (JSON)

```bash
source "${CLAUDE_PLUGIN_ROOT}/scripts/lib/common.sh"
PROVIDERS=$(bash ${CLAUDE_PLUGIN_ROOT}/scripts/check-providers.sh --json)
```

### 3. Merge team.json with team.local.json

```bash
MERGED=$(merge_team_config "$TEAM_CONFIG")
```

### 4. Render Table

For each role in the merged config, look up the provider status block by model and print:
- Role name + emoji
- Provider model (codex / opencode / copilot / gemini / claude)
- Auth status (✓ with auth method, or ✗ with reason)
- Active model — `opencode_model` / `codex_model` / `gemini_model` from the merged config (i.e. team.local.json override if present), otherwise the provider default

Example output:

```
🤖 Agent Team — Provider Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Role                Model      Auth                Active Model
─────────────────────────────────────────────────────────────────
🔴 Frontend Eng     codex      ✓ chatgpt-oauth     o4-mini
⚫ Backend Eng      opencode   ✓ github-copilot    github-copilot/claude-sonnet-4.5
🟢 QA Engineer      copilot    ✓ gh-cli            (shell suggestions)
🟡 Researcher       gemini     ✗ not installed     —
🔵 Coordinator      claude     ✓ claude-code       claude-sonnet-4.6
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 5. Show Latest Session (if any)

```bash
LATEST=$(ls -t ~/.agent-team/sessions/ 2>/dev/null | head -1)
if [[ -n "$LATEST" ]]; then
  echo ""
  echo "Most recent session: ${LATEST}"
  echo "  Status: $(cat ~/.agent-team/sessions/${LATEST}/status 2>/dev/null)"
  echo "  Round:  $(cat ~/.agent-team/sessions/${LATEST}/round 2>/dev/null)"
fi
```

### 6. Hint at Per-Provider Commands

End with:

```
Manage individual providers:
  /agent-team:codex-login     /agent-team:codex-status     /agent-team:codex-model
  /agent-team:opencode-login  /agent-team:opencode-status  /agent-team:opencode-model
  /agent-team:gemini-login    /agent-team:gemini-status    /agent-team:gemini-model
```
