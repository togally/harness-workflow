---
name: harness-ff
description: "Use when the user wants `harness ff` or equivalent intent. Read workflow state first, then route into the main harness skill."
---

# Harness Ff

This is a thin wrapper skill for `harness ff`.

## Hard Gate

Do not act until `WORKFLOW.md`, `.workflow/context/index.md`, and `.workflow/state/runtime.yaml` have been read.
If any of those files are missing, inconsistent, or unreadable, stop immediately and do not fall back to a legacy entrypoint.

Before acting:

1. Read the root `WORKFLOW.md`
2. Read `.workflow/context/index.md` and `.workflow/state/runtime.yaml`
3. Load the matching role / experience / constraint files by following `.workflow/context/index.md`, then read the root `AGENTS.md` and the main harness skill at `.codex/skills/harness/SKILL.md`

Rules:

- treat `harness ff` as the primary action
- do not improvise a parallel workflow
- when entering a new node, switching submodules, or nearing context limits, run a context-maintenance check first; prefer `/clear` for irrelevant context and `/compact` for still-relevant but compressible context
- if state is missing or inconsistent, stop and tell the user to run `harness requirement "<title>"`
- if the global `harness` CLI is unavailable, fall back to `.codex/skills/harness/scripts/harness.py`
