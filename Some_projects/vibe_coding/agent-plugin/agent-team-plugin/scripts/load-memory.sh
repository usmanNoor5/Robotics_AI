#!/usr/bin/env bash
# Load top-N relevant memory files for a given task description.
# Uses keyword frequency scoring — no vector DB required.
# Usage: load-memory.sh <task-description> [max-results=3]
# Outputs combined markdown ready to inject into an agent prompt.

MEMORY_DIR="${HOME}/.agent-team/memory"
TASK="${1:-}"
MAX="${2:-3}"

[[ -z "$TASK" ]] && exit 0
[[ -d "$MEMORY_DIR" ]] || exit 0
[[ -n "$(ls -A "$MEMORY_DIR" 2>/dev/null)" ]] || exit 0

# Extract keywords: words ≥4 chars, unique, lowercased
KEYWORDS=$(echo "$TASK" \
  | tr '[:upper:]' '[:lower:]' \
  | grep -oE '[a-z]{4,}' \
  | sort -u \
  | tr '\n' '|' \
  | sed 's/|$//')

[[ -z "$KEYWORDS" ]] && exit 0

# Score each memory file by total keyword match count, take top N
TOP_FILES=$(for MFILE in "$MEMORY_DIR"/*.md; do
  [[ -f "$MFILE" ]] || continue
  SCORE=$(grep -ciE "$KEYWORDS" "$MFILE" 2>/dev/null || echo 0)
  echo "$SCORE $MFILE"
done | sort -rn | awk '$1 > 0 { print $2 }' | head -"$MAX")

[[ -z "$TOP_FILES" ]] && exit 0

COUNT=0
while IFS= read -r MFILE; do
  [[ -f "$MFILE" ]] || continue
  COUNT=$((COUNT + 1))
  MDATE=$(grep '^date:' "$MFILE" 2>/dev/null | head -1 | sed 's/date: //')
  MTASK=$(grep '^task:' "$MFILE" 2>/dev/null | head -1 | sed 's/task: //')
  echo "### Memory $COUNT — $MTASK ($MDATE)"
  echo ""
  # Strip YAML frontmatter (between first and second --- delimiters)
  awk 'BEGIN{f=0} /^---$/ && f<2{f++; next} f>=2{print}' "$MFILE"
  echo ""
done <<< "$TOP_FILES"
