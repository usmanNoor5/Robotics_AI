#!/usr/bin/env bash
# Save a memory entry to ~/.agent-team/memory/
# Usage: save-memory.sh <session-id> <task> [content-file]
#        save-memory.sh <session-id> <task>             (reads content from stdin)

MEMORY_DIR="${HOME}/.agent-team/memory"
mkdir -p "$MEMORY_DIR"

SESSION_ID="${1:?Usage: save-memory.sh <session-id> <task> [content-file]}"
TASK="${2:?task required}"
CONTENT_FILE="${3:-}"

if [[ -n "$CONTENT_FILE" ]]; then
  [[ -f "$CONTENT_FILE" ]] || { echo "File not found: $CONTENT_FILE" >&2; exit 1; }
  CONTENT=$(cat "$CONTENT_FILE")
else
  CONTENT=$(cat)
fi

DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
SLUG=$(echo "$TASK" \
  | tr '[:upper:]' '[:lower:]' \
  | sed 's/[^a-z0-9]/-/g' \
  | tr -s '-' \
  | cut -c1-40 \
  | sed 's/-$//')

MEMORY_FILE="${MEMORY_DIR}/${TIMESTAMP}-${SLUG}.md"

{
  echo "---"
  echo "date: $DATE"
  echo "session: $SESSION_ID"
  echo "task: $TASK"
  echo "---"
  echo ""
  echo "$CONTENT"
} > "$MEMORY_FILE"

echo "$MEMORY_FILE"
