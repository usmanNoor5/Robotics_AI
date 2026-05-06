#!/usr/bin/env bash
# Check OpenCode auth state and print instructions if not authenticated. Zero Claude tokens.
echo "⚫ OpenCode Login"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

OC_BIN=""
if [[ -x "$HOME/.opencode/bin/opencode" ]]; then
  OC_BIN="$HOME/.opencode/bin/opencode"
elif command -v opencode &>/dev/null; then
  OC_BIN="$(command -v opencode)"
fi

if [[ -z "$OC_BIN" ]]; then
  echo "❌ opencode CLI not installed."
  echo "   Run: curl -fsSL https://opencode.ai/install | bash"
  exit 1
fi

VERSION=$("$OC_BIN" --version 2>/dev/null || echo "unknown")
echo "Found: $OC_BIN (v$VERSION)"
echo ""

AUTH_OUT=$("$OC_BIN" auth list 2>&1 || true)
if echo "$AUTH_OUT" | grep -qiE 'github.copilot|GitHub Copilot|anthropic|openrouter|credentials'; then
  PROVIDER=$(echo "$AUTH_OUT" | grep -oiE 'GitHub Copilot|Anthropic|OpenRouter' | head -1)
  echo "✓ Already authenticated — provider: ${PROVIDER:-authenticated}"
  echo ""
  echo "Tip: /agent-team:opencode-model to set the active model."
else
  echo "✗ Not authenticated."
  echo ""
  echo "Run this in the terminal to authenticate:"
  echo "  ! $OC_BIN auth login"
  echo ""
  echo "  Pick 'github-copilot' from the provider list."
  echo "  Follow the device-code URL, sign in to GitHub, approve access."
  echo ""
  echo "Then run /agent-team:opencode-login again to confirm."
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
