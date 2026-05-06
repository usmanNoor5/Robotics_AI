#!/usr/bin/env bash
# Set Codex model in team.local.json. Zero Claude tokens.
# Usage: cmd-codex-model.sh [model] [role-id|all]
PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$PLUGIN_ROOT/scripts/lib/common.sh"

VALID_MODELS=(
  "gpt-5.5"
  "gpt-5.4"
  "gpt-5.4-mini"
  "gpt-5.3-codex"
  "gpt-5.2"
  "codex-auto-review"
)

TEAM_CONFIG=$(bash "$PLUGIN_ROOT/scripts/find-team-config.sh" 2>/dev/null || true)
if [[ -z "$TEAM_CONFIG" ]]; then
  echo "❌ No team.json found. Run /agent-team:setup first."
  exit 1
fi
PROJECT_ROOT="$(dirname "$TEAM_CONFIG")"
LOCAL_CONFIG="${PROJECT_ROOT}/team.local.json"

CODEX_ROLE_LIST=$(jq -r '.roles[]? | select(.model=="codex") | .id' "$TEAM_CONFIG" 2>/dev/null || true)

SELECTED_MODEL="${1:-}"
TARGET="${2:-all}"

if [[ -z "$SELECTED_MODEL" ]]; then
  echo "🔴 Codex Model"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  MERGED=$(merge_team_config "$TEAM_CONFIG" 2>/dev/null || cat "$TEAM_CONFIG")
  CURRENT=$(echo "$MERGED" | jq -r '.roles[]? | select(.model=="codex") | .codex_model // empty' 2>/dev/null | head -1)
  CODEX_ROLES_INLINE=$(echo "$CODEX_ROLE_LIST" | tr '\n' ',' | sed 's/,$//')
  echo "Current : ${CURRENT:-default}   Roles: ${CODEX_ROLES_INLINE:-(none)}"
  echo ""

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
  readarray -t TARGETS <<< "$CODEX_ROLE_LIST"
else
  TARGETS=("$TARGET")
fi

if [[ ${#TARGETS[@]} -eq 0 || -z "${TARGETS[0]}" ]]; then
  echo "❌ No codex roles found in team.json."
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
          [$roles[] | if .id == $id then .codex_model = $m else . end]
        else
          $roles + [{"id": $id, "codex_model": $m}]
        end
      )
    ')
done

echo "$CURRENT_JSON" | jq '.' > "$LOCAL_CONFIG"

APPLIED=$(printf '%s\n' "${TARGETS[@]}" | grep -v '^$' | paste -sd, -)
echo "🔴 Codex Model"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Model set to : $SELECTED_MODEL"
echo "  Saved to     : $LOCAL_CONFIG (gitignored)"
echo "  Applied to   : $APPLIED"
echo ""
echo "Active on the next /agent-team:start."
