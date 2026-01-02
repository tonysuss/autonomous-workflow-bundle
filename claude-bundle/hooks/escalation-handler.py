#!/usr/bin/env python3
"""Handles escalations and human intervention points."""
import json
import sys
import os
from datetime import datetime

ESCALATION_TRIGGERS = [
    "critical_security",
    "legal_block",
    "test_failures",
    "acceptance_block",
    "budget_exceeded",
    "human_required",
    "ambiguous_requirement"
]

try:
    input_data = json.load(sys.stdin)
except (json.JSONDecodeError, Exception):
    sys.exit(0)

notification_type = input_data.get("type", "")
message = input_data.get("message", "").lower()

project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
escalation_file = os.path.join(project_dir, ".claude/escalations.json")
state_file = os.path.join(project_dir, ".claude/workflow-state.json")

# Load existing escalations
escalations = []
if os.path.exists(escalation_file):
    try:
        with open(escalation_file) as f:
            escalations = json.load(f)
    except Exception:
        pass

# Determine escalation level
escalation_level = "info"
for trigger in ESCALATION_TRIGGERS:
    if trigger.replace("_", " ") in message or trigger in message:
        escalation_level = "critical" if "critical" in trigger or "block" in trigger else "warning"
        break

# Check for security or legal keywords
if any(word in message for word in ["vulnerability", "exploit", "injection", "xss"]):
    escalation_level = "critical"
if any(word in message for word in ["license", "gdpr", "compliance", "legal"]):
    escalation_level = "warning"

escalation = {
    "id": len(escalations),
    "timestamp": datetime.now().isoformat(),
    "type": notification_type,
    "message": input_data.get("message", ""),
    "level": escalation_level,
    "resolved": False
}

escalations.append(escalation)

try:
    with open(escalation_file, 'w') as f:
        json.dump(escalations, f, indent=2)
except Exception:
    pass

# For critical escalations, update workflow state
if escalation_level == "critical":
    state = {}
    if os.path.exists(state_file):
        try:
            with open(state_file) as f:
                state = json.load(f)
        except Exception:
            pass

    state.setdefault("blockers", []).append({
        "escalation_id": escalation["id"],
        "reason": input_data.get("message", ""),
        "at": datetime.now().isoformat()
    })

    try:
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass

sys.exit(0)
