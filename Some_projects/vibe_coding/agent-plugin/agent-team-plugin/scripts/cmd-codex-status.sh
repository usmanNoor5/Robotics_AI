#!/usr/bin/env bash
# Codex agent status: auth, model, daily limit. Zero Claude tokens.
PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$PLUGIN_ROOT/scripts/lib/common.sh"

echo "🔴 Codex Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v codex &>/dev/null; then
  echo "Install      : ❌ codex not found"
  echo "               npm install -g @openai/codex"
  exit 1
fi

AUTH_RAW=$(codex login status 2>&1 || true)
if echo "$AUTH_RAW" | grep -qi "logged in"; then
  echo "Auth         : ✓ $AUTH_RAW"
else
  echo "Auth         : ✗ not authenticated — run /agent-team:codex-login"
fi

ACTIVE_MODEL="default"
CODEX_ROLES="(none)"
TEAM_CONFIG=$(bash "$PLUGIN_ROOT/scripts/find-team-config.sh" 2>/dev/null || true)
if [[ -n "$TEAM_CONFIG" ]]; then
  MERGED=$(merge_team_config "$TEAM_CONFIG" 2>/dev/null || cat "$TEAM_CONFIG")
  _M=$(echo "$MERGED" | jq -r '.roles[]? | select(.model=="codex") | .codex_model // empty' 2>/dev/null | head -1)
  _R=$(echo "$MERGED" | jq -r '.roles[]? | select(.model=="codex") | .id' 2>/dev/null | paste -sd, -)
  [[ -n "$_M" ]] && ACTIVE_MODEL="$_M"
  [[ -n "$_R" ]] && CODEX_ROLES="$_R"
fi
echo "Active model : $ACTIVE_MODEL"
echo "Roles using  : $CODEX_ROLES"

echo ""
echo "Probing daily limit (may take ~10s)..."
PROBE=$(timeout 25 codex exec \
  --dangerously-bypass-approvals-and-sandbox \
  --skip-git-repo-check --json "ping" 2>&1 | head -60 || true)

if echo "$PROBE" | grep -qiE 'rate.?limit|daily.?limit|quota|usage.?limit'; then
  RESET=$(echo "$PROBE" | grep -oiE 'try again[^\n]{0,80}' | head -1)
  echo "Daily limit  : ⚠ REACHED${RESET:+ — $RESET}"
else
  echo "Daily limit  : ✓ OK — agent is dispatchable"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "See also: /agent-team:codex-login  /agent-team:codex-model"
