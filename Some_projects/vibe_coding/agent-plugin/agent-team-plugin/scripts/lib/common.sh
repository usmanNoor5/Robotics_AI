#!/bin/bash
# Shared utilities for agent-team plugin

AGENT_TEAM_HOME="${HOME}/.agent-team"

# ── Colours ────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

log_info()    { echo -e "${CYAN}[agent-team]${RESET} $*"; }
log_success() { echo -e "${GREEN}[agent-team]${RESET} $*"; }
log_warn()    { echo -e "${YELLOW}[agent-team]${RESET} $*"; }
log_error()   { echo -e "${RED}[agent-team]${RESET} $*" >&2; }

# ── Session helpers ────────────────────────────────────────────────────────
session_dir()  { echo "${AGENT_TEAM_HOME}/sessions/$1"; }
agent_dir()    { echo "${AGENT_TEAM_HOME}/sessions/$1/agents/$2"; }
coordinator_dir() { echo "${AGENT_TEAM_HOME}/sessions/$1/coordinator"; }

new_session_id() { date +%Y%m%d-%H%M%S-$(openssl rand -hex 3 2>/dev/null || echo "$(RANDOM)"); }
new_message_id() { echo "msg-$(date +%s)-$(openssl rand -hex 3 2>/dev/null || echo "$(RANDOM)")"; }

# ── JSON helpers (requires jq) ─────────────────────────────────────────────
require_jq() {
  if ! command -v jq &>/dev/null; then
    log_error "jq is required but not installed. Install with: sudo apt install jq / brew install jq"
    exit 1
  fi
}

# ── Team config ────────────────────────────────────────────────────────────
find_team_config() {
  # Walk up from cwd looking for team.json
  local dir="$PWD"
  while [[ "$dir" != "/" ]]; do
    [[ -f "$dir/team.json" ]] && { echo "$dir/team.json"; return 0; }
    dir="$(dirname "$dir")"
  done
  # Also check .agent-team/team.json in cwd
  [[ -f "$PWD/.agent-team/team.json" ]] && { echo "$PWD/.agent-team/team.json"; return 0; }
  return 1
}

# ── Merge team.json with team.local.json (gitignored overrides) ────────────
# team.local.json sits next to team.json. Per-role fields (e.g. model,
# opencode_model) in the local file override the base on a per-id basis.
# Top-level keys in the local file (e.g. roles list additions) are NOT merged
# — only per-role overrides matched by id.
#
# Output: merged JSON document on stdout.
merge_team_config() {
  local BASE="$1"
  local LOCAL="${BASE%.json}.local.json"

  if [[ ! -f "$BASE" ]]; then
    log_error "team.json not found: $BASE"
    return 1
  fi

  if [[ -f "$LOCAL" ]]; then
    jq -s '
      .[0] as $base | .[1] as $local |
      $base | .roles = [
        $base.roles[] as $r |
        (($local.roles // []) | map(select(.id == $r.id)) | first) as $override |
        if $override then $r * $override else $r end
      ]
    ' "$BASE" "$LOCAL"
  else
    cat "$BASE"
  fi
}

# ── Model emoji ────────────────────────────────────────────────────────────
model_emoji() {
  case "$1" in
    codex)    echo "🔴" ;;
    copilot)  echo "🟢" ;;
    opencode) echo "⚫" ;;
    gemini)   echo "🟡" ;;
    claude)   echo "🔵" ;;
    *)        echo "⚪" ;;
  esac
}
