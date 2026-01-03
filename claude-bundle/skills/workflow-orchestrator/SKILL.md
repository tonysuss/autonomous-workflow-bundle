---
name: workflow-orchestrator
description: Orchestrates autonomous PRD-to-implementation workflows. Use when processing PRDs, managing implementation progress, or coordinating multi-stage development pipelines. Triggers on "workflow start", "workflow status", "workflow resume", or autonomous development requests.
---

# Autonomous Workflow Orchestrator

Manages the 6-stage autonomous development pipeline from PRD to completed project.

## Workflow Stages

```
Stage 1: PRD Analysis      → prd-analyzer agent
Stage 2: Plan Generation   → plan-architect agent
Stage 3: Security/Legal    → security-auditor + legal-reviewer (parallel)
Stage 4: Implementation    → code-implementer + asset-builder
Stage 5: Testing           → test-runner-fixer + acceptance-validator
Stage 6: Completion        → doc-writer
```

## Commands

### Start New Workflow
```
workflow start <prd-path>
```
Initializes workflow state and begins Stage 1.

### Check Status
```
workflow status
```
Shows current stage, progress, and next action.

### Resume Workflow
```
workflow resume
```
Continues from last checkpoint.

## State Management

Read/update `.claude/workflow-state.json`:

```json
{
  "workflow_id": "uuid",
  "prd_path": "path/to/prd.md",
  "current_stage": "implementation",
  "stage_status": {
    "prd_analysis": "completed",
    "plan_generation": "completed",
    "security_legal_review": "completed",
    "implementation": "in_progress",
    "testing": "pending",
    "completion": "pending"
  },
  "progress_percent": 45,
  "current_task": "T-015",
  "last_activity": "ISO-8601",
  "files_created": [],
  "files_modified": [],
  "blockers": [],
  "escalations": []
}
```

## Stage Transitions

### Stage 1 → Stage 2
When `.claude/requirements.json` is created with all features extracted.

### Stage 2 → Stage 3
When `.claude/implementation-plan.json` is created with task graph.

### Stage 3 → Stage 4
When security-auditor AND legal-reviewer both approve.

### Stage 4 → Stage 5
When 80% of planned files are created or modified (normalized path matching).

### Stage 5 → Stage 6
When both test-runner-fixer AND acceptance-validator succeed, validation-report.json exists, all tests pass, and 80% coverage threshold is met.

### Stage 6 → Done
When documentation is complete.

## Escalation Handling

Pause workflow and notify human when:
- Critical security vulnerability found
- Legal/license incompatibility detected
- >30% test failures after 3 fix attempts
- Ambiguous requirement blocks progress

## Ralph-Wiggum Integration

For fully autonomous execution, use:
```
/ralph-loop Start autonomous workflow with PRD at <path>
```

This runs the workflow in a continuous loop until completion or escalation. The hook pulls the PRD path from the text after `PRD at` and hands it to `workflow start` so the loop begins at Stage 1.

## Skill Integration

| Stage | Skills Used |
|-------|-------------|
| Stage 4 | `frontend-design`, `web-artifacts-builder`, `gemini-imagegen` |
| Stage 5 | `webapp-testing`, `ios-simulator-skill` |

## Context7 Integration

During implementation, query library docs:
```
mcp__plugin_context7_context7__resolve-library-id
mcp__plugin_context7_context7__query-docs
```
