#!/usr/bin/env python3
"""Processes sub-agent results and triggers workflow transitions."""
import json
import sys
import os
from datetime import datetime

STAGE_TRANSITIONS = {
    "prd-analyzer": ("prd_analysis", "plan_generation"),
    "plan-architect": ("plan_generation", "security_legal_review"),
    "security-auditor": ("security_legal_review", "implementation"),
    "legal-reviewer": ("security_legal_review", "implementation"),
    "code-implementer": ("implementation", "testing"),
    "asset-builder": ("implementation", "testing"),
    "test-runner-fixer": ("testing", "completion"),
    "acceptance-validator": ("testing", "completion"),
    "doc-writer": ("completion", "done")
}

try:
    input_data = json.load(sys.stdin)
except (json.JSONDecodeError, Exception):
    sys.exit(0)

agent_name = input_data.get("agent_name", "")
result = input_data.get("result", {})
success = result.get("success", True)

project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
state_file = os.path.join(project_dir, ".claude/workflow-state.json")

state = {}
if os.path.exists(state_file):
    try:
        with open(state_file) as f:
            state = json.load(f)
    except Exception:
        pass

# Record agent completion
state.setdefault("agent_results", {})[agent_name] = {
    "completed_at": datetime.now().isoformat(),
    "success": success
}

# Check for stage transition
if agent_name in STAGE_TRANSITIONS and success:
    from_stage, to_stage = STAGE_TRANSITIONS[agent_name]
    current = state.get("current_stage", "")

    if current == from_stage:
        should_transition = False

        # For security_legal_review, both agents must complete
        if from_stage == "security_legal_review":
            security_done = state.get("agent_results", {}).get("security-auditor", {}).get("success", False)
            legal_done = state.get("agent_results", {}).get("legal-reviewer", {}).get("success", False)
            if security_done and legal_done:
                should_transition = True
        else:
            should_transition = True

        if should_transition:
            # Mark the from_stage as completed
            state.setdefault("stage_status", {})[from_stage] = "completed"

            # Transition to next stage
            state["current_stage"] = to_stage

            # Log transition
            state.setdefault("stage_transitions", []).append({
                "from": from_stage,
                "to": to_stage,
                "at": datetime.now().isoformat()
            })

# Update stage status for current stage
current_stage = state.get("current_stage")
if current_stage:
    state.setdefault("stage_status", {})
    # Handle terminal "done" state
    if current_stage == "done":
        state["stage_status"]["completion"] = "completed"
        state["workflow_complete"] = True
        state["completed_at"] = datetime.now().isoformat()
    elif current_stage in state["stage_status"]:
        if state["stage_status"][current_stage] != "completed":
            state["stage_status"][current_stage] = "in_progress"

try:
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
except Exception:
    pass

sys.exit(0)
