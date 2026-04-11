---
name: harness-change
description: "Use when the user wants `harness change` or equivalent intent. Read workflow state first, then route into the main harness skill."
---

# Harness Change

This is a thin wrapper skill for `harness change`.

Before acting:

1. Read `workflow/context/rules/workflow-runtime.yaml`
2. Use `current_version` to read the active version `meta.yaml`
3. Then read `workflow/context/hooks/README.md`, the hook doc for the current timing, the root `AGENTS.md`, and the main harness skill at `.codex/skills/harness/SKILL.md`

Rules:

- treat `harness change` as the primary action
- do not improvise a parallel workflow
- when entering a new node, switching submodules, or nearing context limits, run a context-maintenance check first; prefer `/clear` for irrelevant context and `/compact` for still-relevant but compressible context
- if state is missing or inconsistent, stop and tell the user to run `harness active "<version>"`
- if the global `harness` CLI is unavailable, fall back to `.codex/skills/harness/scripts/harness.py`

Focus:

- decide whether this change belongs to a requirement or stands alone
- after creating the change, fill in intent, impact scope, risk points, and acceptance method first
- remind the user that every completed change must include `mvn compile`
- once the change is clear, point to `harness plan` or `harness next`
