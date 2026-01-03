#!/bin/bash
set -euo pipefail

if ! command -v jq &> /dev/null; then
    exit 0
fi

# Read hook input from stdin
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
FORMATTER_CONFIG="${CLAUDE_FORMATTER_CONFIG:-$PROJECT_DIR/.claude/formatters.json}"

if [ ! -f "$FORMATTER_CONFIG" ]; then
    exit 0
fi

ENABLED=$(jq -r '.enabled // false' "$FORMATTER_CONFIG" 2>/dev/null || echo "false")
if [ "$ENABLED" != "true" ]; then
    exit 0
fi

EXTENSION=""
if [[ "$FILE_PATH" == *.* ]]; then
    EXTENSION=".${FILE_PATH##*.}"
fi
EXTENSION=$(echo "$EXTENSION" | tr '[:upper:]' '[:lower:]')

COMMANDS=$(jq -r --arg ext "$EXTENSION" '.formatters[$ext] // .formatters["*"] // empty | .[]?' "$FORMATTER_CONFIG" 2>/dev/null || true)
if [ -z "$COMMANDS" ]; then
    exit 0
fi

while IFS= read -r COMMAND; do
    if [ -z "$COMMAND" ]; then
        continue
    fi

    if [[ "$COMMAND" == *"{file}"* ]]; then
        FORMATTED_COMMAND="${COMMAND//\{file\}/$FILE_PATH}"
    else
        FORMATTED_COMMAND="$COMMAND \"$FILE_PATH\""
    fi

    TOOL=$(printf "%s" "$FORMATTED_COMMAND" | awk '{print $1}')
    if [ -n "$TOOL" ] && command -v "$TOOL" &> /dev/null; then
        bash -c "$FORMATTED_COMMAND" 2>/dev/null || true
    fi
done <<< "$COMMANDS"

exit 0
