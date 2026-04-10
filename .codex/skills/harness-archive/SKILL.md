---
name: harness-archive
description: "Use when the user wants `harness archive` or equivalent intent. Read workflow state first, then route into the main harness skill."
---

# Harness Archive

This is a thin wrapper skill for `harness archive`.

Before acting:

1. Read `docs/context/rules/workflow-runtime.yaml`
2. Use `current_version` to read the active version `meta.yaml`
3. Then read `docs/context/hooks/README.md`, the hook doc for the current timing, the root `AGENTS.md`, and the main harness skill at `.codex/skills/harness/SKILL.md`

Rules:

- treat `harness archive` as the primary action
- do not improvise a parallel workflow
- if state is missing or inconsistent, stop and tell the user to run `harness active "<version>"`
- if the global `harness` CLI is unavailable, fall back to `.codex/skills/harness/scripts/harness.py`
