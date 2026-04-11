---
name: harness-regression
description: "Use when the user wants `harness regression` or equivalent intent. Read workflow state first, then route into the main harness skill."
---

# Harness Regression

This is a thin wrapper skill for `harness regression`.

Before acting:

1. Read `workflow/context/rules/workflow-runtime.yaml`
2. Use `current_version` to read the active version `meta.yaml`
3. Then read `workflow/context/hooks/README.md`, the hook doc for the current timing, the root `AGENTS.md`, and the main harness skill at `.codex/skills/harness/SKILL.md`

Rules:

- treat `harness regression` as the primary action
- do not improvise a parallel workflow
- when entering a new node, switching submodules, or nearing context limits, run a context-maintenance check first; prefer `/clear` for irrelevant context and `/compact` for still-relevant but compressible context
- if state is missing or inconsistent, stop and tell the user to run `harness active "<version>"`
- if the global `harness` CLI is unavailable, fall back to `.codex/skills/harness/scripts/harness.py`

Focus:

- do not jump straight into rework; confirm whether it is a real problem first
- use locally available logs, compile output, and test failures before asking the human
- if human-provided external input is still needed, fill `regression/required-inputs.md` first
- only after confirmation should the regression become a new requirement update or change
