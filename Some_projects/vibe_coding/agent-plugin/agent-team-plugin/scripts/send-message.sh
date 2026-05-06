#!/bin/bash
# Send a message from one agent to another (or to/from coordinator).
# Messages are JSON files dropped into the recipient's inbox.
# Usage: send-message.sh <session-id> <from-id> <to-id> <content> [round]
# from/to can be agent IDs or "coordinator"

set -euo pipefail

source "${CLAUDE_PLUGIN_ROOT}/scripts/lib/common.sh" 2>/dev/null || {
  CLAUDE_PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
  source "${CLAUDE_PLUGIN_ROOT}/scripts/lib/common.sh"
}

SESSION_ID="${1:?session-id required}"
FROM="${2:?from required}"
TO="${3:?to required}"
CONTENT="${4:?content required}"
ROUND="${5:-0}"

SESSION_DIR="$(session_dir "$SESSION_ID")"
MSG_ID="$(new_message_id)"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Resolve inbox path
if [[ "$TO" == "coordinator" ]]; then
  INBOX="${SESSION_DIR}/coordinator/inbox"
else
  INBOX="${SESSION_DIR}/agents/${TO}/inbox"
fi

[[ -d "$INBOX" ]] || { log_error "Inbox not found for '$TO' in session $SESSION_ID"; exit 1; }

# Write message as JSON
MSG_FILE="${INBOX}/${TIMESTAMP//:/}-${FROM}.json"

cat > "$MSG_FILE" <<EOF
{
  "id": "$MSG_ID",
  "from": "$FROM",
  "to": "$TO",
  "round": $ROUND,
  "timestamp": "$TIMESTAMP",
  "read": false,
  "content": $(printf '%s' "$CONTENT" | jq -Rs .)
}
EOF

log_success "Message sent: $FROM → $TO ($MSG_ID)"
echo "$MSG_FILE"
