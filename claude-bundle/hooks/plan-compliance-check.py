#!/usr/bin/env python3
"""Validates file operations against the approved implementation plan."""
import json
import sys
import os

try:
    input_data = json.load(sys.stdin)
except (json.JSONDecodeError, Exception):
    sys.exit(0)

tool_input = input_data.get("tool_input", {})
file_path = tool_input.get("file_path") or tool_input.get("filePath") or ""

if not file_path:
    sys.exit(0)

project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
plan_file = os.path.join(project_dir, ".claude/implementation-plan.json")

# If no plan exists, allow (might be in planning phase)
if not os.path.exists(plan_file):
    sys.exit(0)

try:
    with open(plan_file) as f:
        plan = json.load(f)
except Exception:
    sys.exit(0)

file_structure = plan.get("file_structure", {})
planned_files = file_structure.get("files", [])
planned_paths = []

for f in planned_files:
    if isinstance(f, dict):
        planned_paths.append(f.get("path", ""))
    else:
        planned_paths.append(str(f))

# Normalize paths for comparison
file_path_normalized = os.path.normpath(file_path)
is_planned = any(file_path_normalized.endswith(p) for p in planned_paths if p)

# Allow config files, test files, and workflow files outside plan
allowed_patterns = [
    ".json", ".md", ".yml", ".yaml",
    "test_", "_test.", ".test.", "__tests__",
    ".claude/", "node_modules/", ".git/"
]
is_allowed = any(pattern in file_path for pattern in allowed_patterns)

if not is_planned and not is_allowed:
    output = {
        "hookSpecificOutput": {
            "permissionDecision": "ask",
            "permissionDecisionReason": f"File not in implementation plan: {os.path.basename(file_path)}"
        }
    }
    print(json.dumps(output))

sys.exit(0)
