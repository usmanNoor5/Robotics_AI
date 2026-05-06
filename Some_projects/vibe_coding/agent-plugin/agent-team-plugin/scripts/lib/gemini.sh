#!/bin/bash
# Dispatch a task to the Google Gemini CLI.
# Uses OAuth or API key from the user's existing setup.
# Usage: source gemini.sh; dispatch_gemini <prompt> <result-file> [work-dir] [profile-file] [model]

dispatch_gemini() {
  local PROMPT="$1"
  local RESULT_FILE="$2"
  local WORK_DIR="${3:-$PWD}"
  local PROFILE_FILE="${4:-}"
  local MODEL_OVERRIDE="${5:-}"
  local RESULTS_DIR="${6:-}"

  if ! command -v gemini &>/dev/null; then
    echo "ERROR: gemini CLI not found. Install: npm install -g @google/gemini-cli" >&2
    return 1
  fi

  # Resolve model from profile or override
  local EFFECTIVE_MODEL="${MODEL_OVERRIDE:-gemini-3-flash-preview}"
  if [[ -z "$EFFECTIVE_MODEL" ]] && [[ -n "$PROFILE_FILE" ]] && [[ -f "$PROFILE_FILE" ]]; then
    EFFECTIVE_MODEL=$(jq -r '.gemini_model // ""' "$PROFILE_FILE" 2>/dev/null || true)
  fi

  local MODEL_ARGS=()
  [[ -n "$EFFECTIVE_MODEL" ]] && MODEL_ARGS=("-m" "$EFFECTIVE_MODEL")

  echo "  [gemini] Using model: ${EFFECTIVE_MODEL:-default}" >&2

  # ── Inject prior-round results for continuity ──────────────────────────────
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

  (
    cd "$WORK_DIR" || exit 1
    gemini \
      --skip-trust \
      --approval-mode yolo \
      -p "$FULL_PROMPT" \
      "${MODEL_ARGS[@]}" \
      2>&1
  ) > "$RESULT_FILE"

  local EXIT_CODE=$?

  # Detect quota/rate-limit errors — return exit code 2 so dispatch-agent.sh
  # can trigger automatic model fallback instead of treating this as a hard failure.
  if [[ $EXIT_CODE -ne 0 ]]; then
    if grep -qiE 'QUOTA_EXHAUSTED|quota.*reset|exhausted.*capacity|429|rate.limit' "$RESULT_FILE" 2>/dev/null; then
      echo "⚠ Gemini quota exhausted — triggering fallback" >> "$RESULT_FILE"
      return 2
    fi
    echo "⚠ Gemini exited with code $EXIT_CODE" >> "$RESULT_FILE"
  fi

  return $EXIT_CODE
}
