#!/usr/bin/env python3
"""
Stage gate validation functions.
Each gate returns (passed: bool, reason: str).
Gates can be configured to block or warn via WORKFLOW_GATE_MODE env var.
"""
import os
import json


def load_json(path):
    """Load JSON file, return empty dict on failure."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def gate_prd_to_plan(project_dir):
    """Stage 1 -> 2: requirements.json must exist with features."""
    req_file = os.path.join(project_dir, ".claude/requirements.json")
    req = load_json(req_file)
    features = req.get("features", [])
    if not features:
        return False, "requirements.json missing or has no features"
    return True, f"PRD analysis complete: {len(features)} features extracted"


def gate_plan_to_review(project_dir):
    """Stage 2 -> 3: implementation-plan.json must exist with tasks."""
    plan_file = os.path.join(project_dir, ".claude/implementation-plan.json")
    plan = load_json(plan_file)
    tasks = plan.get("tasks", [])
    files = plan.get("file_structure", {}).get("files", [])
    if not tasks and not files:
        return False, "implementation-plan.json missing or has no tasks/files"
    return True, f"Plan complete: {len(tasks)} tasks, {len(files)} files planned"


def gate_review_to_impl(project_dir):
    """Stage 3 -> 4: Both security and legal agents must have succeeded."""
    state_file = os.path.join(project_dir, ".claude/workflow-state.json")
    state = load_json(state_file)
    results = state.get("agent_results", {})

    security_ok = results.get("security-auditor", {}).get("success", False)
    legal_ok = results.get("legal-reviewer", {}).get("success", False)

    if not security_ok:
        return False, "security-auditor has not approved"
    if not legal_ok:
        return False, "legal-reviewer has not approved"
    return True, "Security and legal review passed"


def normalize_path(path):
    """Normalize a path for comparison (resolve .., ., trailing slashes)."""
    # Expand user home and env vars, then normalize
    expanded = os.path.expanduser(os.path.expandvars(path))
    # Use normpath to resolve .. and . and normalize slashes
    return os.path.normpath(expanded)


def gate_impl_to_testing(project_dir):
    """Stage 4 -> 5: 100% of planned files created or modified."""
    plan_file = os.path.join(project_dir, ".claude/implementation-plan.json")
    state_file = os.path.join(project_dir, ".claude/workflow-state.json")

    plan = load_json(plan_file)
    state = load_json(state_file)

    planned_files = plan.get("file_structure", {}).get("files", [])
    created_files = state.get("files_created", [])
    modified_files = state.get("files_modified", [])

    if not planned_files:
        # No plan means we can't validate; allow transition
        return True, "No file plan to validate against"

    # Extract and normalize paths from planned files
    planned_paths = set()
    for f in planned_files:
        if isinstance(f, dict):
            path = f.get("path", "")
        else:
            path = str(f)
        if path:
            planned_paths.add(normalize_path(path))

    if not planned_paths:
        return True, "No specific files in plan"

    # Normalize all touched files for comparison
    all_touched_normalized = set()
    for f in created_files:
        all_touched_normalized.add(normalize_path(f))
    for f in modified_files:
        all_touched_normalized.add(normalize_path(f))

    # Match by normalized path (exact match after normalization)
    matched = 0
    for planned in planned_paths:
        # Check if any touched file's normalized path matches or ends with the planned path
        # This handles cases where planned is relative and touched is absolute
        for touched in all_touched_normalized:
            if touched == planned or touched.endswith(os.sep + planned):
                matched += 1
                break

    percentage = (matched / len(planned_paths)) * 100 if planned_paths else 100

    if percentage < 100:
        return False, f"Only {percentage:.0f}% of planned files completed ({matched}/{len(planned_paths)})"

    return True, f"{percentage:.0f}% of planned files completed ({matched} created/modified)"


def gate_testing_to_completion(project_dir):
    """Stage 5 -> 6: Tests pass with 80% coverage and acceptance validation."""
    state_file = os.path.join(project_dir, ".claude/workflow-state.json")
    validation_file = os.path.join(project_dir, ".claude/validation-report.json")

    state = load_json(state_file)
    validation = load_json(validation_file)
    results = state.get("agent_results", {})

    # Require both test-runner-fixer and acceptance-validator to have succeeded
    test_ok = results.get("test-runner-fixer", {}).get("success", False)
    acceptance_ok = results.get("acceptance-validator", {}).get("success", False)

    if not test_ok:
        return False, "test-runner-fixer has not succeeded"
    if not acceptance_ok:
        return False, "acceptance-validator has not succeeded"

    # Require validation report to verify coverage (no bypass allowed)
    if not validation:
        return False, "validation-report.json missing - cannot verify 80% coverage requirement"

    tests_passed = validation.get("tests_passed", 0)
    tests_total = validation.get("tests_total", 0)
    coverage = validation.get("coverage_percent", 0)

    # Check pass rate - all tests must pass
    if tests_total > 0:
        pass_rate = (tests_passed / tests_total) * 100
        if pass_rate < 100:
            return False, f"Only {pass_rate:.0f}% of tests passing ({tests_passed}/{tests_total})"

    # Enforce 80% coverage threshold
    if coverage < 80:
        return False, f"Coverage {coverage}% is below 80% threshold"

    return True, f"Tests pass: {tests_passed}/{tests_total}, coverage: {coverage}%"


# Map of (from_stage, to_stage) -> gate function
STAGE_GATES = {
    ("prd_analysis", "plan_generation"): gate_prd_to_plan,
    ("plan_generation", "security_legal_review"): gate_plan_to_review,
    ("security_legal_review", "implementation"): gate_review_to_impl,
    ("implementation", "testing"): gate_impl_to_testing,
    ("testing", "completion"): gate_testing_to_completion,
}


def validate_transition(from_stage, to_stage, project_dir):
    """
    Check if transition from from_stage to to_stage is allowed.
    Returns (passed: bool, reason: str).
    """
    gate_fn = STAGE_GATES.get((from_stage, to_stage))
    if gate_fn is None:
        return True, f"No gate defined for {from_stage} -> {to_stage}"
    return gate_fn(project_dir)


def get_gate_mode():
    """
    Get gate enforcement mode from environment.
    Returns 'strict' (block on failure) or 'warn' (log but allow).
    Invalid values default to 'strict' for safety.
    """
    mode = os.environ.get("WORKFLOW_GATE_MODE", "strict").lower()
    if mode not in ("strict", "warn"):
        mode = "strict"  # Default to safe behavior for unknown values
    return mode
