#!/usr/bin/env bash
# OpenCode agent status: version, auth, model. Zero Claude tokens.
PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$PLUGIN_ROOT/scripts/lib/common.sh"

echo "⚫ OpenCode Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

OC_BIN=""
if [[ -x "$HOME/.opencode/bin/opencode" ]]; then
  OC_BIN="$HOME/.opencode/bin/opencode"
elif command -v opencode &>/dev/null; then
  OC_BIN="$(command -v opencode)"
fi

if [[ -z "$OC_BIN" ]]; then
  echo "Install      : ❌ opencode not found"
  echo "               curl -fsSL https://opencode.ai/install | bash"
  exit 1
fi

VERSION=$("$OC_BIN" --version 2>/dev/null || echo "unknown")
echo "Version      : $VERSION"
echo "Binary       : $OC_BIN"

AUTH_OUT=$("$OC_BIN" auth list 2>&1 || true)
if echo "$AUTH_OUT" | grep -qiE 'github.copilot|anthropic|openrouter|credentials'; then
  PROVIDER=$(echo "$AUTH_OUT" | grep -oiE 'GitHub Copilot|Anthropic|OpenRouter' | head -1)
  echo "Auth         : ✓ ${PROVIDER:-authenticated}"
else
  echo "Auth         : ✗ not authenticated — run /agent-team:opencode-login"
fi

ACTIVE_MODEL="default"
OC_ROLES="(none)"
TEAM_CONFIG=$(bash "$PLUGIN_ROOT/scripts/find-team-config.sh" 2>/dev/null || true)
if [[ -n "$TEAM_CONFIG" ]]; then
  MERGED=$(merge_team_config "$TEAM_CONFIG" 2>/dev/null || cat "$TEAM_CONFIG")
  _M=$(echo "$MERGED" | jq -r '.roles[]? | select(.model=="opencode") | .opencode_model // empty' 2>/dev/null | head -1)
  _R=$(echo "$MERGED" | jq -r '.roles[]? | select(.model=="opencode") | .id' 2>/dev/null | paste -sd, -)
  [[ -n "$_M" ]] && ACTIVE_MODEL="$_M"
  [[ -n "$_R" ]] && OC_ROLES="$_R"
fi
echo "Active model : $ACTIVE_MODEL"
echo "Roles using  : $OC_ROLES"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "See also: /agent-team:opencode-login  /agent-team:opencode-model"
