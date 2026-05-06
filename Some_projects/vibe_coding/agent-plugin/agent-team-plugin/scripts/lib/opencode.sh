#!/bin/bash
# Dispatch a task to OpenCode (opencode CLI).
# OpenCode supports native session persistence: first run starts a new session,
# subsequent runs continue the SAME session so the agent remembers all prior work.
#
# Usage: source opencode.sh; dispatch_opencode <prompt> <result-file> <work-dir> <profile-file> [model]
# profile-file: path to agent's profile.json — stores opencode_session_id and opencode_model

OPENCODE_BIN="${HOME}/.opencode/bin/opencode"
[[ ! -x "$OPENCODE_BIN" ]] && OPENCODE_BIN=$(command -v opencode 2>/dev/null || true)

dispatch_opencode() {
  local PROMPT="$1"
  local RESULT_FILE="$2"
  local WORK_DIR="${3:-$PWD}"
  local PROFILE_FILE="${4:-}"
  local MODEL_OVERRIDE="${5:-}"

  if [[ -z "$OPENCODE_BIN" ]] || [[ ! -x "$OPENCODE_BIN" ]]; then
    echo "ERROR: opencode not found. Install: curl -fsSL https://opencode.ai/install | bash" >&2
    return 1
  fi

  # ── Resolve session continuity ─────────────────────────────────────────────
  local SESSION_ARGS=()
  local SAVED_SESSION=""

  if [[ -n "$PROFILE_FILE" ]] && [[ -f "$PROFILE_FILE" ]]; then
    SAVED_SESSION=$(jq -r '.opencode_session_id // ""' "$PROFILE_FILE" 2>/dev/null || true)
    [[ -z "$MODEL_OVERRIDE" ]] && \
      MODEL_OVERRIDE=$(jq -r '.opencode_model // ""' "$PROFILE_FILE" 2>/dev/null || true)
  fi

  if [[ -n "$SAVED_SESSION" ]]; then
    SESSION_ARGS=("-s" "$SAVED_SESSION")
    echo "  [opencode] Resuming session ${SAVED_SESSION}" >&2
  else
    echo "  [opencode] Starting new session" >&2
  fi

  local EFFECTIVE_MODEL="${MODEL_OVERRIDE:-github-copilot/gpt-5.3-codex}"
  echo "  [opencode] Using model: ${EFFECTIVE_MODEL}" >&2

  # ── Run OpenCode ───────────────────────────────────────────────────────────
  # Tee raw JSONL to a temp file so it streams live to the terminal (tmux pane)
  # while also being captured for post-processing.
  local RAW_TMP EXIT_CODE
  RAW_TMP=$(mktemp /tmp/opencode_raw_XXXXXX.jsonl)

  (
    cd "$WORK_DIR" || exit 1
    "$OPENCODE_BIN" run \
      "${SESSION_ARGS[@]}" \
      -m "$EFFECTIVE_MODEL" \
      --dangerously-skip-permissions \
      --format json \
      "$PROMPT" 2>&1
  ) | tee "$RAW_TMP"
  EXIT_CODE=${PIPESTATUS[0]}

  # ── Extract session ID ─────────────────────────────────────────────────────
  local NEW_SESSION
  NEW_SESSION=$(jq -r 'select(.sessionID != null) | .sessionID' "$RAW_TMP" 2>/dev/null | head -1 || true)

  # ── Extract text content from JSONL event stream using jq ─────────────────
  jq -r 'select(.type == "text") | .part.text' "$RAW_TMP" 2>/dev/null > "$RESULT_FILE"
  rm -f "$RAW_TMP"

  # If jq extraction yielded nothing, leave result file as-is (may have raw output from tee)

  # ── Save session ID for future rounds ─────────────────────────────────────
  if [[ -z "$SAVED_SESSION" ]] && [[ -n "$PROFILE_FILE" ]] && [[ -f "$PROFILE_FILE" ]] && [[ -n "$NEW_SESSION" ]]; then
    jq --arg sid "$NEW_SESSION" '.opencode_session_id = $sid' \
      "$PROFILE_FILE" > "${PROFILE_FILE}.tmp" \
      && mv "${PROFILE_FILE}.tmp" "$PROFILE_FILE"
    echo "  [opencode] Session ID saved: ${NEW_SESSION}" >&2
  fi

  [[ $EXIT_CODE -ne 0 ]] && echo "⚠ opencode exited with code $EXIT_CODE" >> "$RESULT_FILE"
  return $EXIT_CODE
}
