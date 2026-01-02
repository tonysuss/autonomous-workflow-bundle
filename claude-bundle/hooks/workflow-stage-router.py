#!/usr/bin/env python3
"""Routes user prompts to appropriate workflow stage and sub-agents."""
import json
import sys
import os

STAGE_KEYWORDS = {
    "prd_analysis": ["prd", "requirements", "spec", "analyze", "extract"],
    "plan_generation": ["plan", "architect", "design", "structure"],
    "security_legal_review": ["security", "legal", "review", "audit", "compliance"],
    "implementation": ["implement", "build", "code", "create", "develop"],
    "testing": ["test", "validate", "verify", "check"],
    "completion": ["document", "finish", "complete", "deploy", "handoff"]
}

STAGE_AGENTS = {
    "prd_analysis": ["prd-analyzer"],
    "plan_generation": ["plan-architect"],
    "security_legal_review": ["security-auditor", "legal-reviewer"],
    "implementation": ["code-implementer", "asset-builder"],
    "testing": ["test-runner-fixer", "acceptance-validator"],
    "completion": ["doc-writer"]
}

try:
    input_data = json.load(sys.stdin)
except (json.JSONDecodeError, Exception):
    sys.exit(0)

prompt = input_data.get("prompt", "").lower()

# Load current state
project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
state_file = os.path.join(project_dir, ".claude/workflow-state.json")
current_stage = "prd_analysis"

if os.path.exists(state_file):
    try:
        with open(state_file) as f:
            state = json.load(f)
            current_stage = state.get("current_stage", "prd_analysis")
    except Exception:
        pass

# Determine if stage transition is needed
detected_stage = None
for stage, keywords in STAGE_KEYWORDS.items():
    if any(kw in prompt for kw in keywords):
        detected_stage = stage
        break

# Suggest appropriate agents
suggested_agents = STAGE_AGENTS.get(detected_stage or current_stage, [])

output = {
    "hookSpecificOutput": {
        "currentStage": current_stage,
        "detectedStage": detected_stage,
        "suggestedAgents": suggested_agents
    }
}

print(json.dumps(output))
sys.exit(0)
