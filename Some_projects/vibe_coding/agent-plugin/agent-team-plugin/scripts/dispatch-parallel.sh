#!/bin/bash
# Dispatch all non-Claude agents in parallel, then report which ones need
# Claude-native Agent tool invocation (coordinator handles those directly).
#
# Usage: dispatch-parallel.sh <session-id> <round> <tasks-json>
#
# tasks-json: JSON array of {id, task} objects, one per agent.
# Example:
#   '[{"id":"frontend","task":"Review components and list gaps"},
#     {"id":"backend","task":"Audit all API endpoints"},
#     {"id":"tester","task":"Identify missing test coverage"}]'
#
# Exit behaviour:
#   Exits 0 if all non-Claude agents succeeded (even if some had warnings).
#   Exits 1 if any non-Claude agent failed hard.
#   Writes a summary to ~/.agent-team/sessions/<id>/coordinator/rounds/<round>-dispatch.log

set -uo pipefail

source "${CLAUDE_PLUGIN_ROOT}/scripts/lib/common.sh" 2>/dev/null || {
  CLAUDE_PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
  source "${CLAUDE_PLUGIN_ROOT}/scripts/lib/common.sh"
}

require_jq

SESSION_ID="${1:?Usage: dispatch-parallel.sh <session-id> <round> <tasks-json>}"
ROUND="${2:?round required}"
TASKS_JSON="${3:?tasks-json required}"

SESSION_DIR="$(session_dir "$SESSION_ID")"
LOG_DIR="${SESSION_DIR}/coordinator/rounds"
mkdir -p "$LOG_DIR"
DISPATCH_LOG="${LOG_DIR}/${ROUND}-dispatch.log"

echo "Round ${ROUND} parallel dispatch — $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$DISPATCH_LOG"
echo "" >> "$DISPATCH_LOG"

# ── Split tasks into parallel (non-claude) and sequential (claude) ─────────
declare -A PIDS          # agent_id → background PID
declare -a CLAUDE_IDS=() # claude agents to report back to coordinator
declare -a ALL_IDS=()    # all agent IDs for result collection

mapfile -t TASK_ARRAY < <(echo "$TASKS_JSON" | jq -c '.[]')

for TASK_OBJ in "${TASK_ARRAY[@]}"; do
  AGENT_ID=$(echo "$TASK_OBJ" | jq -r '.id')
  TASK=$(echo "$TASK_OBJ" | jq -r '.task')
  PROFILE="$(agent_dir "$SESSION_ID" "$AGENT_ID")/profile.json"
  MODEL=$(jq -r '.model' "$PROFILE" 2>/dev/null || echo "unknown")
  EMOJI=$(model_emoji "$MODEL")

  ALL_IDS+=("$AGENT_ID")

  if [[ "$MODEL" == "claude" ]]; then
    # Claude agents need the coordinator's native Agent tool — flag them
    CLAUDE_IDS+=("$AGENT_ID")
    log_info "${EMOJI} ${AGENT_ID} (claude) — queued for coordinator Agent tool"
    echo "CLAUDE_AGENT: ${AGENT_ID} | task: ${TASK}" >> "$DISPATCH_LOG"
  else
    # Fire non-Claude agents as background processes simultaneously
    log_info "${EMOJI} ${AGENT_ID} (${MODEL}) — launching in background..."
    echo "DISPATCHING: ${AGENT_ID} (${MODEL})" >> "$DISPATCH_LOG"

    bash "${CLAUDE_PLUGIN_ROOT}/scripts/dispatch-agent.sh" \
      "$SESSION_ID" "$AGENT_ID" "$TASK" "$ROUND" \
      >> "$DISPATCH_LOG" 2>&1 &

    PIDS["$AGENT_ID"]=$!
  fi
done

# ── Report Claude agents for coordinator to handle ─────────────────────────
if [[ ${#CLAUDE_IDS[@]} -gt 0 ]]; then
  echo ""
  log_info "The following agents need coordinator (Claude native Agent tool) dispatch:"
  for CID in "${CLAUDE_IDS[@]}"; do
    echo "  → $CID"
  done
  echo ""
fi

# ── Wait for all background agents to finish ───────────────────────────────
FAILED_AGENTS=()
mapfile -t PIDS_KEYS < <(echo "${!PIDS[@]}" | tr ' ' '\n')
for AGENT_ID in "${PIDS_KEYS[@]}"; do
  PID="${PIDS[$AGENT_ID]}"
  MODEL=$(jq -r '.model' "$(agent_dir "$SESSION_ID" "$AGENT_ID")/profile.json" 2>/dev/null)
  EMOJI=$(model_emoji "$MODEL")

  wait "$PID" && {
    log_success "${EMOJI} ${AGENT_ID} — DONE"
    echo "DONE: ${AGENT_ID}" >> "$DISPATCH_LOG"
  } || {
    log_error "${EMOJI} ${AGENT_ID} — FAILED (exit $?)"
    echo "FAILED: ${AGENT_ID}" >> "$DISPATCH_LOG"
    FAILED_AGENTS+=("$AGENT_ID")
  }
done

# ── Summary ────────────────────────────────────────────────────────────────
echo "" >> "$DISPATCH_LOG"
echo "Parallel dispatch complete at $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$DISPATCH_LOG"
echo "Failed: ${FAILED_AGENTS[*]:-none}" >> "$DISPATCH_LOG"

if [[ ${#CLAUDE_IDS[@]} -gt 0 ]]; then
  echo ""
  echo "CLAUDE_AGENTS_PENDING=${CLAUDE_IDS[*]}"
fi

if [[ ${#FAILED_AGENTS[@]} -gt 0 ]]; then
  log_error "Round ${ROUND} — ${#FAILED_AGENTS[@]} agent(s) failed: ${FAILED_AGENTS[*]}"
  exit 1
fi

log_success "Round ${ROUND} — all parallel agents finished."
