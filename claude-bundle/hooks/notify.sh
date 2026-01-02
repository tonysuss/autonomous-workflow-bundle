#!/bin/bash
INPUT=$(cat)
MESSAGE=$(echo "$INPUT" | jq -r '.message // "Claude needs your attention"')

osascript -e "display notification \"$MESSAGE\" with title \"Claude Code\" sound name \"Glass\""