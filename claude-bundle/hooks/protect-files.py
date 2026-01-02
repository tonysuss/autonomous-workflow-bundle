#!/usr/bin/env python3
import json
import sys
import os

# Files/patterns that should never be modified
PROTECTED_FILES = [
    ".env",
    ".env.local",
    ".env.production",
    "secrets.json",
    "credentials.json",
    ".git/",
    "node_modules/",
    "package-lock.json",  # Usually shouldn't be edited directly
    "yarn.lock",
]

PROTECTED_PATTERNS = [
    "**/id_rsa",
    "**/id_ed25519",
    "**/*.pem",
    "**/*.key",
]

try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(1)

tool_input = input_data.get("tool_input", {})
file_path = tool_input.get("file_path") or tool_input.get("filePath") or ""

if not file_path:
    sys.exit(0)

# Normalize path
file_path = os.path.normpath(file_path)

# Prevent generated code/config from being written into the bundle directory (.claude)
claude_allowed = [
    os.path.normpath(".claude/workflow-state.json"),
    os.path.normpath(".claude/requirements.json"),
    os.path.normpath(".claude/implementation-plan.json"),
    os.path.normpath(".claude/validation-report.json"),
    os.path.normpath(".claude/settings.json"),
    os.path.normpath(".claude/settings.local.json"),
    os.path.normpath(".claude/checkpoints")
]

parts = file_path.split(os.sep)
if ".claude" in parts:
    idx = parts.index(".claude")
    claude_subpath = os.sep.join(parts[idx:])
    allowed = any(
        claude_subpath == allowed_path or claude_subpath.startswith(f"{allowed_path}{os.sep}")
        for allowed_path in claude_allowed
    )
    if not allowed:
        print(f"🔒 PROTECTED: Keep generated code outside .claude ({file_path})", file=sys.stderr)
        sys.exit(2)

# Check protected files
for protected in PROTECTED_FILES:
    if protected in file_path or file_path.endswith(protected):
        print(f"🔒 PROTECTED: Cannot modify {file_path}", file=sys.stderr)
        print(f"This file is protected by project policy.", file=sys.stderr)
        sys.exit(2)

# Check for path traversal
if ".." in file_path:
    print(f"🚫 BLOCKED: Path traversal detected in {file_path}", file=sys.stderr)
    sys.exit(2)

sys.exit(0)
