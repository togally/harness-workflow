---
name: harness
description: "Use when Codex, Claude Code, or Qoder needs to operate a repository with the current Harness workflow rooted at WORKFLOW.md and .workflow/state/runtime.yaml."
---

# Harness Workflow

## Overview

Harness is a structured workflow system for managing software development tasks. All harness commands are routed through the **harness-manager** role, which serves as the command guiding center.

The source of truth is:

1. `WORKFLOW.md`
2. `.workflow/context/index.md`
3. `.workflow/state/runtime.yaml`

## Hard Gate

Do not act until `WORKFLOW.md`, `.workflow/context/index.md`, and `.workflow/state/runtime.yaml` have been read.

If any of those files are missing, inconsistent, or unreadable, stop immediately and do not fall back to a legacy entrypoint.

## Command Guiding Center (harness-manager)

The harness-manager role is the unified entry point for all harness commands:

1. **Command Understanding Layer**: Parses `harness <command>` intent
2. **Role Scheduling Layer**: Dispatches to appropriate subagents
3. **Project Insight Layer**: Scans project characteristics
4. **Tools Integration**: Delegates to toolsManager for tool recommendations

## Command Categories

### Installation & Update (harness-manager executes directly)
- `harness install` — Initialize repository + refresh all managed files (已吸收原 update 刷新职责；req-33 / chg-01)
- `harness install --agent <agent>` — Install to specific agent
- `harness update` — 触发 project-reporter 生成 `artifacts/main/project-overview.md`（CLI 打印引导 + exit 0；语义详见 harness-manager.md §A.3；req-33 / chg-02）
- `harness update --check` — 同 `harness update`（flag 不报错，handler 忽略）
- `harness update --scan` — 同 `harness update`（如需扫描报告请用 `harness install` 或在会话中触发 project-reporter）
- `harness language <english|cn>` — Set language

### Session Control (technical-director executes)
- `harness enter [req-id]` — Enter workflow mode
- `harness exit` — Exit workflow mode
- `harness status` — Show current status
- `harness validate` — Validate artifacts

### Workflow Progression (technical-director executes)
- `harness next [--execute]` — Advance to next stage
- `harness ff` — Fast-forward to execution

### Artifact Management (stage roles execute)
- `harness requirement <title>` — Create requirement
- `harness change <title>` — Create change
- `harness bugfix <title>` — Create bugfix
- `harness archive [req-id]` — Archive requirement
- `harness rename <kind> <old> <new>` — Rename artifact

### Auxiliary Functions (respective roles execute)
- `harness suggest [content]` — Manage suggestions
- `harness tool-search <keywords...>` — Search tools
- `harness tool-rate <tool-id> <rating>` — Rate tool
- `harness regression [issue]` — Diagnose issues
- `harness feedback [--reset]` — Export feedback

## Routing Rules

- Prefer the global `harness` CLI when available
- If the human is unhappy with a completed result, start `harness regression "<issue>"` first
- If `conversation_mode: harness`, stay inside the locked requirement and stage until the human explicitly exits
- If `.workflow/state/runtime.yaml` is missing or inconsistent, repair it instead of improvising a parallel workflow
- Do not treat `.workflow/context/rules/workflow-runtime.yaml` as the primary entrypoint

## Stage Flow

```
requirement_review → planning → executing → testing → acceptance → done
                           ↓
                     regression (when needed)
```

## Install / Update Expectations（req-33 / chg-01 + chg-02 重定义后）

`harness install` should (has absorbed former `update` responsibilities; req-33 / chg-01):

- create `WORKFLOW.md`
- create `.workflow/state/runtime.yaml`
- create the role / constraint / evaluation docs referenced by `.workflow/context/index.md`
- refresh managed skill files (`.codex|.claude|.qoder/skills/harness`)
- refresh `.workflow/context/project-profile.md` via `_write_project_profile_if_changed`
- migrate legacy `.harness/feedback.jsonl` and state schema (idempotent on re-run)
- keep root guides thin and route them back to `WORKFLOW.md`
- avoid restoring legacy entrypoints such as `.workflow/context/rules/workflow-runtime.yaml`

`harness update` is a **role-contract trigger** (req-33 / chg-02): its CLI prints guidance + exits 0; the real semantics is "project-reporter generates `artifacts/main/project-overview.md`" invoked by harness-manager when the user utters a §3.5.1 trigger phrase in conversation.

## Validation

After installing or updating the workflow, verify the repository structure with:

```bash
python3 tools/lint_harness_repo.py --root . --strict-claude --strict-stage-roles
```

## SOP Compliance

All stage roles have mandatory SOPs defined in role files. **Hard Gates are BINDING - violating a Hard Gate = immediate stop.**

### Your Role's SOP
When you execute a stage, you MUST read and follow the SOP in your role file:
- **requirement_review**: `requirement-review.md` — Define background, goal, scope, acceptance criteria
- **planning**: `planning.md` — Split changes, create `change.md` + `plan.md`
- **executing**: `executing.md` — Execute plan.md steps, mark each as ✅
- **testing**: `testing.md` — Design and run tests
- **acceptance**: `acceptance.md` — Verify against requirement.md
- **regression**: `regression.md` — Diagnose and confirm problem

### What This Prevents
- Skipping SOP steps
- Claiming completion without following the process
- Bypassing Hard Gates

### SOP Execution Requirements
1. Read your role file before starting
2. Follow the SOP steps in order
3. Mark each step as ✅ when completed
4. Check exit conditions before reporting completion

## Fallback

If the global `harness` CLI is unavailable, the local script at `.codex/skills/harness/scripts/harness.py` may be used as a thin fallback entrypoint.
