#!/usr/bin/env bash
# Gemini agent status: version, auth, model. Zero Claude tokens.
PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$PLUGIN_ROOT/scripts/lib/common.sh"

echo "🟡 Gemini Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v gemini &>/dev/null; then
  echo "Install      : ❌ gemini not found"
  echo "               npm install -g @google/gemini-cli"
  exit 1
fi

VERSION=$(gemini --version 2>/dev/null || echo "unknown")
echo "Version      : $VERSION"

AUTH_FOUND=false
ACCOUNT=""
for D in "$HOME/.gemini" "$HOME/.config/google-gemini" "$HOME/.config/gemini"; do
  if [[ -d "$D" ]]; then
    AUTH_FOUND=true
    ACCOUNT=$(grep -hoE '"email"[[:space:]]*:[[:space:]]*"[^"]+"' "$D"/*.json 2>/dev/null \
              | head -1 | sed -E 's/.*"([^"]+)"$/\1/' || true)
    break
  fi
done

if $AUTH_FOUND; then
  echo "Auth         : ✓ ${ACCOUNT:-credentials present}"
else
  echo "Auth         : ✗ not authenticated — run /agent-team:gemini-login"
fi

ACTIVE_MODEL="default"
GEM_ROLES="(none)"
TEAM_CONFIG=$(bash "$PLUGIN_ROOT/scripts/find-team-config.sh" 2>/dev/null || true)
if [[ -n "$TEAM_CONFIG" ]]; then
  MERGED=$(merge_team_config "$TEAM_CONFIG" 2>/dev/null || cat "$TEAM_CONFIG")
  _M=$(echo "$MERGED" | jq -r '.roles[]? | select(.model=="gemini") | .gemini_model // empty' 2>/dev/null | head -1)
  _R=$(echo "$MERGED" | jq -r '.roles[]? | select(.model=="gemini") | .id' 2>/dev/null | paste -sd, -)
  [[ -n "$_M" ]] && ACTIVE_MODEL="$_M"
  [[ -n "$_R" ]] && GEM_ROLES="$_R"
fi
echo "Active model : $ACTIVE_MODEL"
echo "Roles using  : $GEM_ROLES"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "See also: /agent-team:gemini-login  /agent-team:gemini-model"
