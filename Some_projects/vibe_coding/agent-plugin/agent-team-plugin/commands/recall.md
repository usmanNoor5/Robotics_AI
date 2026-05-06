---
name: recall
description: View and search cross-session agent-team memories. Lists recent sessions or searches by keyword. Zero Claude tokens consumed.
argument-hint: '[keyword...]'
disable-model-invocation: true
allowed-tools: Bash(bash:*)
---

!`bash "${CLAUDE_PLUGIN_ROOT}/scripts/cmd-memory.sh" $ARGUMENTS`
