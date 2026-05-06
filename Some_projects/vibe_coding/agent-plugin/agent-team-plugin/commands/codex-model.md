---
name: codex-model
description: Set the Codex model for codex-powered roles. With no args: shows available models and asks which to select. With args: writes to team.local.json instantly.
argument-hint: '[model] [role-id|all]'
allowed-tools: Bash(bash:*)
---

# /agent-team:codex-model

Set the Codex model written to `team.local.json`.

## If arguments were provided

Run directly — no interaction needed:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cmd-codex-model.sh" $ARGUMENTS
```

## If no arguments were provided

### Step 1 — Show current state

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cmd-codex-model.sh"
```

### Step 2 — Present the model list

Show the available models as a numbered list and ask the user to pick one:

```
Available Codex models:
1. gpt-5.5           — frontier, most capable
2. gpt-5.4
3. gpt-5.4-mini      — fast and efficient
4. gpt-5.3-codex
5. gpt-5.2
6. codex-auto-review — code review specialised

Which model? (enter number or name)
```

### Step 3 — Ask which roles to apply to

Once the user picks a model, ask:

```
Apply to: all roles / specific role?
(codex roles in team.json)
```

### Step 4 — Write the selection

Run the script with the chosen model and role:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/cmd-codex-model.sh" "<chosen-model>" "<all|role-id>"
```
