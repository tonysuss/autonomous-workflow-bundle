---
name: validation-testing
description: Validates implementations against acceptance criteria and runs comprehensive tests. Use during testing and validation phases or when verifying feature completeness.
---

# Validation and Testing

Comprehensive validation against acceptance criteria.

## Process

1. **Load Acceptance Criteria**
   - Read from `.claude/requirements.json`
   - Map criteria to implemented features

2. **Run Automated Tests**
   ```bash
   npm test              # Unit tests
   npm run test:integration  # Integration tests
   npm run test:e2e      # E2E tests (if applicable)
   ```

3. **Validate Each Criterion**
   - Identify validation method
   - Execute validation
   - Record result with evidence

4. **Generate Report**
   Save to `.claude/validation-report.json`

## Skill Integration

### Web UI Testing
Use `webapp-testing` skill:
```bash
python scripts/with_server.py --server "npm run dev" --port 5173 -- python test_script.py
```

### iOS Testing
Use `ios-simulator-skill`:
- Boot simulator
- Install and launch app
- Run UI automation scripts

## Acceptance Threshold

- All P0 criteria must pass
- 80% of P1 criteria must pass
- Test coverage >= 80%
- No critical security issues

## Remediation

For failures (max 3 attempts):
1. Analyze root cause
2. Create fix task
3. Invoke debugger or code-implementer
4. Re-validate
5. Escalate if still failing
