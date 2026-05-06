# Agent Team Plugin

A Claude Code plugin that orchestrates a team of AI agents — Codex, OpenCode, Gemini, and Claude — working in parallel on engineering tasks. Each agent gets its own context, receives inter-agent messages, and writes results to a shared session directory. A coordinator (Claude) decomposes tasks, reads results, routes messages, and synthesises the outcome.

---

## Quick Start

```
/agent-team:setup          → create team.json for your project
/agent-team:agents         → check who is ready (auth, model, quota)
/agent-team:start "task"   → deploy the team
/agent-team:session        → check progress
/agent-team:recall         → search past session learnings
```

---

## All Commands

> All commands are namespaced `/agent-team:<name>`. None conflict with Claude Code built-ins.

### Coordination

| Command | Tokens | What it does |
|---|---|---|
| `/agent-team:start <task>` | Claude | Decomposes task, dispatches all agents in parallel, collects results, routes messages, repeats until done. Accepts `--tmux` flag to watch each agent in a split terminal. |
| `/agent-team:session` | Claude | Shows the active session: agent status table (idle/working/done), round number, unread inbox count, result excerpts, and pending inter-agent messages. |
| `/agent-team:message <agent-id> <text>` | Claude | Sends a message directly into a specific agent's inbox mid-session. |
| `/agent-team:setup` | Claude | Interactive wizard that creates `team.json` for the current project. Asks for role names, models, and context directories. |
| `/agent-team:agents` | Claude | Master overview table showing every agent, their model, auth state, and model selection. |
| `/agent-team:recall [keyword]` | **Zero** | Browse or keyword-search cross-session memories saved from past runs. |

### Codex Management

| Command | Tokens | What it does |
|---|---|---|
| `/agent-team:codex-login` | **Zero** | Checks auth state. If logged in, confirms. If not, prints `! codex login` instructions. |
| `/agent-team:codex-status` | **Zero** | Shows auth method, active model, Codex roles, and daily quota state (probes the API). |
| `/agent-team:codex-model [model] [role\|all]` | **Zero** | With no args: lists available models and current selection. With args: writes `codex_model` to `team.local.json` instantly. Models: `o4-mini` `o3` `o3-mini` `codex-mini`. |

### OpenCode Management

| Command | Tokens | What it does |
|---|---|---|
| `/agent-team:opencode-login` | **Zero** | Checks auth state. Prints `! opencode auth login` instructions if not authenticated. |
| `/agent-team:opencode-status` | **Zero** | Shows version, auth provider, active model, and which roles use OpenCode. |
| `/agent-team:opencode-model [model] [role\|all]` | **Zero** | With no args: lists available models. With args: writes `opencode_model` to `team.local.json`. Models: `github-copilot/claude-sonnet-4.5` `github-copilot/gpt-4.1` `github-copilot/o3` `github-copilot/gemini-2.5-pro`. |

### Gemini Management

| Command | Tokens | What it does |
|---|---|---|
| `/agent-team:gemini-login` | **Zero** | Checks auth state. Prints `! gemini auth` instructions if not authenticated. |
| `/agent-team:gemini-status` | **Zero** | Shows version, Google account (if detectable), active model, and which roles use Gemini. |
| `/agent-team:gemini-model [model] [role\|all]` | **Zero** | With no args: lists available models. With args: writes `gemini_model` to `team.local.json`. Models: `gemini-2.5-pro` `gemini-2.5-flash` `gemini-2.0-flash`. |

---

## Skills

Skills are loaded automatically when you run commands. You can also invoke them directly with `/agent-team:<skill-name>`.

| Skill | When it activates |
|---|---|
| `agent-team:team-coordination` | When the coordinator assembles and runs a session |
| `agent-team:agent-dispatch` | When a single agent is dispatched with context + inbox |
| `agent-team:context-loading` | When an agent's file-tree context is built |

---

## Configuration Files

### `team.json` (committed)

Defines your team. Lives in the project root. Created by `/agent-team:setup`.

```json
{
  "version": "1.0",
  "name": "My Dev Team",
  "roles": [
    {
      "id": "frontend-engineer",
      "name": "Frontend Engineer",
      "model": "codex",
      "context_dirs": ["frontend/", "planning/"],
      "expertise": "React, Next.js, TypeScript, Tailwind CSS"
    },
    {
      "id": "backend-engineer",
      "name": "Backend Engineer",
      "model": "opencode",
      "context_dirs": ["backend/", "planning/"],
      "expertise": "FastAPI, Python, SQLite"
    }
  ]
}
```

**`model` values:** `codex` · `opencode` · `gemini` · `copilot` · `claude`

### `team.local.json` (gitignored)

Per-machine model overrides. Written by the `*-model` commands. Never commit this.

```json
{
  "roles": [
    { "id": "frontend-engineer", "codex_model": "o4-mini" },
    { "id": "backend-engineer",  "opencode_model": "github-copilot/claude-sonnet-4.5" }
  ]
}
```

Fields: `codex_model` · `opencode_model` · `gemini_model`

---

## Memory System

After every `/agent-team:start` session the coordinator saves a structured learning file. Future sessions on similar tasks automatically receive the top-3 most relevant past memories in each agent's prompt.

```
~/.agent-team/memory/
└── YYYYMMDD-HHMMSS-<task-slug>.md   (one file per session)
```

Each file stores:
- What was accomplished
- Key decisions and why
- Patterns that worked
- Issues encountered
- Files changed

**Search:** `/agent-team:recall <keyword>` — zero Claude tokens, grep-scored relevance ranking.

**Manual save:**
```bash
bash plugins/agent-team/scripts/save-memory.sh <session-id> "task" <<'EOF'
## Key Decisions
- Used X because Y
EOF
```

---

## Session Directory Structure

Every `/agent-team:start` creates a session under `~/.agent-team/sessions/`:

```
~/.agent-team/sessions/<session-id>/
├── session.json                     ← session metadata (status, round, project root)
├── team.json                        ← snapshot of merged team config for this run
├── coordinator/
│   ├── inbox/                       ← messages addressed to the coordinator
│   └── rounds/
│       └── 1-dispatch.log           ← parallel dispatch log per round
└── agents/
    └── <agent-id>/
        ├── profile.json             ← model, status, last_round, expertise, session IDs
        ├── inbox/
        │   └── <msg-id>.json        ← messages from teammates
        └── results/
            └── 1-result.md          ← agent output per round
```

### Multi-Round Session Continuity

How each model type remembers prior rounds:

| Model | Strategy |
|---|---|
| **opencode** | Native session resume — `opencode run -s <session-id>` continues the exact same session. Session ID is stored in `profile.json` after Round 1. Full memory, no prompt overhead. |
| **gemini** | Context injection — all previous `*.md` result files are prepended to the prompt as `## Your Prior Work`. Stateless CLI, so prior work is re-sent each round. |
| **codex** | Context injection — same approach as Gemini. |
| **claude** | Invoked by coordinator via native `Agent` tool — coordinator manages continuity. |

---

## Tmux Mode

Run all agents in visible split panes:

```
/agent-team:start --tmux "build the auth module"
```

Opens a tmux session named `agent-team-<session-id>` with one pane per agent. Attach with:

```bash
tmux attach -t agent-team-<session-id>
```

---

## Inter-Agent Messaging

Agents communicate by including lines in their output:

```
MESSAGE TO backend-engineer: I need /api/prices to return 24h high/low.
MESSAGE TO coordinator: Done. Created 3 components. Blocked on API contract.
```

The dispatcher parses these after each result and writes JSON messages to the recipient's inbox. The coordinator routes messages to Claude agents. Messages persist across rounds.

**MCP doc fetch** — agents can request external docs:
```
MESSAGE TO coordinator: FETCH DOCS recharts treemap-component
```
The coordinator fetches the docs and injects them in the agent's next-round inbox.

---

## Conflict-Free Command Reference

All commands are under the `agent-team:` namespace. The following names were intentionally **avoided** to prevent shadowing Claude Code built-ins:

| Avoided name | Reason | Our name instead |
|---|---|---|
| `status` | Shadows Claude `/status` fuzzy match | `session` |
| `memory` | Conflicts with Claude `/memory` built-in | `recall` |

Claude Code built-ins that remain unaffected:
`/help` · `/clear` · `/compact` · `/config` · `/cost` · `/doctor` · `/exit` · `/memory` · `/model` · `/mcp` · `/permissions` · `/reload-plugins` · `/init` · `/login`

---

## Token Cost Summary

| Operation | Claude tokens |
|---|---|
| Login / status / model checks (9 commands) | **0** — `disable-model-invocation: true` |
| `/agent-team:recall` search | **0** — shell script |
| `/agent-team:session` | ~500 — reads files, formats table |
| `/agent-team:start` (per round) | ~2k coordinator + agent prompt × N agents |
| Post-session memory save | ~300 — coordinator writes summary |

---

## Auto-Sync Hook

Plugin source edits sync to the Claude Code cache automatically on every `git commit`:

```bash
# Install once:
bash plugins/agent-team/scripts/install-hook.sh
```

The post-commit hook runs `rsync` from `plugins/agent-team/` → `~/.claude/plugins/cache/`.
After structural changes (new commands, scripts), run `/reload-plugins` to pick them up.
