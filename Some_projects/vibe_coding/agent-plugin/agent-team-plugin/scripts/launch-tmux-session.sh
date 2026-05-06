#!/bin/bash
# Launch the agent team in a tmux session with one pane per agent.
# Each non-Claude agent runs dispatch-agent.sh live inside its pane so the user
# can watch every agent work in real time.
#
# Usage: launch-tmux-session.sh <session-id> <team-config> <project-root> <task>
#
# After running, attach with:
#   tmux attach -t agent-team-<session-id>

set -euo pipefail

source "${CLAUDE_PLUGIN_ROOT}/scripts/lib/common.sh" 2>/dev/null || {
  CLAUDE_PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
  source "${CLAUDE_PLUGIN_ROOT}/scripts/lib/common.sh"
}

SESSION_ID="${1:?Usage: launch-tmux-session.sh <session-id> <team-config> <project-root> <task>}"
TEAM_CONFIG="${2:?team-config path required}"
PROJECT_ROOT="${3:?project-root required}"
TASK="${4:?task required}"

require_jq

[[ -f "$TEAM_CONFIG" ]] || { log_error "team config not found: $TEAM_CONFIG"; exit 1; }
command -v tmux &>/dev/null || { log_error "tmux not installed. Run: sudo apt install tmux"; exit 1; }

TMUX_SESSION="agent-team-${SESSION_ID}"
SESSION_DIR="${HOME}/.agent-team/sessions/${SESSION_ID}"

# Init the agent-team session (idempotent — caller may have already done this)
if [[ ! -d "$SESSION_DIR" ]]; then
  log_info "Initialising session ${SESSION_ID}..."
  bash "${CLAUDE_PLUGIN_ROOT}/scripts/init-session.sh" \
    "$SESSION_ID" "$TEAM_CONFIG" "$PROJECT_ROOT" >/dev/null
fi

# Save SESSION_ID where Claude (coordinator) can read it
echo "$SESSION_ID" > "$PROJECT_ROOT/.agent-team-session"

# ── Write per-agent task files ────────────────────────────────────────────
# Each agent gets a copy of the same top-level task. The dispatch-agent.sh
# script wraps it in the role-specific prompt (identity, expertise, context)
# at run time, so role specialisation happens there — not here.
TASKS_DIR="$SESSION_DIR/tasks"
mkdir -p "$TASKS_DIR"

# Read role list from the (possibly merged) team config
MERGED_CONFIG=$(merge_team_config "$TEAM_CONFIG")

ROLE_IDS=()
while IFS= read -r RID; do ROLE_IDS+=("$RID"); done < <(echo "$MERGED_CONFIG" | jq -r '.roles[].id')

for RID in "${ROLE_IDS[@]}"; do
  printf '%s\n' "$TASK" > "$TASKS_DIR/${RID}.txt"
done

# ── Create tmux session ────────────────────────────────────────────────────
log_info "Creating tmux session '${TMUX_SESSION}'..."
tmux kill-session -t "$TMUX_SESSION" 2>/dev/null || true

# Generous dimensions so the file tree + dispatcher logs are readable
tmux new-session -d -s "$TMUX_SESSION" -x 220 -y 55

# Spawn one pane per role beyond the first (which the new-session already gave us)
NUM_ROLES=${#ROLE_IDS[@]}
for ((i = 1; i < NUM_ROLES; i++)); do
  tmux split-window -d -t "${TMUX_SESSION}:0"
done
tmux select-layout -t "${TMUX_SESSION}:0" tiled

# ── Dispatch each agent into its pane ─────────────────────────────────────
DISPATCH_SCRIPT="${CLAUDE_PLUGIN_ROOT}/scripts/dispatch-agent.sh"
DONE_FLAG_DIR="$SESSION_DIR/.tmux-done"
mkdir -p "$DONE_FLAG_DIR"

for ((PANE = 0; PANE < NUM_ROLES; PANE++)); do
  AGENT_ID="${ROLE_IDS[$PANE]}"
  AGENT_NAME=$(echo "$MERGED_CONFIG" | jq -r --arg id "$AGENT_ID" '.roles[] | select(.id==$id) | .name')
  MODEL=$(echo "$MERGED_CONFIG" | jq -r --arg id "$AGENT_ID" '.roles[] | select(.id==$id) | .model')
  EMOJI="$(model_emoji "$MODEL")"
  LABEL="${EMOJI} ${AGENT_NAME} (${MODEL})"

  TASK_FILE="$TASKS_DIR/${AGENT_ID}.txt"
  DONE_FLAG="$DONE_FLAG_DIR/${AGENT_ID}.done"

  # Set pane title (works in modern tmux)
  tmux send-keys -t "${TMUX_SESSION}:0.${PANE}" \
    "printf '\\033]2;${LABEL}\\033\\\\'" Enter

  if [[ "$MODEL" == "claude" ]]; then
    # Claude agents are dispatched by the coordinator via the native Agent tool;
    # there's no shell-side process to show inside tmux. Print a clear message.
    tmux send-keys -t "${TMUX_SESSION}:0.${PANE}" \
      "clear; echo ''; echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'; \
       echo '  ${LABEL}'; \
       echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'; \
       echo ''; \
       echo '  Claude agents are dispatched by the coordinator —'; \
       echo '  check Claude Code output above this terminal.'; \
       echo ''; \
       echo '  This pane stays idle by design.'; \
       echo ''; \
       touch '${DONE_FLAG}'" Enter
  else
    # Codex / OpenCode / Copilot / Gemini agents: run dispatch live in the pane
    tmux send-keys -t "${TMUX_SESSION}:0.${PANE}" \
      "export CLAUDE_PLUGIN_ROOT='${CLAUDE_PLUGIN_ROOT}'; \
       clear; echo ''; \
       echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'; \
       echo '  ${LABEL}'; \
       echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'; \
       echo '  Session: ${SESSION_ID}'; \
       echo '  Agent  : ${AGENT_ID}'; \
       echo ''; \
       (bash '${DISPATCH_SCRIPT}' '${SESSION_ID}' '${AGENT_ID}' \"\$(cat '${TASK_FILE}')\" 1 \
          && echo '' && echo '━━━ ✅ DONE ━━━' \
          || echo '━━━ ❌ FAILED ━━━'); \
       touch '${DONE_FLAG}'" Enter
  fi
done

# ── Background watcher: when all agents finish, prompt the user ────────────
WATCHER_SCRIPT="$SESSION_DIR/.tmux-watcher.sh"
cat > "$WATCHER_SCRIPT" <<WATCH_EOF
#!/bin/bash
# Wait for every agent to drop its done flag, then notify each pane.
EXPECTED=${NUM_ROLES}
while true; do
  COUNT=\$(ls "${DONE_FLAG_DIR}"/*.done 2>/dev/null | wc -l)
  if [[ "\$COUNT" -ge "\$EXPECTED" ]]; then
    for ((P=0; P<\$EXPECTED; P++)); do
      tmux send-keys -t "${TMUX_SESSION}:0.\${P}" \
        "echo ''; echo '━━━ All agents done. Press any key to close tmux. ━━━'; read -n1 -s -r; tmux kill-session -t ${TMUX_SESSION}" Enter 2>/dev/null || true
    done
    exit 0
  fi
  sleep 2
done
WATCH_EOF
chmod +x "$WATCHER_SCRIPT"
nohup "$WATCHER_SCRIPT" >/dev/null 2>&1 &

# ── Print summary ──────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}🤖 Agent Team Launched (tmux mode)${RESET}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Session ID : ${SESSION_ID}"
echo "  Session dir: ${SESSION_DIR}"
echo "  Team config: ${TEAM_CONFIG}"
echo "  Project    : ${PROJECT_ROOT}"
echo ""
echo "  Agents:"
PANE_NUM=0
for RID in "${ROLE_IDS[@]}"; do
  ANAME=$(echo "$MERGED_CONFIG" | jq -r --arg id "$RID" '.roles[] | select(.id==$id) | .name')
  AMODEL=$(echo "$MERGED_CONFIG" | jq -r --arg id "$RID" '.roles[] | select(.id==$id) | .model')
  AEMOJI="$(model_emoji "$AMODEL")"
  echo "  ${AEMOJI} Pane ${PANE_NUM} — ${ANAME} (${AMODEL})"
  PANE_NUM=$((PANE_NUM + 1))
done
echo ""
echo -e "  ${GREEN}Attach now:${RESET}"
echo "  tmux attach -t ${TMUX_SESSION}"
echo ""
echo "  Navigate panes: Ctrl+B then arrow keys"
echo "  Zoom a pane:    Ctrl+B then Z"
echo "  Detach:         Ctrl+B then D"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "SESSION_ID=$SESSION_ID"
