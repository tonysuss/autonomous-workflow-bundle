---
name: prd-processor
description: Processes PRD documents into structured requirements. Use when analyzing product requirements, extracting features, or defining acceptance criteria from specification documents.
---

# PRD Processor

Specialized skill for analyzing and structuring PRD documents.

## Process

1. **Parse Document Structure**
   - Identify sections (Executive Summary, Features, Requirements)
   - Extract headings and subheadings
   - Map document hierarchy

2. **Extract Features**
   - Feature name and description
   - User stories (As a..., I want..., So that...)
   - Priority level (P0/P1/P2/P3)
   - Dependencies on other features

3. **Define Acceptance Criteria**
   - Functional criteria (what it must do)
   - Non-functional criteria (performance, security)
   - Testable assertions (Given/When/Then format)

4. **Identify Technical Requirements**
   - Technology stack constraints
   - Integration requirements
   - API specifications
   - Database needs

5. **Risk Assessment**
   - Technical complexity
   - Dependency risks
   - Resource constraints

## Output

Save to `.claude/requirements.json` with structure defined in prd-analyzer agent.

## Quality Standards

- Every feature must have at least one acceptance criterion
- All acceptance criteria must be testable
- Technical requirements must be specific and measurable
