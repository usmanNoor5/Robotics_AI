---
name: context-loading
description: Activate when an agent prompt is being assembled and you need to understand how directory context, file trees, and key-file hints are produced. Governs the lightweight orientation block that ships in every agent prompt.
version: 1.0.0
---

# Context Loading

This skill describes how `scripts/load-context.sh` builds the orientation block
that goes into every agent prompt. The design favours **awareness over volume**:
agents see what exists and which files matter, then read those files themselves
with their own tools.

## Philosophy

Earlier versions of the dispatcher inlined up to 30 files × 4KB each into every
agent prompt — ~120KB of noise. Agents skimmed it, missed details, and used the
context window for indexing instead of thinking. The new approach:

- Show the file tree (orientation)
- Surface a short list of "key files" (priorities)
- Let the agent read the files itself with its native tools

This trades a heavier first read step for vastly better signal-to-noise across
the rest of the round.

## What the Script Emits

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/load-context.sh \
  "$PROJECT_ROOT" "$CONTEXT_DIRS_JSON"
```

Output structure:

```
## Project Context

_<one-line note explaining tree-only mode>_

### `frontend/`
```
<file tree, up to 80 lines, sorted>
```

## Key Files — Read These First (frontend)

- `frontend/package.json`
- `frontend/next.config.ts`
- `frontend/app/page.tsx`
- ...
```

## File Tree

- Recurses through each directory in the agent's `context_dirs`
- Sorted alphabetically for deterministic output
- Truncated to 80 lines per directory (enough for orientation, not for indexing)
- **Skipped paths:** `node_modules/`, `.git/`, `__pycache__/`, `dist/`, `.next/`,
  `build/`, `.venv/`, `venv/`, `.cache/`, `coverage/`

## Key Files Heuristic

A file is flagged as "read first" if its basename matches one of these
orientation-class names:

| Category | Examples |
|---|---|
| Build/manifest | `package.json`, `pyproject.toml`, `tsconfig.json`, `next.config.*`, `tailwind.config.*`, `postcss.config.mjs` |
| Container | `Dockerfile`, `docker-compose.yml` |
| Entry points | `main.py`, `app.py`, `index.ts(x)`, `index.js`, `server.py`, `__main__.py` |
| Framework entries | `page.tsx`, `layout.tsx` |
| Docs | `README.md`, `PLAN.md`, `ARCHITECTURE.md`, `CLAUDE.md` |
| Schema | `schema.sql`, `schema.prisma` |

Up to 10 key files surface per directory. The agent reads them itself before
writing any code — that's part of the dispatcher's instructions in the prompt.

## When to Inline a File (Exception)

The default is **never inline**. The narrow exception: if a file is shorter than
~20 lines AND it's load-bearing for the task, the coordinator may quote it
inline in the agent's mission brief (the `${TASK}` portion of the prompt).
`load-context.sh` itself never does this — it's the coordinator's call.

## Why the Coordinator Still Adds a Project Briefing

`dispatch-agent.sh` reads the first 50 lines of `planning/PLAN.md` (if present)
and embeds them above the file tree. The PLAN file is the closest thing to a
project-wide spec, so it's worth always being in the prompt — but only the head
of it. Agents read the rest themselves on demand.
