#!/usr/bin/env bash
# Set Gemini model in team.local.json. Zero Claude tokens.
# Usage: cmd-gemini-model.sh [model] [role-id|all]
PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$PLUGIN_ROOT/scripts/lib/common.sh"

VALID_MODELS=(
  "gemini-3.1-pro"
  "gemini-3-pro"
  "gemini-3-flash"
  "gemini-3.1-flash-lite-preview"
  "gemini-3-flash-preview"
  "gemini-3-pro-preview"
  "gemini-2.5-pro"
  "gemini-2.5-flash"
  "gemini-2.5-flash-lite"
  "gemini-2.0-flash"
  "gemini-1.5-pro"
  "gemini-1.5-flash"
)

TEAM_CONFIG=$(bash "$PLUGIN_ROOT/scripts/find-team-config.sh" 2>/dev/null || true)
if [[ -z "$TEAM_CONFIG" ]]; then
  echo "❌ No team.json found. Run /agent-team:setup first."
  exit 1
fi
PROJECT_ROOT="$(dirname "$TEAM_CONFIG")"
LOCAL_CONFIG="${PROJECT_ROOT}/team.local.json"

GEM_ROLE_LIST=$(jq -r '.roles[]? | select(.model=="gemini") | .id' "$TEAM_CONFIG" 2>/dev/null || true)

SELECTED_MODEL="${1:-}"
TARGET="${2:-all}"

if [[ -z "$SELECTED_MODEL" ]]; then
  echo "🟡 Gemini Model"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  MERGED=$(merge_team_config "$TEAM_CONFIG" 2>/dev/null || cat "$TEAM_CONFIG")
  CURRENT=$(echo "$MERGED" | jq -r '.roles[]? | select(.model=="gemini") | .gemini_model // empty' 2>/dev/null | head -1)
  GEM_ROLES_INLINE=$(echo "$GEM_ROLE_LIST" | tr '\n' ',' | sed 's/,$//')
  echo "Current : ${CURRENT:-default}   Roles: ${GEM_ROLES_INLINE:-(none)}"
  exit 0
fi

VALID=false
for M in "${VALID_MODELS[@]}"; do [[ "$SELECTED_MODEL" == "$M" ]] && VALID=true && break; done
if ! $VALID; then
  echo "❌ Unknown model: $SELECTED_MODEL"
  echo "   Valid: ${VALID_MODELS[*]}"
  exit 1
fi

if [[ "$TARGET" == "all" ]]; then
  readarray -t TARGETS <<< "$GEM_ROLE_LIST"
else
  TARGETS=("$TARGET")
fi

if [[ ${#TARGETS[@]} -eq 0 || -z "${TARGETS[0]}" ]]; then
  echo "❌ No gemini roles found in team.json."
  exit 1
fi

[[ -f "$LOCAL_CONFIG" ]] && CURRENT_JSON=$(cat "$LOCAL_CONFIG") || CURRENT_JSON='{"roles": []}'

for ROLE_ID in "${TARGETS[@]}"; do
  [[ -z "$ROLE_ID" ]] && continue
  CURRENT_JSON=$(echo "$CURRENT_JSON" | jq \
    --arg id "$ROLE_ID" --arg m "$SELECTED_MODEL" '
      .roles = (
        (.roles // []) as $roles |
        if any($roles[]; .id == $id) then
          [$roles[] | if .id == $id then .gemini_model = $m else . end]
        else
          $roles + [{"id": $id, "gemini_model": $m}]
        end
      )
    ')
done

echo "$CURRENT_JSON" | jq '.' > "$LOCAL_CONFIG"

APPLIED=$(printf '%s\n' "${TARGETS[@]}" | grep -v '^$' | paste -sd, -)
echo "🟡 Gemini Model"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Model set to : $SELECTED_MODEL"
echo "  Saved to     : $LOCAL_CONFIG (gitignored)"
echo "  Applied to   : $APPLIED"
echo ""
echo "Active on the next /agent-team:start."
