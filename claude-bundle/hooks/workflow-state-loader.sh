#!/bin/bash
# Loads workflow state on session start/resume
set -euo pipefail

STATE_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/workflow-state.json"

if [ -f "$STATE_FILE" ]; then
    STATE=$(cat "$STATE_FILE")
    STAGE=$(echo "$STATE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('current_stage','unknown'))" 2>/dev/null || echo "unknown")
    PROGRESS=$(echo "$STATE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('progress_percent',0))" 2>/dev/null || echo "0")
    TASK=$(echo "$STATE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('current_task','none'))" 2>/dev/null || echo "none")

    CONTEXT="## Active Workflow\n"
    CONTEXT+="- Stage: $STAGE\n"
    CONTEXT+="- Progress: $PROGRESS%\n"
    CONTEXT+="- Current Task: $TASK\n"
    CONTEXT+="- State File: $STATE_FILE\n"

    # Output as JSON for Claude Code hook system
    printf '{"hookSpecificOutput":{"additionalContext":"%s"}}' "$CONTEXT"
else
    printf '{"hookSpecificOutput":{"additionalContext":"No active workflow. Use workflow start <prd-path> to begin."}}'
fi
