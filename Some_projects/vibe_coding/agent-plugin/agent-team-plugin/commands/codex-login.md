---
name: codex-login
description: Check Codex CLI auth state. Prints current login status or instructions to authenticate. Zero Claude tokens consumed.
disable-model-invocation: true
allowed-tools: Bash(bash:*)
---

!`bash "${CLAUDE_PLUGIN_ROOT}/scripts/cmd-codex-login.sh"`
