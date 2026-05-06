---
name: opencode-status
description: Show OpenCode CLI status — version, auth provider, active model. Zero Claude tokens consumed.
disable-model-invocation: true
allowed-tools: Bash(bash:*)
---

!`bash "${CLAUDE_PLUGIN_ROOT}/scripts/cmd-opencode-status.sh"`
