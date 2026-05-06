#!/bin/bash
# Dispatch a task to the Codex CLI agent.
#
# Session persistence strategy:
#   Round 1  — fresh `codex exec --full-auto --json`; all previous-round results
#               are injected into the prompt as "Prior Work" so the agent has full
#               memory of what it already analyzed or built.
#   Round 2+ — same approach; accumulated results give the agent continuity.
#               True interactive resume is not used because `codex resume` requires
#               interactive TTY; context injection is more reliable for automation.
#
# Usage: source codex.sh; dispatch_codex <prompt> <result-file> <work-dir> <results-dir>
# results-dir: agent's results dir — previous round files are loaded as context

dispatch_codex() {
  local PROMPT="$1"
  local RESULT_FILE="$2"
  local WORK_DIR="${3:-$PWD}"
  local RESULTS_DIR="${4:-}"
  local MODEL_OVERRIDE="${5:-}"
  local PROFILE_FILE="${6:-}"

  # Resolve model: arg > profile > default
  local EFFECTIVE_MODEL="${MODEL_OVERRIDE:-}"
  if [[ -z "$EFFECTIVE_MODEL" ]] && [[ -n "$PROFILE_FILE" ]] && [[ -f "$PROFILE_FILE" ]]; then
    EFFECTIVE_MODEL=$(jq -r '.codex_model // ""' "$PROFILE_FILE" 2>/dev/null || true)
  fi
  EFFECTIVE_MODEL="${EFFECTIVE_MODEL:-gpt-5.4}"
  echo "  [codex] Using model: ${EFFECTIVE_MODEL}" >&2

  local MODEL_ARGS=(-m "$EFFECTIVE_MODEL")

  if ! command -v codex &>/dev/null; then
    echo "ERROR: codex CLI not found. Install: npm install -g @openai/codex && codex login" >&2
    return 1
  fi

  # ── Inject prior-round results for continuity ──────────────────────────────
  # This gives the agent full memory of its own previous work without needing
  # a persistent process — functionally equivalent from the agent's perspective.
  local PRIOR_CONTEXT=""
  if [[ -n "$RESULTS_DIR" ]] && [[ -d "$RESULTS_DIR" ]]; then
    local PRIOR_FILES
    mapfile -t PRIOR_FILES < <(ls "$RESULTS_DIR"/*.md 2>/dev/null | sort -V)
    if [[ ${#PRIOR_FILES[@]} -gt 0 ]]; then
      PRIOR_CONTEXT=$'\n\n## Your Prior Work (from previous rounds)\n'
      PRIOR_CONTEXT+='The following is your own output from earlier rounds. '
      PRIOR_CONTEXT+='Continue from where you left off — do not repeat completed work.'$'\n\n'
      for f in "${PRIOR_FILES[@]}"; do
        local ROUND_NUM
        ROUND_NUM=$(basename "$f" | grep -o '^[0-9]*')
        PRIOR_CONTEXT+="### Round ${ROUND_NUM} result\n"
        PRIOR_CONTEXT+=$(cat "$f")
        PRIOR_CONTEXT+=$'\n\n'
      done
    fi
  fi

  local FULL_PROMPT="${PRIOR_CONTEXT}${PROMPT}"

  # ── Run Codex ─────────────────────────────────────────────────────────────
  # Tee raw output to a temp file so it streams live to the terminal (tmux pane)
  # while also being captured for post-processing.
  local RAW_TMP EXIT_CODE
  RAW_TMP=$(mktemp /tmp/codex_raw_XXXXXX.jsonl)

  (
    cd "$WORK_DIR" || exit 1
    codex exec \
      --dangerously-bypass-approvals-and-sandbox \
      --skip-git-repo-check \
      --json \
      "${MODEL_ARGS[@]}" \
      "$FULL_PROMPT" 2>&1
  ) | tee "$RAW_TMP"
  EXIT_CODE=${PIPESTATUS[0]}

  # ── Extract text from JSON event stream ───────────────────────────────────
  grep -o '"text":"[^"]*"' "$RAW_TMP" \
    | sed 's/"text":"//;s/"$//' \
    | sed 's/\\n/\n/g;s/\\t/\t/g' \
    > "$RESULT_FILE"
  rm -f "$RAW_TMP"

  if [[ ! -s "$RESULT_FILE" ]]; then
    echo "$RAW" > "$RESULT_FILE"
  fi

  [[ $EXIT_CODE -ne 0 ]] && echo "⚠ Codex exited with code $EXIT_CODE" >> "$RESULT_FILE"
  return $EXIT_CODE
}
