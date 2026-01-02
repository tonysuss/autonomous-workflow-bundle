#!/usr/bin/env python3
import json
import re
import sys

# Dangerous patterns to block
BLOCKED_PATTERNS = [
    (r"rm\s+-rf\s+/", "Cannot delete root filesystem"),
    (r"rm\s+-rf\s+~", "Cannot delete home directory"),
    (r"sudo\s+rm", "Cannot use sudo rm"),
    (r"chmod\s+777", "Cannot set world-writable permissions"),
    (r">\s*/etc/", "Cannot overwrite system files"),
    (r"curl.*\|\s*sh", "Cannot pipe curl to shell"),
    (r"wget.*\|\s*sh", "Cannot pipe wget to shell"),
    (r":(){.*};:", "Fork bomb detected"),
]

# Patterns that require confirmation
WARN_PATTERNS = [
    (r"rm\s+-rf", "Recursive force delete"),
    (r"DROP\s+DATABASE", "Database drop operation"),
    (r"DROP\s+TABLE", "Table drop operation"),
    (r"TRUNCATE", "Table truncate operation"),
]

try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(1)

tool_name = input_data.get("tool_name", "")
if tool_name != "Bash":
    sys.exit(0)

command = input_data.get("tool_input", {}).get("command", "")

# Check for blocked patterns
for pattern, message in BLOCKED_PATTERNS:
    if re.search(pattern, command, re.IGNORECASE):
        print(f"🚫 BLOCKED: {message}", file=sys.stderr)
        print(f"Command: {command}", file=sys.stderr)
        sys.exit(2)

# Check for warning patterns (allow but notify)
for pattern, message in WARN_PATTERNS:
    if re.search(pattern, command, re.IGNORECASE):
        # Use JSON output to ask for confirmation
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": f"⚠️ Warning: {message}"
            }
        }
        print(json.dumps(output))
        sys.exit(0)

sys.exit(0)