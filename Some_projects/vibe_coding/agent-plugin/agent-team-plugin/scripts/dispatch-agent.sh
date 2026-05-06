#!/bin/bash
# Dispatch a single agent for one round.
# Assembles context, reads inbox, builds prompt, calls model, routes messages.
#
# Usage: dispatch-agent.sh <session-id> <agent-id> <task> <round>
#
# Session persistence:
#   - opencode agents: session ID stored in profile.json (opencode_session_id)
#                      Each round resumes the SAME opencode session.
#   - codex agents:    prior round results are injected into the prompt so the
#                      agent has full memory of its previous work.
#   - gemini/copilot:  same context-injection approach as codex.

set -euo pipefail

source "${CLAUDE_PLUGIN_ROOT}/scripts/lib/common.sh" 2>/dev/null || {
  CLAUDE_PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
  source "${CLAUDE_PLUGIN_ROOT}/scripts/lib/common.sh"
}
source "${CLAUDE_PLUGIN_ROOT}/scripts/lib/codex.sh"
source "${CLAUDE_PLUGIN_ROOT}/scripts/lib/copilot.sh"
source "${CLAUDE_PLUGIN_ROOT}/scripts/lib/gemini.sh"
source "${CLAUDE_PLUGIN_ROOT}/scripts/lib/opencode.sh"

require_jq

SESSION_ID="${1:?Usage: dispatch-agent.sh <session-id> <agent-id> <task> <round>}"
AGENT_ID="${2:?agent-id required}"
TASK="${3:?task required}"
ROUND="${4:-1}"

SESSION_DIR="$(session_dir "$SESSION_ID")"
AGENT_DIR="$(agent_dir "$SESSION_ID" "$AGENT_ID")"
PROFILE="$AGENT_DIR/profile.json"

[[ -f "$PROFILE" ]] || { log_error "Agent profile not found: $PROFILE"; exit 1; }

# ── Read agent profile ─────────────────────────────────────────────────────
MODEL=$(jq -r '.model' "$PROFILE")
AGENT_NAME=$(jq -r '.name' "$PROFILE")
EXPERTISE=$(jq -r '.expertise' "$PROFILE")
CONTEXT_DIRS=$(jq -c '.context_dirs' "$PROFILE")
PROJECT_ROOT=$(jq -r '.project_root' "$PROFILE")

EMOJI="$(model_emoji "$MODEL")"
log_info "${EMOJI} Dispatching ${AGENT_NAME} (${MODEL}) — Round ${ROUND}"

# ── Update agent status ────────────────────────────────────────────────────
jq '.status = "working"' "$PROFILE" > "${PROFILE}.tmp" && mv "${PROFILE}.tmp" "$PROFILE"

# ── Load directory context ─────────────────────────────────────────────────
log_info "  Loading context from ${CONTEXT_DIRS}..."
CONTEXT=$("${CLAUDE_PLUGIN_ROOT}/scripts/load-context.sh" \
  "$PROJECT_ROOT" "$CONTEXT_DIRS" 2>/dev/null \
  || echo "## Context\n_Context unavailable._")

# ── Read inbox messages ────────────────────────────────────────────────────
INBOX_CONTENT=$("${CLAUDE_PLUGIN_ROOT}/scripts/read-inbox.sh" \
  "$AGENT_DIR/inbox" 2>/dev/null || echo "")

# ── Load cross-session memory (top-3 relevant past sessions) ───────────────
PAST_MEMORY=$("${CLAUDE_PLUGIN_ROOT}/scripts/load-memory.sh" "$TASK" 3 2>/dev/null || echo "")

# ── Read teammate list for communication instructions ─────────────────────
TEAM_JSON="$SESSION_DIR/team.json"
TEAMMATE_LIST=$(jq -r \
  '.roles[] | select(.id != "'"$AGENT_ID"'") | "- \(.name) (id: \(.id))"' \
  "$TEAM_JSON" 2>/dev/null || echo "")

# ── Project Briefing (first ~50 lines of planning/PLAN.md if present) ─────
PLAN_FILE="${PROJECT_ROOT}/planning/PLAN.md"
if [[ -f "$PLAN_FILE" ]]; then
  PROJECT_BRIEFING=$(head -50 "$PLAN_FILE")
else
  PROJECT_BRIEFING="No planning/PLAN.md found at ${PROJECT_ROOT}. Read README.md or any top-level docs to orient yourself."
fi

# ── Build full prompt ──────────────────────────────────────────────────────
PROMPT="$(cat <<PROMPT_EOF
You are the ${AGENT_NAME} on an AI engineering team. Your expertise: ${EXPERTISE}.

## Project Briefing
Project root: ${PROJECT_ROOT}

The first ~50 lines of planning/PLAN.md (or a fallback note) follow. Read this to
understand what this project is, what is built, and what is in progress. Open the
full PLAN.md yourself if you need more.

${PROJECT_BRIEFING}

## Your Mission — Round ${ROUND}
${TASK}

What DONE looks like: the coordinator will check your result file. Be explicit
about what you completed, what files you created or modified, and any blockers
you hit.

## Your Team
${TEAMMATE_LIST}
- Coordinator (id: coordinator) — assigned you this task

## File Tree — Your Context
${CONTEXT}

## Messages from Teammates
${INBOX_CONTENT}

## Past Session Memory
Relevant learnings from previous agent-team sessions on similar tasks.
Use this to avoid repeating past mistakes and to apply patterns that worked.
${PAST_MEMORY:-_No relevant past sessions found._}

## MCP Tool Requests
If you need external documentation or the coordinator to fetch something for you,
include this exact line in your response:

  MESSAGE TO coordinator: FETCH DOCS <library-name> <specific-topic>

The coordinator will fetch it and inject the result in your next round inbox.

## How to Message Teammates
Include messages in your response using this exact format (one per line):

  MESSAGE TO <teammate-id>: <your message here>

Example:
  MESSAGE TO backend: I need /api/prices to also return a 24h high/low field.
  MESSAGE TO coordinator: Done. Created 3 new components in frontend/components/.

## Instructions
- Read the key files listed in your file tree section before writing any code.
- Do actual work — write complete files, not snippets.
- Send a message to any teammate whose work yours depends on.
- State explicitly what you completed at the end of your response.
PROMPT_EOF
)"

# ── Dispatch to model ──────────────────────────────────────────────────────
RESULT_FILE="$AGENT_DIR/results/${ROUND}-result.md"
mkdir -p "$AGENT_DIR/results"

# Fallback chains: when a model returns exit code 2 (quota/rate-limit), retry
# automatically with the next model in the chain — same round, no user action needed.
# Format: "primary_model:fallback1:fallback2"
declare -A FALLBACK_CHAIN
FALLBACK_CHAIN[gemini]="opencode:codex"
FALLBACK_CHAIN[opencode]="codex"
FALLBACK_CHAIN[codex]="opencode"
FALLBACK_CHAIN[copilot]="opencode"

try_dispatch() {
  local TRY_MODEL="$1"
  log_info "  Trying model: ${TRY_MODEL}"

  case "$TRY_MODEL" in
    codex)
      CODEX_MODEL=$(jq -r '.codex_model // ""' "$PROFILE" 2>/dev/null)
      dispatch_codex "$PROMPT" "$RESULT_FILE" "$PROJECT_ROOT" "$AGENT_DIR/results" "$CODEX_MODEL" "$PROFILE"
      ;;
    opencode)
      OPENCODE_MODEL=$(jq -r '.opencode_model // ""' "$PROFILE" 2>/dev/null)
      [[ -z "$OPENCODE_MODEL" ]] && OPENCODE_MODEL="github-copilot/gpt-5.3-codex"
      dispatch_opencode "$PROMPT" "$RESULT_FILE" "$PROJECT_ROOT" "$PROFILE" "$OPENCODE_MODEL"
      ;;
    copilot)
      dispatch_copilot "$PROMPT" "$RESULT_FILE"
      ;;
    gemini)
      GEMINI_MODEL=$(jq -r '.gemini_model // ""' "$PROFILE" 2>/dev/null)
      dispatch_gemini "$PROMPT" "$RESULT_FILE" "$PROJECT_ROOT" "$PROFILE" "$GEMINI_MODEL" "$AGENT_DIR/results"
      ;;
    *)
      return 1
      ;;
  esac
}

DISPATCH_SUCCESS=false
ACTIVE_MODEL="$MODEL"

if [[ "$MODEL" == "claude" ]]; then
  log_info "  Claude agent '${AGENT_ID}' — coordinator invokes via native Agent tool."
  {
    echo "# Claude Agent: ${AGENT_NAME} — Round ${ROUND}"
    echo "_Invoked by coordinator via native Agent tool._"
    echo ""
    echo "Task: ${TASK}"
  } > "$RESULT_FILE"
  DISPATCH_SUCCESS=true
else
  # Build ordered model list: primary + fallbacks
  FALLBACKS="${FALLBACK_CHAIN[$MODEL]:-}"
  MODEL_ORDER=("$MODEL")
  IFS=':' read -ra FB_LIST <<< "$FALLBACKS"
  for fb in "${FB_LIST[@]}"; do
    MODEL_ORDER+=("$fb")
  done

  for TRY_MODEL in "${MODEL_ORDER[@]}"; do
    try_dispatch "$TRY_MODEL"
    EXIT=$?

    if [[ $EXIT -eq 0 ]]; then
      ACTIVE_MODEL="$TRY_MODEL"
      DISPATCH_SUCCESS=true
      [[ "$TRY_MODEL" != "$MODEL" ]] && \
        log_info "  ✅ Fallback succeeded with: ${TRY_MODEL}"
      break
    elif [[ $EXIT -eq 2 ]]; then
      log_info "  ⚠ ${TRY_MODEL} quota exhausted — trying next fallback..."
      # Clear result file so fallback starts fresh
      > "$RESULT_FILE"
    else
      log_error "  ${TRY_MODEL} failed with exit code ${EXIT}"
      break
    fi
  done
fi

# ── Parse and route outbound messages from result ──────────────────────────
if [[ -f "$RESULT_FILE" ]] && $DISPATCH_SUCCESS; then
  log_info "  Parsing messages from ${AGENT_NAME}..."

  while IFS= read -r LINE; do
    if [[ "$LINE" =~ ^[[:space:]]*MESSAGE[[:space:]]+TO[[:space:]]+([^:]+):[[:space:]]*(.+)$ ]]; then
      TO_ID="${BASH_REMATCH[1]// /}"
      MSG_CONTENT="${BASH_REMATCH[2]}"

      "${CLAUDE_PLUGIN_ROOT}/scripts/send-message.sh" \
        "$SESSION_ID" "$AGENT_ID" "$TO_ID" "$MSG_CONTENT" "$ROUND" 2>/dev/null \
        && log_info "  ✉ Routed: ${AGENT_NAME} → ${TO_ID}"
    fi
  done < "$RESULT_FILE"
fi

# ── Update agent status ────────────────────────────────────────────────────
STATUS=$($DISPATCH_SUCCESS && echo "done" || echo "error")
jq --arg s "$STATUS" --arg r "$ROUND" \
  '.status = $s | .last_round = ($r | tonumber)' \
  "$PROFILE" > "${PROFILE}.tmp" && mv "${PROFILE}.tmp" "$PROFILE"

if $DISPATCH_SUCCESS; then
  log_success "${EMOJI} ${AGENT_NAME} finished Round ${ROUND} → $(basename $RESULT_FILE)"
else
  log_error "${EMOJI} ${AGENT_NAME} failed on Round ${ROUND}"
  exit 1
fi
