#!/usr/bin/env bash
# View and search agent-team cross-session memories. Zero Claude tokens.
# Usage: cmd-memory.sh [keyword...]

MEMORY_DIR="${HOME}/.agent-team/memory"
QUERY="${*:-}"

echo "🧠 Agent Team Memory"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ ! -d "$MEMORY_DIR" ]] || [[ -z "$(ls -A "$MEMORY_DIR" 2>/dev/null)" ]]; then
  echo "No memories yet."
  echo ""
  echo "Memories are auto-saved after each /agent-team:start session completes."
  echo "Store: $MEMORY_DIR"
  exit 0
fi

TOTAL=$(ls "$MEMORY_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
echo "Total memories : $TOTAL"
echo "Store          : $MEMORY_DIR"
echo ""

if [[ -z "$QUERY" ]]; then
  echo "Recent sessions (newest first):"
  echo ""
  IDX=0
  while IFS= read -r MFILE; do
    [[ -f "$MFILE" ]] || continue
    IDX=$((IDX + 1))
    MDATE=$(grep '^date:'    "$MFILE" 2>/dev/null | head -1 | sed 's/date: //')
    MTASK=$(grep '^task:'    "$MFILE" 2>/dev/null | head -1 | sed 's/task: //')
    MSESS=$(grep '^session:' "$MFILE" 2>/dev/null | head -1 | sed 's/session: //')
    printf "  %2d. [%s] %s\n" "$IDX" "$MDATE" "$MTASK"
    printf "       session: %s\n" "$MSESS"
  done < <(ls -t "$MEMORY_DIR"/*.md 2>/dev/null | head -15)
  echo ""
  echo "Tip: /agent-team:recall <keyword>  — search memories"
else
  echo "Search: \"$QUERY\""
  echo ""
  FOUND=0
  while IFS= read -r MFILE; do
    [[ -f "$MFILE" ]] || continue
    if grep -qi "$QUERY" "$MFILE" 2>/dev/null; then
      FOUND=$((FOUND + 1))
      MDATE=$(grep '^date:' "$MFILE" 2>/dev/null | head -1 | sed 's/date: //')
      MTASK=$(grep '^task:' "$MFILE" 2>/dev/null | head -1 | sed 's/task: //')
      echo "[$MDATE] $MTASK"
      echo "  file: $(basename "$MFILE")"
      # Show up to 3 matching lines (skip frontmatter)
      grep -i "$QUERY" "$MFILE" 2>/dev/null \
        | grep -v '^---\|^date:\|^task:\|^session:' \
        | head -3 \
        | sed 's/^/  > /'
      echo ""
    fi
  done < <(ls -t "$MEMORY_DIR"/*.md 2>/dev/null)

  if [[ $FOUND -eq 0 ]]; then
    echo "No memories found matching \"$QUERY\"."
  else
    echo "Found $FOUND matching memory file(s)."
  fi
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
