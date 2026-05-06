---
name: message
description: Send a message directly to a specific agent in the current session, or broadcast to all agents. Useful for the user to give mid-session instructions to a specific teammate.
---

# /agent-team:message \<agent-id\> \<message\>

Send a message from you (the user, via coordinator) to a specific agent.

**Your first output must be:** `✉ Sending message...`

## Usage Examples

```text
/agent-team:message frontend "Please also add dark mode support to the new components"
/agent-team:message backend "The frontend needs a /api/prices/history endpoint returning the last 50 ticks"
/agent-team:message all "Stop what you're doing — we're changing the database to Postgres"
```

## Steps

### 1. Find Latest Session

```bash
LATEST=$(ls -t ~/.agent-team/sessions/ 2>/dev/null | head -1)
SESSION_DIR="$HOME/.agent-team/sessions/$LATEST"
```

### 2. Resolve Target

- If `<agent-id>` is `all`: send to every agent in the team
- If `<agent-id>` is a role id in team.json: send to that agent
- Otherwise: show available agent IDs from team.json and ask which one

### 3. Send Message

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/send-message.sh \
  "$SESSION_ID" "coordinator" "$AGENT_ID" "$MESSAGE" "$CURRENT_ROUND"
```

For `all`:

```bash
for AGENT_ID in $(jq -r '.roles[].id' "$SESSION_DIR/team.json"); do
  bash ${CLAUDE_PLUGIN_ROOT}/scripts/send-message.sh \
    "$SESSION_ID" "coordinator" "$AGENT_ID" "$MESSAGE" "$CURRENT_ROUND"
done
```

### 4. Confirm

```text
✉ Message delivered to <Agent Name>
  They will receive it on their next dispatch.
```

Note: the agent will read this message at the start of their next round when dispatch-agent.sh reads their inbox.
