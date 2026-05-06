# Agent Team Plugin — Feature Plans

## Interactive Model Selection (in progress)

### Goal
When `/agent-team:opencode-model`, `/agent-team:codex-model`, or `/agent-team:gemini-model` is run
with **no arguments**, show an interactive arrow-key selection UI instead of static text.
Non-interactive argument usage (`/agent-team:opencode-model github-copilot/claude-sonnet-4.5 all`)
is unchanged.

### Model Lists (hardcoded, update when new models release)

**OpenCode (GitHub Copilot)**
- github-copilot/claude-haiku-4.5
- github-copilot/claude-opus-4.5
- github-copilot/claude-sonnet-4
- github-copilot/claude-sonnet-4.5
- github-copilot/gemini-2.5-pro
- github-copilot/gemini-3-flash-preview
- github-copilot/gemini-3.1-pro-preview
- github-copilot/gpt-4.1
- github-copilot/gpt-4o
- github-copilot/gpt-5-mini
- github-copilot/gpt-5.2
- github-copilot/gpt-5.2-codex
- github-copilot/gpt-5.3-codex
- github-copilot/gpt-5.4-mini
- github-copilot/grok-code-fast-1

**Codex**
- gpt-5.5
- gpt-5.4
- gpt-5.4-mini
- gpt-5.3-codex
- gpt-5.2
- codex-auto-review

**Gemini**
- gemini-3.1-pro
- gemini-3-pro
- gemini-3-flash
- gemini-3.1-flash-lite-preview
- gemini-3-flash-preview
- gemini-3-pro-preview
- gemini-2.5-pro
- gemini-2.5-flash
- gemini-2.5-flash-lite
- gemini-2.0-flash
- gemini-1.5-pro
- gemini-1.5-flash

### Implementation

1. `scripts/lib/select-menu.sh` — shared interactive selector function
   - `select_from_list <prompt> <item1> <item2> ...` → echoes selected item
   - Priority: fzf (if installed + TTY) → pure bash arrow-key menu → numbered fallback
   - Ctrl+C exits cleanly with "Cancelled."

2. Interactive flow (no-args mode):
   - Stage 1: pick model from list (arrow keys)
   - Stage 2: pick role(s): all / individual role
   - Write to `team.local.json`, print confirmation

3. `cmd-opencode-model.sh`, `cmd-codex-model.sh`, `cmd-gemini-model.sh` — add interactive path

### Updating Models
When a provider releases new models, edit the hardcoded list in the relevant script and run:
```bash
rsync -a --delete plugins/agent-team/ ~/.claude/plugins/cache/finally-local-plugins/agent-team/1.0.0/
```
Then `/reload-plugins`.

---

## Bug Fixes Applied

### Gemini multi-round context loss (fixed 2026-04-26)

**Problem:** In multi-round sessions, Gemini agents started each round with no memory of their prior work.

**Root cause — two separate bugs:**

1. `dispatch-agent.sh` called `dispatch_gemini` with only 2 arguments:
   ```bash
   # Before (broken)
   dispatch_gemini "$PROMPT" "$RESULT_FILE"
   ```
   Missing args meant Gemini ran in the wrong directory, model overrides from `team.local.json` were silently ignored, and no results directory was passed for context injection.

2. `gemini.sh` had no `RESULTS_DIR` parameter and no prior-round injection logic — unlike `codex.sh` which had both.

**Fix:**

`dispatch-agent.sh` — now passes all 6 args:
```bash
GEMINI_MODEL=$(jq -r '.gemini_model // ""' "$PROFILE" 2>/dev/null)
dispatch_gemini "$PROMPT" "$RESULT_FILE" "$PROJECT_ROOT" "$PROFILE" "$GEMINI_MODEL" "$AGENT_DIR/results"
```

`gemini.sh` — added `RESULTS_DIR` as 6th parameter + prior-round injection block (same pattern as `codex.sh`). Injects a `## Your Prior Work` section built from all previous `*.md` result files before the main prompt.

**Note on OpenCode:** Not affected — OpenCode uses native session IDs (`opencode run -s <id>`) so it remembers everything natively without prompt injection.
