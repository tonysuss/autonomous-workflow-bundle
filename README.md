# Autonomous Workflow Bundle

<p align="center">
  <img src="assets/cover.svg" alt="Autonomous Workflow Bundle" width="800">
</p>

<p align="center">
  <strong>Portable Claude Code configuration for autonomous PRD-to-implementation workflows</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Claude_Code-Compatible-5A45FF?style=flat-square" alt="Claude Code">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-lightgrey?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License">
</p>

---

A complete `.claude` configuration bundle that transforms Claude Code into an autonomous software development agent. Drop it into any project to enable PRD-driven workflows with built-in security gates, quality checks, and stage-based orchestration.

## Installation

```bash
# Clone the bundle
git clone https://github.com/YOUR_USERNAME/autonomous-workflow-bundle.git

# Copy to your project (rename to .claude)
cp -r autonomous-workflow-bundle/claude-bundle /path/to/your/project/.claude
```

## Contents
- `claude-bundle/agents` — stage playbooks
- `claude-bundle/hooks` — routing/commands/validation/checkpoints
- `claude-bundle/skills` — project skills + bundled globals (`ios-simulator-skill`, `webapp-testing`, `frontend-design`, `web-artifacts-builder`, `gemini-imagegen`)
- `claude-bundle/settings.json` — hook wiring
- `claude-bundle/settings.local.json` — local permissions template
- `claude-bundle/workflow-state.json` — sanitized for a fresh start
- `claude-bundle/checkpoints/.gitkeep` — keeps the folder when zipped

## Workflow at a glance
Stage flow: PRD Analysis → Plan Generation → Security/Legal → Implementation → Testing → Completion → Done  
Agent mapping:
- PRD Analysis: `prd-analyzer`
- Plan Generation: `plan-architect`
- Security/Legal: `security-auditor` + `legal-reviewer` (both must succeed before moving on)
- Implementation: `code-implementer`, `asset-builder`
- Testing: `test-runner-fixer`, `acceptance-validator`
- Completion: `doc-writer`

## Prereqs (not bundled)
- Claude plugins enabled in the user environment: `context7`, `frontend-design`, `swift-lsp`, `pyright-lsp`, `typescript-lsp`, `ralph-wiggum`, `feature-dev`, `code-review`, `security-guidance`.
- Optional MCP servers: `supabase` is enabled in `settings.local.json`; remove/disable if unavailable.
- Tooling: node/npm (for format/test hooks), Python 3 (hooks), Xcode/xcodebuild for iOS flows, plus any stack-specific runtimes your project needs.
- Env vars (optional):
  - `CLAUDE_PROJECT_DIR` if the bundle isn’t placed at project root.
  - `GEMINI_API_KEY` to enable `gemini-imagegen`.
  - Any MCP server auth vars (e.g., Supabase) if you keep those enabled.

Skill → plugin hints (enable the plugin if you need the capability):
- `workflow-orchestrator`, `implementation-executor`, `validation-testing`: benefit from `context7` docs lookup
- `frontend-design`, `web-artifacts-builder`, `webapp-testing`: benefit from `frontend-design`/web tooling
- `ios-simulator-skill`: needs Xcode; `swift-lsp` helps for Swift projects

## Usage
1. Copy `claude-bundle` to your project root as `.claude` (see Installation above).
2. Adjust `.claude/settings.local.json` for permissions/MCP servers as needed.
3. Start a workflow: `workflow start <path-to-prd>`. This initializes state at `prd_analysis`.
4. Check status: `workflow status`. Resume: `workflow resume`. Stage transitions occur on agent completions via `subagent-result-processor.py`.
5. Fully autonomous loop (optional): `/ralph-loop Start autonomous workflow with PRD at <path>` if you have the `ralph-wiggum` plugin enabled.

## Artifacts produced
During workflow execution, the following files are created in your project's `.claude/`:
- `requirements.json` — parsed PRD with features and acceptance criteria (after PRD Analysis)
- `implementation-plan.json` — task graph with file structure and dependencies (after Plan Generation)
- `workflow-state.json` — current stage, progress, and agent results (updated continuously)
- `checkpoints/` — session checkpoints for resuming interrupted workflows

## Notes
- No active workflow is included; state is reset.
- If plugins/MCP servers aren't available on the target machine, disable the entries in `settings.local.json`/`settings.json` and proceed without them.
- Security/legal gate: Stage 3 only advances after both `security-auditor` and `legal-reviewer` succeed.

## Troubleshooting
- **Command not found / missing plugin**: Enable it with `claude plugins enable <plugin>@claude-plugins-official`, or disable in `settings.local.json`.
- **Stuck stage**: Ensure the corresponding agent completed successfully; stage advances only on `subagent-result-processor.py` success.
- **Permissions prompt**: Tighten or relax `settings.local.json` allowlist as needed.
