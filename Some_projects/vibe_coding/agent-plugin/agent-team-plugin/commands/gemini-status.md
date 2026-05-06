---
name: gemini-status
description: Show Gemini CLI status — version, auth state, active model. Zero Claude tokens consumed.
disable-model-invocation: true
allowed-tools: Bash(bash:*)
---

!`bash "${CLAUDE_PLUGIN_ROOT}/scripts/cmd-gemini-status.sh"`
