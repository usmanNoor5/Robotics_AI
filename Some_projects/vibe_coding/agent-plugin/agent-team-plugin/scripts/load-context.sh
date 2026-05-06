#!/bin/bash
# Build a lightweight orientation block for an agent.
# Emits a file tree per context dir + a "Key Files — Read These First" list.
# File contents are NOT inlined — agents read files themselves with their own tools.
#
# Usage: load-context.sh <project-root> <context-dirs-json-array>
# Output: markdown-formatted context block (stdout)

set -euo pipefail

PROJECT_ROOT="${1:?project root required}"
CONTEXT_DIRS_JSON="${2:?context dirs JSON array required}"  # e.g. '["frontend/","backend/"]'

MAX_KEY_FILES=10        # max files surfaced as "read these first"
MAX_TREE_LINES=80       # truncate the file tree per dir

# ── Skip patterns ──────────────────────────────────────────────────────────
SKIP_FIND_ARGS=(
  -not \( -path "*/node_modules/*"
       -o -path "*/.git/*"
       -o -path "*/__pycache__/*"
       -o -path "*/dist/*"
       -o -path "*/.next/*"
       -o -path "*/build/*"
       -o -path "*/.venv/*"
       -o -path "*/venv/*"
       -o -path "*/.cache/*"
       -o -path "*/coverage/*"
       \)
)

# ── Heuristic: is this file likely to be a "key" orientation file? ─────────
# Returns 0 (true) if the file matches one of:
#  - common config files at the dir root
#  - common entry-point files
#  - top-level README or PLAN files
is_key_file() {
  local rel="$1"      # path relative to the context dir
  local base
  base=$(basename "$rel")

  case "$base" in
    package.json|pyproject.toml|tsconfig.json|next.config.ts|next.config.mjs|next.config.js)
      return 0 ;;
    tailwind.config.ts|tailwind.config.js|postcss.config.mjs)
      return 0 ;;
    Dockerfile|docker-compose.yml|docker-compose.yaml)
      return 0 ;;
    main.py|app.py|index.ts|index.tsx|index.js|server.py|__main__.py)
      return 0 ;;
    page.tsx|layout.tsx)
      return 0 ;;
    README.md|README|PLAN.md|ARCHITECTURE.md|CLAUDE.md)
      return 0 ;;
    schema.sql|schema.prisma)
      return 0 ;;
  esac

  return 1
}

# ── Render ─────────────────────────────────────────────────────────────────
DIRS=$(echo "$CONTEXT_DIRS_JSON" | jq -r '.[]' 2>/dev/null)

echo "## Project Context"
echo ""
echo "_File tree below shows what exists in your context directories. Use your"
echo "file-reading tools to open any file you need — content is not inlined here._"
echo ""

for RELDIR in $DIRS; do
  ABSDIR="${PROJECT_ROOT}/${RELDIR%/}"

  if [[ ! -d "$ABSDIR" ]]; then
    echo "### \`${RELDIR}\` — directory not found"
    echo ""
    continue
  fi

  echo "### \`${RELDIR}\`"
  echo ""
  echo '```'
  find "$ABSDIR" "${SKIP_FIND_ARGS[@]}" -type f \
    | sort \
    | sed "s|${ABSDIR}/||" \
    | head -n "$MAX_TREE_LINES"
  echo '```'
  echo ""

  # ── Key files heuristic ──────────────────────────────────────────────
  KEY_FILES=()
  while IFS= read -r FPATH; do
    [[ ${#KEY_FILES[@]} -ge $MAX_KEY_FILES ]] && break
    REL="${FPATH#$ABSDIR/}"
    if is_key_file "$REL"; then
      KEY_FILES+=("${RELDIR%/}/${REL}")
    fi
  done < <(find "$ABSDIR" "${SKIP_FIND_ARGS[@]}" -type f | sort)

  if [[ ${#KEY_FILES[@]} -gt 0 ]]; then
    echo "## Key Files — Read These First (${RELDIR%/})"
    echo ""
    for KF in "${KEY_FILES[@]}"; do
      echo "- \`${KF}\`"
    done
    echo ""
  fi
done
