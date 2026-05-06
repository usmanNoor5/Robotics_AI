---
name: session
description: Show the current state of the active or most recent agent team session — which agents are working, what round they're on, any pending inbox messages, and result summaries.
---

# /agent-team:session

Show live team session status.

**Your first output must be:** `🤖 Agent Team Status`

## Steps

### 1. Find Latest Session

```bash
LATEST=$(ls -t ~/.agent-team/sessions/ 2>/dev/null | head -1)
if [[ -z "$LATEST" ]]; then
  echo "No active session found. Run /agent-team:start to begin."
  exit 0
fi
SESSION_DIR="$HOME/.agent-team/sessions/$LATEST"
```

### 2. Read Session Info

```bash
cat "$SESSION_DIR/session.json"
cat "$SESSION_DIR/team.json"
```

### 3. Display Status Table

For each agent in the team, show:

```
🤖 AGENT TEAM STATUS — Session: <session-id>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Agent               Model     Status    Round   Messages
─────────────────────────────────────────────────────────
🔴 Frontend Eng     codex     done      1       1 unread
🟢 Backend Eng      copilot   working   1       0 unread
🟡 QA Engineer      gemini    idle      —       2 unread
🔵 Coordinator      claude    —         —       1 unread
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Check each agent's profile.json for status and last_round.
Count unread messages in each inbox.

### 4. Show Recent Results

If any agents have completed results, show a brief excerpt (first 5 lines):

```bash
for RESULT in "$SESSION_DIR"/agents/*/results/*.md; do
  head -5 "$RESULT"
done
```

### 5. Show Pending Messages

List any unread messages across all inboxes (without marking them read):

```bash
find "$SESSION_DIR" -path "*/inbox/*.json" -exec jq 'select(.read == false)' {} \;
```
