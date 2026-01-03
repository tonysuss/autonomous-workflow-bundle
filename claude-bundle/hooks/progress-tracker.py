#!/usr/bin/env python3
"""Tracks implementation progress after file modifications."""
import json
import sys
import os
from datetime import datetime

try:
    input_data = json.load(sys.stdin)
except (json.JSONDecodeError, Exception):
    sys.exit(0)

tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})
file_path = tool_input.get("file_path") or tool_input.get("filePath") or ""

if not file_path:
    sys.exit(0)

# Load workflow state
project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
state_file = os.path.join(project_dir, ".claude/workflow-state.json")
plan_file = os.path.join(project_dir, ".claude/implementation-plan.json")

state = {
    "files_created": [],
    "files_modified": [],
    "current_stage": "prd_analysis",
    "progress_percent": 0
}

if os.path.exists(state_file):
    try:
        with open(state_file) as f:
            state = json.load(f)
    except Exception:
        pass

# Update state based on tool
if tool_name == "Write":
    if file_path not in state.get("files_created", []):
        state.setdefault("files_created", []).append(file_path)
elif tool_name in ["Edit", "MultiEdit"]:
    if file_path not in state.get("files_modified", []):
        state.setdefault("files_modified", []).append(file_path)

state["last_activity"] = datetime.now().isoformat()

# Ensure stage_status dict exists
if "stage_status" not in state:
    state["stage_status"] = {
        "prd_analysis": "pending",
        "plan_generation": "pending",
        "security_legal_review": "pending",
        "implementation": "pending",
        "testing": "pending",
        "completion": "pending"
    }

# Update stage_status based on current_stage (mark as in_progress, don't auto-advance)
current_stage = state.get("current_stage")
if current_stage and current_stage in state["stage_status"]:
    if state["stage_status"][current_stage] == "pending":
        state["stage_status"][current_stage] = "in_progress"

# NOTE: Stage advancement is handled by subagent-result-processor.py, not here.
# This ensures approval gates (security/legal review) are respected.
# We only track artifact existence for informational purposes.
requirements_file = os.path.join(project_dir, ".claude/requirements.json")
if os.path.exists(requirements_file):
    state["stage_status"]["prd_analysis"] = "completed"

if os.path.exists(plan_file):
    state["stage_status"]["plan_generation"] = "completed"

# Calculate progress if plan exists (match gate logic: normalized path matching)
if os.path.exists(plan_file):
    try:
        with open(plan_file) as f:
            plan = json.load(f)
        file_structure = plan.get("file_structure", {})
        planned_files = file_structure.get("files", [])
        if planned_files:
            # Extract and normalize planned paths (same logic as stage_gates.py)
            planned_paths = set()
            for f in planned_files:
                if isinstance(f, dict):
                    path = f.get("path", "")
                else:
                    path = str(f)
                if path:
                    planned_paths.add(os.path.normpath(os.path.expanduser(os.path.expandvars(path))))

            if planned_paths:
                # Normalize touched files
                created = state.get("files_created", [])
                modified = state.get("files_modified", [])
                touched_normalized = set()
                for f in created + modified:
                    touched_normalized.add(os.path.normpath(os.path.expanduser(os.path.expandvars(f))))

                # Count matched planned files (same logic as gate)
                matched = 0
                for planned in planned_paths:
                    for touched in touched_normalized:
                        if touched == planned or touched.endswith(os.sep + planned):
                            matched += 1
                            break

                state["progress_percent"] = min(100, int(matched / len(planned_paths) * 100))
    except Exception:
        pass

# Write updated state
try:
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
except Exception:
    pass

sys.exit(0)
