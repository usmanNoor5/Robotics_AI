#!/bin/bash
# Initialise a new agent-team session.
# Creates the full directory structure for agent inboxes, outboxes, results.
# Usage: init-session.sh <session-id> <team-config-path> <project-root>
# Outputs: session directory path

set -euo pipefail

source "${CLAUDE_PLUGIN_ROOT}/scripts/lib/common.sh" 2>/dev/null || {
  CLAUDE_PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
  source "${CLAUDE_PLUGIN_ROOT}/scripts/lib/common.sh"
}

require_jq

SESSION_ID="${1:?Usage: init-session.sh <session-id> <team-config> <project-root>}"
TEAM_CONFIG="${2:?team config path required}"
PROJECT_ROOT="${3:-$PWD}"

SESSION_DIR="$(session_dir "$SESSION_ID")"

[[ -f "$TEAM_CONFIG" ]] || { log_error "team.json not found: $TEAM_CONFIG"; exit 1; }

# ── Create session directory tree ──────────────────────────────────────────
mkdir -p "$SESSION_DIR"/{coordinator/inbox,coordinator/rounds,logs}

# Merge team.json + team.local.json (if present) and snapshot the result.
# All downstream code reads from $SESSION_DIR/team.json which is the merged
# document — this means model overrides from team.local.json apply to the
# session without ever being written back to the committed team.json.
MERGED_TEAM="$SESSION_DIR/team.json"
if ! merge_team_config "$TEAM_CONFIG" > "$MERGED_TEAM"; then
  log_error "Failed to merge team config"
  exit 1
fi
echo "$PROJECT_ROOT" > "$SESSION_DIR/project-root"
echo "pending" > "$SESSION_DIR/status"
echo "0" > "$SESSION_DIR/round"

# ── Create per-agent directories ───────────────────────────────────────────
ROLE_COUNT=$(jq '.roles | length' "$MERGED_TEAM")

for i in $(seq 0 $((ROLE_COUNT - 1))); do
  AGENT_ID=$(jq -r ".roles[$i].id" "$MERGED_TEAM")
  AGENT_NAME=$(jq -r ".roles[$i].name" "$MERGED_TEAM")
  MODEL=$(jq -r ".roles[$i].model" "$MERGED_TEAM")
  EXPERTISE=$(jq -r ".roles[$i].expertise" "$MERGED_TEAM")
  CONTEXT_DIRS=$(jq -c ".roles[$i].context_dirs" "$MERGED_TEAM")
  OPENCODE_MODEL=$(jq -r ".roles[$i].opencode_model // \"\"" "$MERGED_TEAM")
  CODEX_MODEL=$(jq -r ".roles[$i].codex_model // \"\"" "$MERGED_TEAM")
  GEMINI_MODEL=$(jq -r ".roles[$i].gemini_model // \"\"" "$MERGED_TEAM")

  ADIR="$SESSION_DIR/agents/$AGENT_ID"
  mkdir -p "$ADIR"/{inbox,outbox,results}

  # Write agent profile
  cat > "$ADIR/profile.json" <<EOF
{
  "id": "$AGENT_ID",
  "name": "$AGENT_NAME",
  "model": "$MODEL",
  "expertise": "$EXPERTISE",
  "context_dirs": $CONTEXT_DIRS,
  "opencode_model": "$OPENCODE_MODEL",
  "codex_model": "$CODEX_MODEL",
  "gemini_model": "$GEMINI_MODEL",
  "status": "idle",
  "project_root": "$PROJECT_ROOT"
}
EOF
done

# ── Write session manifest ─────────────────────────────────────────────────
cat > "$SESSION_DIR/session.json" <<EOF
{
  "session_id": "$SESSION_ID",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "project_root": "$PROJECT_ROOT",
  "team_config": "$TEAM_CONFIG",
  "status": "pending",
  "round": 0
}
EOF

log_success "Session initialised: $SESSION_DIR"
echo "$SESSION_DIR"
