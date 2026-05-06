---
name: codex-status
description: Show Codex CLI status — auth, active model, daily limit. Zero Claude tokens consumed.
disable-model-invocation: true
allowed-tools: Bash(bash:*)
---

!`bash "${CLAUDE_PLUGIN_ROOT}/scripts/cmd-codex-status.sh"`
