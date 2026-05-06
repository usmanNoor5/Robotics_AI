#!/bin/bash
# Detect which model providers are available on this machine.
# Outputs a JSON object with availability and auth method for each provider.
# Usage: check-providers.sh [--json]

source "${CLAUDE_PLUGIN_ROOT}/scripts/lib/common.sh" 2>/dev/null || {
  CLAUDE_PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
  source "${CLAUDE_PLUGIN_ROOT}/scripts/lib/common.sh"
}

JSON_MODE=false
[[ "$1" == "--json" ]] && JSON_MODE=true

check_codex() {
  if ! command -v codex &>/dev/null; then
    echo '{"available":false,"auth":"none","reason":"codex CLI not installed (npm install -g @openai/codex)"}'
    return
  fi
  if codex --version &>/dev/null 2>&1; then
    if [[ -n "$OPENAI_API_KEY" ]]; then
      echo '{"available":true,"auth":"api-key"}'
    else
      echo '{"available":true,"auth":"chatgpt-oauth"}'
    fi
  else
    echo '{"available":false,"auth":"none","reason":"codex CLI installed but not authenticated (run: codex login)"}'
  fi
}

check_copilot() {
  # Strategy 1: standalone copilot CLI (real GA CLI, not VS Code stub)
  local copilot_bin
  copilot_bin=$(command -v copilot 2>/dev/null)
  if [[ -n "$copilot_bin" ]]; then
    # Validate it's real (VS Code stub outputs "Cannot find GitHub Copilot CLI")
    local test_out
    test_out=$("$copilot_bin" --version 2>&1)
    if echo "$test_out" | grep -qi "cannot find\|install github copilot"; then
      copilot_bin=""  # it's just the broken VS Code stub
    fi
  fi

  if [[ -n "$copilot_bin" ]]; then
    echo "{\"available\":true,\"auth\":\"gh-subscription\",\"mode\":\"copilot-cli\",\"bin\":\"$copilot_bin\"}"
    return
  fi

  # Strategy 2: gh copilot extension (limited but functional)
  if command -v gh &>/dev/null && gh copilot --version &>/dev/null 2>&1; then
    echo '{"available":true,"auth":"gh-cli","mode":"gh-copilot-extension","note":"limited to shell suggestions"}'
    return
  fi

  echo '{"available":false,"auth":"none","reason":"Copilot CLI not installed — see: https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli"}'
}

check_opencode() {
  local OPENCODE_BIN="${HOME}/.opencode/bin/opencode"
  [[ ! -x "$OPENCODE_BIN" ]] && OPENCODE_BIN=$(command -v opencode 2>/dev/null)

  if [[ -z "$OPENCODE_BIN" ]] || [[ ! -x "$OPENCODE_BIN" ]]; then
    echo '{"available":false,"auth":"none","reason":"opencode not installed (curl -fsSL https://opencode.ai/install | bash)"}'
    return
  fi

  local VERSION
  VERSION=$("$OPENCODE_BIN" --version 2>/dev/null | tr -d '\n')

  # Check which providers are configured in opencode
  local AUTH_INFO=""
  local AUTH_LIST
  AUTH_LIST=$("$OPENCODE_BIN" auth list 2>/dev/null || true)
  if echo "$AUTH_LIST" | grep -qi "github.copilot\|GitHub Copilot"; then
    AUTH_INFO="github-copilot"
  elif echo "$AUTH_LIST" | grep -qi "anthropic"; then
    AUTH_INFO="anthropic"
  elif echo "$AUTH_LIST" | grep -qi "openrouter"; then
    AUTH_INFO="openrouter"
  elif echo "$AUTH_LIST" | grep -qi "credentials\|credential"; then
    AUTH_INFO="authenticated"
  else
    echo '{"available":false,"auth":"none","reason":"opencode not authenticated — run: opencode auth login"}'
    return
  fi

  echo "{\"available\":true,\"auth\":\"${AUTH_INFO}\",\"version\":\"${VERSION}\",\"bin\":\"${OPENCODE_BIN}\"}"
}

check_gemini() {
  if ! command -v gemini &>/dev/null; then
    echo '{"available":false,"auth":"none","reason":"gemini CLI not installed (npm install -g @google/gemini-cli)"}'
    return
  fi
  if [[ -n "$GEMINI_API_KEY" ]] || [[ -n "$GOOGLE_API_KEY" ]]; then
    echo '{"available":true,"auth":"api-key"}'
  else
    echo '{"available":true,"auth":"google-oauth"}'
  fi
}

check_claude() {
  if command -v claude &>/dev/null; then
    echo '{"available":true,"auth":"claude-code"}'
  else
    echo '{"available":false,"auth":"none","reason":"claude CLI not found"}'
  fi
}

CODEX=$(check_codex)
COPILOT=$(check_copilot)
OPENCODE=$(check_opencode)
GEMINI=$(check_gemini)
CLAUDE=$(check_claude)

if $JSON_MODE; then
  printf '{"codex":%s,"copilot":%s,"opencode":%s,"gemini":%s,"claude":%s}\n' \
    "$CODEX" "$COPILOT" "$OPENCODE" "$GEMINI" "$CLAUDE"
  exit 0
fi

# Human-readable output
echo ""
echo -e "${BOLD}🤖 Agent Team — Provider Detection${RESET}"
echo "──────────────────────────────────────"

print_status() {
  local model="$1" emoji="$2" data="$3"
  local available auth reason note
  available=$(echo "$data" | jq -r '.available' 2>/dev/null)
  auth=$(echo "$data" | jq -r '.auth' 2>/dev/null)
  reason=$(echo "$data" | jq -r '.reason // ""' 2>/dev/null)
  note=$(echo "$data" | jq -r '.note // ""' 2>/dev/null)

  if [[ "$available" == "true" ]]; then
    local EXTRA=""
    [[ -n "$note" ]] && EXTRA=" (${note})"
    echo -e "  ${emoji} ${GREEN}✓${RESET} ${BOLD}${model}${RESET} — auth: ${auth}${EXTRA}"
  else
    echo -e "  ${emoji} ${RED}✗${RESET} ${BOLD}${model}${RESET} — ${reason}"
  fi
}

print_status "Codex"    "🔴" "$CODEX"
print_status "Copilot"  "🟢" "$COPILOT"
print_status "OpenCode" "⚫" "$OPENCODE"
print_status "Gemini"   "🟡" "$GEMINI"
print_status "Claude"   "🔵" "$CLAUDE"
echo ""

AVAILABLE_COUNT=$(printf '%s\n' "$CODEX" "$COPILOT" "$OPENCODE" "$GEMINI" "$CLAUDE" | \
  grep -c '"available":true' || true)

if [[ "$AVAILABLE_COUNT" -eq 0 ]]; then
  echo -e "  ${RED}No providers available.${RESET} Install at least one model CLI to use agent-team."
  exit 1
elif [[ "$AVAILABLE_COUNT" -eq 1 ]]; then
  echo -e "  ${YELLOW}1 provider available.${RESET} Team will work but with limited model diversity."
else
  echo -e "  ${GREEN}${AVAILABLE_COUNT} providers available.${RESET} Ready to build your team."
fi
echo ""
