#!/bin/bash
set -e

INPUT=$(cat)
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')

# Prevent infinite loops
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
    exit 0
fi

ERRORS=""

# Run linter
if command -v npm &> /dev/null && [ -f "package.json" ]; then
    if ! npm run lint 2>&1; then
        ERRORS+="Linting failed. Please fix lint errors.\n"
    fi
fi

# Run type check
if [ -f "tsconfig.json" ]; then
    if ! npx tsc --noEmit 2>&1; then
        ERRORS+="TypeScript type checking failed.\n"
    fi
fi

# Run tests
if [ -f "package.json" ]; then
    if ! npm test 2>&1; then
        ERRORS+="Tests failed. Please fix failing tests.\n"
    fi
fi

# Block if errors found
if [ -n "$ERRORS" ]; then
    echo -e "Quality checks failed:\n$ERRORS" >&2
    exit 2
fi

echo "All quality checks passed!"
exit 0