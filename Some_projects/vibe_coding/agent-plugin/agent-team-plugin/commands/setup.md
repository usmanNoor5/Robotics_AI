---
name: setup
description: Interactive wizard to create a team.json for this project. Detects available model providers, asks the user to define roles, assign models, and set context directories. Writes team.json to the project root.
---

# /agent-team:setup

Run the interactive team setup wizard. Creates a `team.json` in the current project.

**Your first output must be:** `🤖 Agent Team Setup`

## Step 1 — Detect Providers

Run provider detection first:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/check-providers.sh
```

Show the results clearly. Note which models are available so the user knows what they can assign.

## Step 2 — Ask for Team Definition

Ask the user (conversationally, not as a form):

1. **Team name** — what do they want to call this team?
2. **Roles** — what engineering roles do they need? (e.g. Frontend Engineer, Backend Engineer, QA, DevOps)
3. For each role:
   - Which model should power it? (only offer available ones + claude which is always available)
   - Which directories does this agent need to see? (e.g. `frontend/`, `backend/`, `test/`)
   - What is this agent's expertise? (short phrase, e.g. "React, TypeScript, CSS")

If the user isn't sure, suggest sensible defaults based on the project structure you can see.

## Step 3 — Detect Project Structure

```bash
ls -la
find . -maxdepth 2 -type d | grep -v node_modules | grep -v .git | head -30
```

Use this to suggest relevant context directories for each role.

## Step 4 — Write team.json

Write `team.json` to the project root with this structure:

```json
{
  "version": "1.0",
  "name": "<team name>",
  "roles": [
    {
      "id": "<kebab-case-id>",
      "name": "<Role Name>",
      "model": "<codex|copilot|gemini|claude>",
      "context_dirs": ["<dir1>/", "<dir2>/"],
      "expertise": "<short expertise phrase>"
    }
  ]
}
```

## Step 5 — Confirm

Show the final team.json to the user and confirm it was written.

Then tell them:

```text
✅ Team configured. Run /agent-team:start "<your task>" to deploy your team.
```
