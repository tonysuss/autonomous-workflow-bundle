#!/bin/bash
set -euo pipefail

# Build context for Claude
CONTEXT=""

# Git status
if git rev-parse --git-dir > /dev/null 2>&1; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
    CONTEXT+="## Current Git Status\n"
    CONTEXT+="Branch: $BRANCH\n"
    CONTEXT+="\nRecent commits:\n"
    CONTEXT+="$(git log --oneline -5 2>/dev/null || echo 'No commits')\n"
    
    # Uncommitted changes
    CHANGES=$(git status --porcelain 2>/dev/null | head -20)
    if [ -n "$CHANGES" ]; then
        CONTEXT+="\nUncommitted changes:\n$CHANGES\n"
    fi
fi

# TODO items from code
TODOS=$(grep -rn "TODO\|FIXME\|HACK" --include="*.js" --include="*.ts" --include="*.py" --include="*.go" --include="*.rs" . 2>/dev/null | head -10 || true)
if [ -n "$TODOS" ]; then
    CONTEXT+="\n## TODOs in codebase:\n$TODOS\n"
fi

# Recent issues (if GitHub CLI available)
if command -v gh &> /dev/null; then
    ISSUES=$(gh issue list --limit 5 2>/dev/null || true)
    if [ -n "$ISSUES" ]; then
        CONTEXT+="\n## Open GitHub Issues:\n$ISSUES\n"
    fi
fi

# Escape JSON special characters in CONTEXT
ESCAPED=$(printf '%s' "$CONTEXT" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read())[1:-1])')
# Output as JSON
echo "{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":\"$ESCAPED\"}}"