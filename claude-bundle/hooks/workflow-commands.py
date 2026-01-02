#!/usr/bin/env python3
"""
Workflow command handler for: workflow start, workflow status, workflow resume
This script is invoked via UserPromptSubmit hook when workflow commands are detected.
"""
import json
import sys
import os
import uuid
from datetime import datetime


def strip_quotes(value):
    """Remove wrapping quotes without touching internal content."""
    if not isinstance(value, str):
        return value
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1].strip()
    return value.strip()


def extract_prd_from_ralph(raw_prompt, prompt_lower):
    """
    Parse `/ralph-loop Start autonomous workflow with PRD at <path>` to a PRD path.
    Uses the original prompt for path casing and spacing.
    """
    if not prompt_lower.startswith("/ralph-loop"):
        return None

    markers = ["with prd at", "prd at", "with prd"]
    for marker in markers:
        if marker in prompt_lower:
            start = prompt_lower.index(marker) + len(marker)
            candidate = raw_prompt[start:].strip(" :")
            candidate = strip_quotes(candidate)
            if candidate:
                return candidate

    # Fallback: use everything after the command token
    tokens = raw_prompt.split(maxsplit=1)
    if len(tokens) > 1:
        candidate = strip_quotes(tokens[1])
        if candidate:
            return candidate

    return None

def get_paths():
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    return {
        "state": os.path.join(project_dir, ".claude/workflow-state.json"),
        "requirements": os.path.join(project_dir, ".claude/requirements.json"),
        "plan": os.path.join(project_dir, ".claude/implementation-plan.json"),
        "checkpoints": os.path.join(project_dir, ".claude/checkpoints"),
    }

def load_state(paths):
    if os.path.exists(paths["state"]):
        try:
            with open(paths["state"]) as f:
                return json.load(f)
        except Exception:
            pass
    return None

def save_state(paths, state):
    os.makedirs(os.path.dirname(paths["state"]), exist_ok=True)
    with open(paths["state"], 'w') as f:
        json.dump(state, f, indent=2)

def workflow_start(prd_path, paths):
    """Initialize a new workflow with the given PRD."""
    # Resolve PRD path
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    full_prd_path = os.path.join(project_dir, prd_path) if not os.path.isabs(prd_path) else prd_path

    if not os.path.exists(full_prd_path):
        return {
            "error": f"PRD file not found: {prd_path}",
            "action": "none"
        }

    state = {
        "workflow_id": str(uuid.uuid4()),
        "prd_path": prd_path,
        "current_stage": "prd_analysis",
        "stage_status": {
            "prd_analysis": "in_progress",
            "plan_generation": "pending",
            "security_legal_review": "pending",
            "implementation": "pending",
            "testing": "pending",
            "completion": "pending"
        },
        "progress_percent": 0,
        "current_task": None,
        "started_at": datetime.now().isoformat(),
        "last_activity": datetime.now().isoformat(),
        "files_created": [],
        "files_modified": [],
        "agent_results": {},
        "stage_transitions": [],
        "blockers": [],
        "escalations": [],
        "last_checkpoint": None,
        "can_resume": True
    }

    save_state(paths, state)

    return {
        "action": "start",
        "workflow_id": state["workflow_id"],
        "prd_path": prd_path,
        "current_stage": "prd_analysis",
        "next_step": f"Invoke prd-analyzer agent to analyze: {prd_path}",
        "message": f"Workflow started. Beginning PRD analysis of {prd_path}"
    }

def workflow_status(paths):
    """Get current workflow status."""
    state = load_state(paths)

    if not state or not state.get("current_stage"):
        return {
            "action": "status",
            "status": "no_active_workflow",
            "message": "No active workflow. Use 'workflow start <prd-path>' to begin."
        }

    # Calculate overall progress
    stage_order = ["prd_analysis", "plan_generation", "security_legal_review",
                   "implementation", "testing", "completion"]
    completed_stages = sum(1 for s in stage_order
                          if state.get("stage_status", {}).get(s) == "completed")
    overall_progress = int((completed_stages / len(stage_order)) * 100)

    return {
        "action": "status",
        "workflow_id": state.get("workflow_id"),
        "prd_path": state.get("prd_path"),
        "current_stage": state.get("current_stage"),
        "stage_status": state.get("stage_status", {}),
        "progress_percent": overall_progress,
        "current_task": state.get("current_task"),
        "files_created": len(state.get("files_created", [])),
        "files_modified": len(state.get("files_modified", [])),
        "blockers": state.get("blockers", []),
        "last_activity": state.get("last_activity"),
        "can_resume": state.get("can_resume", False)
    }

def workflow_resume(paths):
    """Resume workflow from last checkpoint."""
    state = load_state(paths)

    if not state:
        # Check for checkpoints
        checkpoint_dir = paths["checkpoints"]
        if os.path.exists(checkpoint_dir):
            checkpoints = sorted([f for f in os.listdir(checkpoint_dir) if f.endswith('.json')])
            if checkpoints:
                latest = os.path.join(checkpoint_dir, checkpoints[-1])
                try:
                    with open(latest) as f:
                        checkpoint = json.load(f)
                        state = checkpoint.get("state", {})
                        save_state(paths, state)
                except Exception:
                    pass

    if not state or not state.get("current_stage"):
        return {
            "action": "resume",
            "status": "no_workflow_to_resume",
            "message": "No workflow to resume. Use 'workflow start <prd-path>' to begin."
        }

    # Update state to mark as resumed
    state["last_activity"] = datetime.now().isoformat()
    state["can_resume"] = True
    save_state(paths, state)

    # Determine next action based on current stage
    stage = state.get("current_stage", "prd_analysis")
    stage_agents = {
        "prd_analysis": "prd-analyzer",
        "plan_generation": "plan-architect",
        "security_legal_review": "security-auditor and legal-reviewer",
        "implementation": "code-implementer",
        "testing": "test-runner-fixer and acceptance-validator",
        "completion": "doc-writer"
    }

    return {
        "action": "resume",
        "workflow_id": state.get("workflow_id"),
        "current_stage": stage,
        "current_task": state.get("current_task"),
        "next_agent": stage_agents.get(stage, "unknown"),
        "message": f"Resuming workflow at stage: {stage}"
    }

def extract_prd_from_prompt(raw_prompt, prompt_lower):
    """Heuristically extract PRD path from free-form workflow start prompts."""
    if "workflow start" in prompt_lower:
        idx = prompt_lower.index("workflow start") + len("workflow start")
        candidate = strip_quotes(raw_prompt[idx:].strip(" :"))
        if candidate:
            return candidate

    if "prd at" in prompt_lower:
        idx = prompt_lower.index("prd at") + len("prd at")
        candidate = strip_quotes(raw_prompt[idx:].strip(" :"))
        if candidate:
            return candidate

    if "start" in prompt_lower:
        parts = raw_prompt.split()
        for i, part in enumerate(parts):
            if part.lower() == "start" and i + 1 < len(parts):
                candidate = strip_quotes(" ".join(parts[i + 1:]).strip())
                if candidate:
                    return candidate

    return None


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        sys.exit(0)

    raw_prompt = input_data.get("prompt", "").strip()
    prompt_lower = raw_prompt.lower()
    paths = get_paths()

    result = None

    # Parse workflow commands
    if prompt_lower.startswith("/ralph-loop"):
        prd_path = extract_prd_from_ralph(raw_prompt, prompt_lower)
        if prd_path:
            result = workflow_start(prd_path, paths)
        else:
            result = {
                "error": "No PRD path detected after /ralph-loop. Use '/ralph-loop Start autonomous workflow with PRD at <path>'.",
                "action": "none"
            }
    elif prompt_lower.startswith("workflow start "):
        prd_path = strip_quotes(raw_prompt[len("workflow start "):].strip())
        result = workflow_start(prd_path, paths)
    elif prompt_lower == "workflow status":
        result = workflow_status(paths)
    elif prompt_lower == "workflow resume":
        result = workflow_resume(paths)
    elif "workflow" in prompt_lower and ("start" in prompt_lower or "status" in prompt_lower or "resume" in prompt_lower):
        # Fuzzy match for workflow commands
        if "start" in prompt_lower:
            prd_path = extract_prd_from_prompt(raw_prompt, prompt_lower)
            if prd_path:
                result = workflow_start(prd_path, paths)
        elif "status" in prompt_lower:
            result = workflow_status(paths)
        elif "resume" in prompt_lower:
            result = workflow_resume(paths)

    if result:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "workflowCommand": result
            }
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
