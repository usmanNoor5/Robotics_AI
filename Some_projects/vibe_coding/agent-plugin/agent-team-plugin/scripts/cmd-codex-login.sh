#!/usr/bin/env bash
# Check Codex auth state and print instructions if not logged in. Zero Claude tokens.
echo "🔴 Codex Login"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v codex &>/dev/null; then
  echo "❌ codex CLI not installed."
  echo "   Run: npm install -g @openai/codex"
  exit 1
fi

AUTH=$(codex login status 2>&1 || true)

if echo "$AUTH" | grep -qi "logged in"; then
  echo "✓ $AUTH"
  echo ""
  echo "Daily limit: run /agent-team:codex-status to check your quota."
else
  echo "✗ Not logged in."
  echo ""
  echo "Run this in the terminal to authenticate:"
  echo "  ! codex login"
  echo ""
  echo "  OAuth path : opens a device-code URL — visit it and approve."
  echo "  API key    : export OPENAI_API_KEY=sk-... instead."
  echo ""
  echo "Then run /agent-team:codex-login again to confirm."
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
