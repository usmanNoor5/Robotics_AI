#!/bin/bash
# Read all unread messages from an agent's inbox.
# Marks them as read and prints formatted context block.
# Usage: read-inbox.sh <inbox-dir>
# Output: markdown-formatted messages (stdout), empty string if none

INBOX_DIR="${1:?inbox directory required}"

[[ -d "$INBOX_DIR" ]] || exit 0

# Collect unread messages sorted by timestamp
MESSAGES=$(find "$INBOX_DIR" -name "*.json" -type f | sort)

if [[ -z "$MESSAGES" ]]; then
  echo ""
  exit 0
fi

HAS_UNREAD=false

while IFS= read -r MSG_FILE; do
  [[ -f "$MSG_FILE" ]] || continue
  READ=$(jq -r '.read' "$MSG_FILE" 2>/dev/null)
  [[ "$READ" == "true" ]] && continue

  FROM=$(jq -r '.from' "$MSG_FILE")
  TIMESTAMP=$(jq -r '.timestamp' "$MSG_FILE")
  CONTENT=$(jq -r '.content' "$MSG_FILE")

  if ! $HAS_UNREAD; then
    echo "## Messages from Teammates"
    echo ""
    HAS_UNREAD=true
  fi

  echo "**From: ${FROM}** _(${TIMESTAMP})_"
  echo ""
  echo "$CONTENT"
  echo ""
  echo "---"
  echo ""

  # Mark as read
  TMP=$(mktemp)
  jq '.read = true' "$MSG_FILE" > "$TMP" && mv "$TMP" "$MSG_FILE"
done <<< "$MESSAGES"
