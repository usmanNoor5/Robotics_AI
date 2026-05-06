---
name: gemini-model
description: Set the Gemini model for gemini-powered roles. With no args: shows available models and asks which to select. With args: writes to team.local.json instantly.
argument-hint: '[model] [role-id|all]'
allowed-tools: Bash(bash:*)
---

# /agent-team:gemini-model

Set the Gemini model written to `team.local.json`.

## If arguments were provided

Run directly — no interaction needed:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cmd-gemini-model.sh" $ARGUMENTS
```

## If no arguments were provided

### Step 1 — Show current state

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cmd-gemini-model.sh"
```

### Step 2 — Present the model list

Show the available models as a numbered list and ask the user to pick one:

```
Available Gemini models:
 1. gemini-3.1-pro              — most capable Gemini 3 (recommended)
 2. gemini-3-pro
 3. gemini-3-flash              — fast Gemini 3
 4. gemini-3.1-flash-lite-preview
 5. gemini-3-flash-preview
 6. gemini-3-pro-preview
 7. gemini-2.5-pro              — most capable Gemini 2.5, 2M context
 8. gemini-2.5-flash
 9. gemini-2.5-flash-lite
10. gemini-2.0-flash
11. gemini-1.5-pro
12. gemini-1.5-flash

Which model? (enter number or name)
```

### Step 3 — Ask which roles to apply to

Once the user picks a model, ask:

```
Apply to: all roles / specific role?
(gemini roles: frontend-engineer, devops-engineer)
```

### Step 4 — Write the selection

Run the script with the chosen model and role:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cmd-gemini-model.sh" "<chosen-model>" "<all|role-id>"
```
