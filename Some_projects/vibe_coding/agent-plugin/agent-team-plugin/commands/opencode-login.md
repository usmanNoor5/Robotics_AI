---
name: opencode-login
description: Check OpenCode CLI auth state. Prints current login status or instructions to authenticate. Zero Claude tokens consumed.
disable-model-invocation: true
allowed-tools: Bash(bash:*)
---

!`bash "${CLAUDE_PLUGIN_ROOT}/scripts/cmd-opencode-login.sh"`
