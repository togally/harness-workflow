---
name: harness-exit
description: "Use when the user wants `harness exit` or equivalent intent. Read workflow state first, then route into the main harness skill."
---

# Harness Exit

This is a thin wrapper skill for `harness exit`.

Before acting:

1. Read `docs/context/rules/workflow-runtime.yaml`
2. Use `current_version` to read the active version `meta.yaml`
3. Then read `docs/context/hooks/README.md`, the hook doc for the current timing, the root `AGENTS.md`, and the main harness skill at `.codex/skills/harness/SKILL.md`

Rules:

- treat `harness exit` as the primary action
- do not improvise a parallel workflow
- if state is missing or inconsistent, stop and tell the user to run `harness active "<version>"`
- if the global `harness` CLI is unavailable, fall back to `.codex/skills/harness/scripts/harness.py`

Focus:

- leave harness conversation mode cleanly
- once exited, do not keep enforcing the current harness node as the only valid context
- do not mutate requirement, change, plan, or runtime stage beyond clearing the conversation lock
