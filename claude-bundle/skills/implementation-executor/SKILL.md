---
name: implementation-executor
description: Executes implementation plans by creating files, writing code, and building assets. Use during the implementation phase of autonomous workflows or when executing planned development tasks.
---

# Implementation Executor

Executes approved implementation plans systematically.

## Process

1. **Load Plan**
   - Read `.claude/implementation-plan.json`
   - Identify current phase and task
   - Check dependencies are satisfied

2. **Create File Structure**
   - Create directories first
   - Follow planned file hierarchy

3. **Implement Features**
   For each task:
   - Query Context7 for library docs if needed
   - Write code following project patterns
   - Add inline documentation
   - Run local validation

4. **Track Progress**
   After each file, update `.claude/workflow-state.json`

## Skill Integration

- Use `frontend-design` for UI components
- Use `web-artifacts-builder` for React artifacts
- Use `gemini-imagegen` for visual assets

## Context7 Usage

```
# Find library
mcp__plugin_context7_context7__resolve-library-id(libraryName="flutter", query="...")

# Get docs
mcp__plugin_context7_context7__query-docs(libraryId="/flutter/flutter", query="...")
```

## Code Quality

- Follow existing project conventions
- Maintain type safety
- Handle errors gracefully
- No hardcoded secrets
- Write self-documenting code
