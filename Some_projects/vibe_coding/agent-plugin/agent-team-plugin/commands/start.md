---
name: start
description: Launch the agent team on a task. Reads team.json, initialises a session, decomposes the task across roles, dispatches ALL agents simultaneously in parallel, collects results, routes inter-agent messages, and synthesises outcomes. Runs as many rounds as needed.
---

# /agent-team:start \<task\>

Deploy your agent team on a task. **All agents fire at the same time.**

**Usage:**
```
/agent-team:start "build the auth module"
/agent-team:start --tmux "build the auth module"
```

The `--tmux` flag opens a tmux session with one pane per agent so the user can watch every agent work in real time. Without it, all output streams into the Claude Code terminal as text.

**Your first output must be:** `🤖 AGENT TEAM ACTIVATED`

## Execution

Follow the `team-coordination` skill exactly. Steps:

### 0. Parse Flags

Strip leading flags from the user's args before treating the rest as the task:

```bash
TMUX_MODE=false
RAW_ARGS="$ARGUMENTS"           # whatever the user passed in

# Detect --tmux flag (must be first token)
if [[ "$RAW_ARGS" =~ ^[[:space:]]*--tmux([[:space:]]+|$) ]]; then
  TMUX_MODE=true
  TASK="$(echo "$RAW_ARGS" | sed -E 's/^[[:space:]]*--tmux[[:space:]]*//')"
else
  TASK="$RAW_ARGS"
fi

if [[ -z "$TASK" ]]; then
  echo "Usage: /agent-team:start [--tmux] \"<task description>\""
  exit 1
fi
```

If `TMUX_MODE=true`, branch to **Step 5b — tmux dispatch** below instead of the default text dispatch.

### 1. Validate

```bash
# Check team.json exists
TEAM_CONFIG=$(bash ${CLAUDE_PLUGIN_ROOT}/scripts/find-team-config.sh 2>/dev/null)
if [[ -z "$TEAM_CONFIG" ]]; then
  echo "No team.json found. Run /agent-team:setup first."
  exit 1
fi

# Check providers
bash ${CLAUDE_PLUGIN_ROOT}/scripts/check-providers.sh
```

### 2. Initialise Session

```bash
SESSION_ID=$(date +%Y%m%d-%H%M%S)
SESSION_DIR=$(bash ${CLAUDE_PLUGIN_ROOT}/scripts/init-session.sh \
  "$SESSION_ID" "$TEAM_CONFIG" "$PWD")
```

### 3. Display Team Banner

Show the full team banner with emojis, session ID, and all agent roles before doing anything else.

### 4. Decompose Task

Read team.json roles. Break the user's task into role-specific subtasks. Be specific — each agent gets concrete instructions with file paths, acceptance criteria, and who to message if blocked.

### 5. Dispatch ALL Agents in Parallel — Round 1

If `TMUX_MODE=false` (default), build a tasks JSON array and fire everyone simultaneously:

```bash
TASKS=$(jq -n \
  --arg fid "frontend" --arg ftask "Your frontend task here..." \
  --arg bid "backend"  --arg btask "Your backend task here..." \
  --arg tid "tester"   --arg ttask "Your tester task here..." \
  '[{"id":$fid,"task":$ftask},{"id":$bid,"task":$btask},{"id":$tid,"task":$ttask}]')

bash ${CLAUDE_PLUGIN_ROOT}/scripts/dispatch-parallel.sh \
  "$SESSION_ID" "1" "$TASKS"
```

For any Claude-powered agents: use the native Agent tool **at the same moment** — do not wait for bash agents to finish first.

Show: `🚀 Round 1 — all agents dispatched in parallel`

### 5b. Dispatch in Tmux Mode (only if `TMUX_MODE=true`)

Skip the parallel-dispatch script and hand off to the tmux launcher. The launcher
creates a tmux session named `agent-team-<session-id>` with one pane per agent and
runs `dispatch-agent.sh` in each non-Claude pane.

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/launch-tmux-session.sh \
  "$SESSION_ID" "$TEAM_CONFIG" "$PWD" "$TASK"
```

Then print the attach command for the user and stop — the user watches progress
live inside tmux. After tmux mode finishes, jump straight to **Step 10** (no need
to collect results in this terminal; they live on disk for the user to inspect).

```
🚀 Tmux session launched — attach with:
   tmux attach -t agent-team-<session-id>
```

### 6. Collect Results

After all agents finish, read every result:

```bash
cat ~/.agent-team/sessions/$SESSION_ID/agents/frontend/results/1-result.md
cat ~/.agent-team/sessions/$SESSION_ID/agents/backend/results/1-result.md
cat ~/.agent-team/sessions/$SESSION_ID/agents/tester/results/1-result.md
```

Display a summary:
```
✅ Frontend Engineer — reviewed 11 components, messaged backend about 3 missing endpoints
✅ Backend Engineer  — all 9 endpoints confirmed complete
✅ QA Engineer       — identified 5 missing E2E tests, wrote 3
✉  2 inter-agent messages routed
```

### 7. Check Coordinator Inbox

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/read-inbox.sh \
  "$SESSION_DIR/coordinator/inbox"
```

### 8. Synthesise

Combine the results. Show:
- What was accomplished this round
- What inter-agent messages were exchanged and what they contained
- What's still remaining

### 9. Decide: Another Round?

If work is incomplete or agents sent messages to each other that need follow-up, start Round 2. Each agent's session persists — they pick up where they left off:
- opencode agents: same session ID auto-resumed in dispatch
- codex/gemini/copilot agents: prior round results injected automatically as context

Repeat until the task is done.

### 10. Session Complete

```
🏁 AGENT TEAM SESSION COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Session: <id>  |  Rounds: <n>  |  Agents: <count>
Results: ~/.agent-team/sessions/<id>/
```

### 11. Save Session Memory

Extract the key learnings from this session and save them to persistent memory so future sessions on similar tasks can benefit.

Write a concise memory document with these sections, then pipe it to `save-memory.sh`:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/save-memory.sh \
  "$SESSION_ID" "$TASK" <<'MEMORY_EOF'
## What Was Accomplished
- <bullet: what each agent did and completed>

## Key Decisions
- <decision made and why — e.g. "Used X approach because Y constraint">

## Patterns That Worked
- <approaches, file structures, commands that succeeded>

## Issues Encountered
- <blockers, errors, workarounds applied>

## Files Changed
- <list of files created or modified>
MEMORY_EOF
```

After saving, show:
```
🧠 Session memory saved — searchable via /agent-team:memory
```
