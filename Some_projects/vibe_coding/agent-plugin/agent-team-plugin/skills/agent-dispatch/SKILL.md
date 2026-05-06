---
name: agent-dispatch
description: Activate when dispatching a specific agent to do work — loading their context, building their prompt, calling their model, and routing their output messages back into the team.
version: 1.0.0
---

# Agent Dispatch

This skill governs the mechanics of invoking a single agent — from context loading through to result collection and message routing.

## Dispatch Flow

```
1. Read agent profile      → model, role, expertise, context_dirs
2. Load directory context  → compressed snapshot of their codebase area
3. Read inbox             → unread messages from teammates
4. Build prompt            → identity + context + inbox + task
5. Call model CLI          → codex / copilot / gemini / claude Agent tool
6. Collect result          → written to results/<round>-result.md
7. Parse messages          → route any MESSAGE TO <id>: lines
8. Update status           → agent profile status field
```

## Prompt Structure (for all models)

Every agent receives a prompt with these sections in order:

1. **Identity** — who they are, their expertise
2. **Project Briefing** — first ~50 lines of `planning/PLAN.md` (if present) plus the project root path, so the agent knows where to look
3. **Mission — Round N** — the role-specific task, including what DONE looks like
4. **Team** — teammate roster (so the agent knows who to message)
5. **File Tree — Your Context** — output of `load-context.sh`: tree per context dir + "Key Files — Read These First" list (no file contents inlined)
6. **Messages from Teammates** — unread inbox messages from prior rounds
7. **MCP Tool Requests** — protocol for asking the coordinator to fetch external docs (`MESSAGE TO coordinator: FETCH DOCS <library> <topic>`)
8. **Communication Format** — `MESSAGE TO <id>: ...` syntax
9. **Instructions** — read key files first, write complete files, summarise at end

## Model-Specific Behaviours

### Codex (`codex exec --dangerously-bypass-approvals-and-sandbox`)
- Has a full agentic loop — it will read, write, and run code autonomously
- Best for: implementation tasks, refactoring, writing complete files
- Output: mix of prose explanation and actual code changes it made
- Context: pass the working directory as project root so it can edit files directly
- Flag note: prior versions used `--full-auto`; the current CLI uses `--dangerously-bypass-approvals-and-sandbox` for the same effect

### Copilot (`copilot -p --no-ask-user`)
- One-shot generation with the user's GitHub subscription
- Best for: code generation, boilerplate, documentation, architecture suggestions
- Output: code and explanations — coordinator applies changes if needed
- Context: inline the relevant file contents in the prompt

### Gemini (`gemini -p --approval-mode yolo`)
- Strong analysis, long-context understanding (2M token window)
- Best for: code review, test generation, research, cross-cutting analysis
- Output: detailed analysis and recommendations
- Context: can handle large codebases; inline generously

### Claude (native Agent tool)
- Full Claude Code tool access — Read, Edit, Write, Bash
- Best for: complex multi-file changes, tasks requiring iterative tool use
- Invoked via: the native Agent tool from the coordinator
- Output: structured tool use results, files are changed directly

## Context Loading

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/load-context.sh \
  "$PROJECT_ROOT" "$CONTEXT_DIRS_JSON"
```

Lightweight orientation only — see the `context-loading` skill for full details:
- Shows the file tree per context directory (sorted, up to 80 lines per dir)
- Lists up to 10 "key files" per dir (configs, entry points, top-level docs)
- **No file contents are inlined** — agents read files themselves with native tools
- Skipped paths: `node_modules/`, `.git/`, `__pycache__/`, `dist/`, `.next/`, `build/`, `.venv/`, `venv/`, `.cache/`, `coverage/`

The dispatcher additionally injects the first 50 lines of `planning/PLAN.md` (if present) as a Project Briefing so agents know what the project is before they read anything.

## Message Parsing

After receiving an agent's result, the dispatch script automatically scans for:

```
MESSAGE TO <agent-id>: <content>
```

These are parsed and written to the target agent's inbox as JSON messages. The coordinator's inbox is also checked for messages addressed to `coordinator`.

**Valid target IDs:** any role id from team.json, or `coordinator`

## Result Format

Results are saved as markdown:
```
~/.agent-team/sessions/<session-id>/agents/<agent-id>/results/<round>-result.md
```

The coordinator reads these after all agents finish their round.
