---
name: harness-next
description: "Use when the user wants `harness next` or equivalent intent. Read workflow state first, then route into the main harness skill."
---

# Harness Next

This is a thin wrapper skill for `harness next`.

Before acting:

1. Read `workflow/context/rules/workflow-runtime.yaml`
2. Use `current_version` to read the active version `meta.yaml`
3. Then read `workflow/context/hooks/README.md`, the hook doc for the current timing, the root `AGENTS.md`, and the main harness skill at `.codex/skills/harness/SKILL.md`

Rules:

- treat `harness next` as the primary action
- do not improvise a parallel workflow
- when entering a new node, switching submodules, or nearing context limits, run a context-maintenance check first; prefer `/clear` for irrelevant context and `/compact` for still-relevant but compressible context
- if state is missing or inconsistent, stop and tell the user to run `harness active "<version>"`
- if the global `harness` CLI is unavailable, fall back to `.codex/skills/harness/scripts/harness.py`

Focus:

- explain the current stage, current task, and next action first
- then advance according to the actual state instead of assuming a fixed sequence
- if the version is already `ready_for_execution`, do not start implementation automatically; ask for confirmation or use `harness next --execute`
- if workflow state is incomplete, stop and require state repair first
