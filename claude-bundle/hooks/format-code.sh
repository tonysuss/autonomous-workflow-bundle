#!/bin/bash
set -euo pipefail

# Read hook input from stdin
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.filePath // empty')

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Format based on file extension
case "$FILE_PATH" in
    *.py)
        if command -v black &> /dev/null; then
            black "$FILE_PATH" 2>/dev/null || true
            isort "$FILE_PATH" 2>/dev/null || true
        fi
        ;;
    *.js|*.ts|*.jsx|*.tsx|*.json|*.md)
        if command -v prettier &> /dev/null; then
            prettier --write "$FILE_PATH" 2>/dev/null || true
        fi
        ;;
    *.go)
        if command -v gofmt &> /dev/null; then
            gofmt -w "$FILE_PATH" 2>/dev/null || true
        fi
        ;;
esac

exit 0