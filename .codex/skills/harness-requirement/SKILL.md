---
name: harness-requirement
description: "Use when the user wants `harness requirement` or equivalent intent. Read workflow state first, then route into the main harness skill."
---

# Harness Requirement

This is a thin wrapper skill for `harness requirement`.

## Hard Gate

Do not act until `WORKFLOW.md`, `.workflow/context/index.md`, and `.workflow/state/runtime.yaml` have been read.
If any of those files are missing, inconsistent, or unreadable, stop immediately and do not fall back to a legacy entrypoint.

Before acting:

1. Read the root `WORKFLOW.md`
2. Read `.workflow/context/index.md` and `.workflow/state/runtime.yaml`
3. Load the matching role / experience / constraint files by following `.workflow/context/index.md`, then read the root `AGENTS.md` and the main harness skill at `.codex/skills/harness/SKILL.md`

Rules:

- treat `harness requirement` as the primary action
- do not improvise a parallel workflow
- when entering a new node, switching submodules, or nearing context limits, run a context-maintenance check first; prefer `/clear` for irrelevant context and `/compact` for still-relevant but compressible context
- if state is missing or inconsistent, stop and tell the user to run `harness requirement "<title>"`
- if the global `harness` CLI is unavailable, fall back to `.codex/skills/harness/scripts/harness.py`

Focus:

- confirm there is an active version first; if not, guide the user to `harness version` or `harness active`
- after creating the requirement, fill in background, goal, scope, and acceptance boundaries first
- do not jump into implementation; discuss whether the requirement is correct
- once the requirement is approved, point to splitting changes or running `harness next`
