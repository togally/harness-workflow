---
name: harness-requirement
description: "Use when the user wants `harness requirement` or equivalent intent. Read workflow state first, then route into the main harness skill."
---

# Harness Requirement

This is a thin wrapper skill for `harness requirement`.

Before acting:

1. Read `docs/context/rules/workflow-runtime.yaml`
2. Use `current_version` to read the active version `meta.yaml`
3. Then read `docs/context/hooks/README.md`, the hook doc for the current timing, the root `AGENTS.md`, and the main harness skill at `.codex/skills/harness/SKILL.md`

Rules:

- treat `harness requirement` as the primary action
- do not improvise a parallel workflow
- if state is missing or inconsistent, stop and tell the user to run `harness active "<version>"`
- if the global `harness` CLI is unavailable, fall back to `.codex/skills/harness/scripts/harness.py`

Focus:

- confirm there is an active version first; if not, guide the user to `harness version` or `harness active`
- after creating the requirement, fill in background, goal, scope, and acceptance boundaries first
- do not jump into implementation; discuss whether the requirement is correct
- once the requirement is approved, point to splitting changes or running `harness next`
