#!/usr/bin/env python3
"""Processes sub-agent results and triggers workflow transitions."""
import json
import sys
import os
from datetime import datetime

# Ensure sibling module imports work regardless of CWD
_HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))
if _HOOKS_DIR not in sys.path:
    sys.path.insert(0, _HOOKS_DIR)

from stage_gates import validate_transition, get_gate_mode

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
# Fail-safe: treat missing success field as failure, not success
success = result.get("success", False)

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

# Log failures for debugging
if not success:
    state.setdefault("failed_agents", []).append({
        "agent": agent_name,
        "at": datetime.now().isoformat(),
        "result": result
    })


def save_state():
    """Persist state to disk."""
    try:
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


# Persist agent result BEFORE gate validation so gates see current state
save_state()

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
        # For testing, both test-runner-fixer and acceptance-validator must complete
        elif from_stage == "testing":
            test_done = state.get("agent_results", {}).get("test-runner-fixer", {}).get("success", False)
            acceptance_done = state.get("agent_results", {}).get("acceptance-validator", {}).get("success", False)
            if test_done and acceptance_done:
                should_transition = True
        else:
            should_transition = True

        if should_transition:
            # Validate stage gate before allowing transition
            gate_passed, gate_reason = validate_transition(from_stage, to_stage, project_dir)
            gate_mode = get_gate_mode()

            if not gate_passed:
                if gate_mode == "strict":
                    # Block transition and log failure
                    state.setdefault("gate_failures", []).append({
                        "from": from_stage,
                        "to": to_stage,
                        "reason": gate_reason,
                        "at": datetime.now().isoformat()
                    })
                    should_transition = False
                else:
                    # Warn mode: log but allow transition
                    state.setdefault("gate_warnings", []).append({
                        "from": from_stage,
                        "to": to_stage,
                        "reason": gate_reason,
                        "at": datetime.now().isoformat()
                    })

            if should_transition:
                # Mark the from_stage as completed
                state.setdefault("stage_status", {})[from_stage] = "completed"

                # Transition to next stage
                state["current_stage"] = to_stage

                # Log transition with gate info
                state.setdefault("stage_transitions", []).append({
                    "from": from_stage,
                    "to": to_stage,
                    "at": datetime.now().isoformat(),
                    "gate_passed": gate_passed,
                    "gate_reason": gate_reason
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

# Final state save (captures any transition updates)
save_state()

sys.exit(0)
