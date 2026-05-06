---
name: opencode-model
description: Set the OpenCode model for opencode-powered roles. With no args: shows available models and asks which to select. With args: writes to team.local.json instantly.
argument-hint: '[model] [role-id|all]'
allowed-tools: Bash(bash:*)
---

# /agent-team:opencode-model

Set the OpenCode model written to `team.local.json`.

## If arguments were provided

Run directly — no interaction needed:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cmd-opencode-model.sh" $ARGUMENTS
```

## If no arguments were provided

### Step 1 — Show current state

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cmd-opencode-model.sh"
```

### Step 2 — Present the model list

Show the available models as a numbered list and ask the user to pick one:

```
Available OpenCode models:
 1. github-copilot/claude-sonnet-4.5   — recommended
 2. github-copilot/claude-opus-4.5
 3. github-copilot/claude-haiku-4.5
 4. github-copilot/claude-sonnet-4
 5. github-copilot/gpt-5.4-mini
 6. github-copilot/gpt-5.3-codex
 7. github-copilot/gpt-5.2-codex
 8. github-copilot/gpt-5.2
 9. github-copilot/gpt-5-mini
10. github-copilot/gpt-4.1
11. github-copilot/gpt-4o
12. github-copilot/gemini-3.1-pro-preview
13. github-copilot/gemini-3-flash-preview
14. github-copilot/gemini-2.5-pro
15. github-copilot/grok-code-fast-1

Which model? (enter number or name)
```

### Step 3 — Ask which roles to apply to

Once the user picks a model, ask:

```
Apply to: all roles / specific role?
(opencode roles: backend-engineer, qa-engineer, db-engineer)
```

### Step 4 — Write the selection

Run the script with the chosen model and role:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cmd-opencode-model.sh" "<chosen-model>" "<all|role-id>"
```
