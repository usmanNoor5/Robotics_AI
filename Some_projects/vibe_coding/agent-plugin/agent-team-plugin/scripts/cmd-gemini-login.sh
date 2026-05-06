#!/usr/bin/env bash
# Check Gemini auth state and print instructions if not authenticated. Zero Claude tokens.
echo "🟡 Gemini Login"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v gemini &>/dev/null; then
  echo "❌ gemini CLI not installed."
  echo "   Run: npm install -g @google/gemini-cli"
  exit 1
fi

VERSION=$(gemini --version 2>/dev/null || echo "unknown")
echo "Found: gemini v$VERSION"
echo ""

AUTH_FOUND=false
ACCOUNT=""
for D in "$HOME/.gemini" "$HOME/.config/google-gemini" "$HOME/.config/gemini"; do
  if [[ -d "$D" ]]; then
    AUTH_FOUND=true
    ACCOUNT=$(grep -hoE '"email"[[:space:]]*:[[:space:]]*"[^"]+"' "$D"/*.json 2>/dev/null \
              | head -1 | sed -E 's/.*"([^"]+)"$/\1/' || true)
    break
  fi
done

if $AUTH_FOUND; then
  echo "✓ Already authenticated${ACCOUNT:+ — $ACCOUNT}"
  echo ""
  echo "Tip: /agent-team:gemini-model to set the active model."
else
  echo "✗ Not authenticated."
  echo ""
  echo "Run this in the terminal to authenticate:"
  echo "  ! gemini auth"
  echo ""
  echo "  If 'auth' subcommand is unavailable, use: ! gemini"
  echo "  Follow the Google OAuth URL, sign in, approve access."
  echo ""
  echo "Then run /agent-team:gemini-login again to confirm."
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
