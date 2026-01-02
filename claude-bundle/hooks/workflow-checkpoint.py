#!/usr/bin/env python3
"""Creates checkpoints on session stop for resumability."""
import json
import sys
import os
from datetime import datetime

try:
    input_data = json.load(sys.stdin)
except (json.JSONDecodeError, Exception):
    sys.exit(0)

project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
state_file = os.path.join(project_dir, ".claude/workflow-state.json")
checkpoint_dir = os.path.join(project_dir, ".claude/checkpoints")

# Ensure checkpoint directory exists
os.makedirs(checkpoint_dir, exist_ok=True)

# Load current state
state = {}
if os.path.exists(state_file):
    try:
        with open(state_file) as f:
            state = json.load(f)
    except Exception:
        pass

# Skip if no active workflow
if not state.get("current_stage"):
    sys.exit(0)

# Create checkpoint
checkpoint = {
    "created_at": datetime.now().isoformat(),
    "state": state,
    "stop_reason": input_data.get("stop_reason", "session_end")
}

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
checkpoint_file = os.path.join(checkpoint_dir, f"checkpoint_{timestamp}.json")

try:
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint, f, indent=2)
except Exception:
    pass

# Update state with resume info
state["last_checkpoint"] = checkpoint_file
state["can_resume"] = True
state["checkpoint_at"] = datetime.now().isoformat()

try:
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
except Exception:
    pass

# Output checkpoint info
output = {
    "hookSpecificOutput": {
        "checkpointCreated": checkpoint_file,
        "canResume": True
    }
}
print(json.dumps(output))

sys.exit(0)
