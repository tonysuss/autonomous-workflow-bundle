#!/bin/bash
# Cross-platform notification handler
INPUT=$(cat)

# Extract message with jq if available, otherwise use python3 or default
if command -v jq &> /dev/null; then
    MESSAGE=$(echo "$INPUT" | jq -r '.message // "Claude needs your attention"')
elif command -v python3 &> /dev/null; then
    MESSAGE=$(echo "$INPUT" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("message", "Claude needs your attention"))' 2>/dev/null || echo "Claude needs your attention")
else
    MESSAGE="Claude needs your attention"
fi

# Sanitize message: escape quotes and backslashes to prevent injection
SAFE_MESSAGE=$(printf '%s' "$MESSAGE" | sed 's/\\/\\\\/g; s/"/\\"/g')

# Detect platform and use appropriate notification method
case "$(uname -s)" in
    Darwin)
        osascript -e "display notification \"$SAFE_MESSAGE\" with title \"Claude Code\" sound name \"Glass\"" 2>/dev/null || true
        ;;
    Linux)
        if command -v notify-send &> /dev/null; then
            notify-send "Claude Code" "$SAFE_MESSAGE" 2>/dev/null || true
        elif command -v zenity &> /dev/null; then
            zenity --notification --text="$SAFE_MESSAGE" 2>/dev/null || true
        fi
        ;;
esac

exit 0
