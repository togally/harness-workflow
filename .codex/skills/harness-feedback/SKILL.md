---
name: harness-feedback
description: "Use when the user wants `harness feedback` or equivalent intent. Exports the feedback event summary from the current repository."
---

# Harness Feedback

This is a thin wrapper skill for `harness feedback`.

## Hard Gate

Do not act until `WORKFLOW.md`, `.workflow/context/index.md`, and `.workflow/state/runtime.yaml` have been read.
If any of those files are missing, inconsistent, or unreadable, stop immediately and do not fall back to a legacy entrypoint.

Before acting:

1. Read the root `WORKFLOW.md`
2. Read `.workflow/context/index.md` and `.workflow/state/runtime.yaml`
3. Load the matching role / experience / constraint files by following `.workflow/context/index.md`, then read the root `AGENTS.md` and the main harness skill at `.codex/skills/harness/SKILL.md`

Rules:

- treat `harness feedback` as the primary action
- do not improvise a parallel workflow
- if state is missing or inconsistent, stop and tell the user to run `harness requirement "<title>"`
- if the global `harness` CLI is unavailable, fall back to `.codex/skills/harness/scripts/harness.py`

Focus:

- export the feedback event summary from the current repository
- pass `--reset` to clear the feedback log after export
- this command has no workflow stage semantics; it can be run at any stage
