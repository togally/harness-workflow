---
name: harness
description: "Use when Codex, Claude Code, or Qoder needs to operate a repository with the current Harness workflow rooted at WORKFLOW.md and`.workflow/state/runtime.yaml."
---

# Harness

## Overview

Operate the repository from the workflow entrypoint, not from ad-hoc chat and not from legacy version-flow files.

The source of truth is:

1. `WORKFLOW.md`
2. `.workflow/context/index.md`
3. `.workflow/state/runtime.yaml`

Load any additional role, experience, and constraint files by following `.workflow/context/index.md`.

## Hard Gate

Do not act until `WORKFLOW.md`, `.workflow/context/index.md`, and `.workflow/state/runtime.yaml` have been read.

If any of those files are missing, inconsistent, or unreadable, stop immediately and do not fall back to a legacy entrypoint.

## Command Model

Use these commands conceptually:

1. `harness install`
   Install local skills and scaffold the current workflow entry files.
2. `harness update`
   Refresh harness-managed files without restoring legacy entrypoints.
3. `harness status`
   Show the current requirement, stage, and routing state from `.workflow/state/runtime.yaml`.
4. `harness requirement <title>`
   Create and route into a requirement workspace.
5. `harness change <title>`
   Create one concrete change under the active requirement.
6. `harness next`
   Advance the current requirement through the next stage.
7. `harness regression <issue>`
   Diagnose dissatisfaction or failures before creating new work.

## Routing Rules

- Prefer the global `harness` CLI when available.
- Do not treat `.workflow/context/rules/workflow-runtime.yaml` as the primary entrypoint.
- If the human is unhappy with a completed result, start `harness regression "<issue>"` first.
- If `conversation_mode: harness`, stay inside the locked requirement and stage until the human explicitly exits.
- If `.workflow/state/runtime.yaml` is missing or inconsistent, repair it instead of improvising a parallel workflow.

## Install / Update Expectations

`harness install` and `harness update` should:

- create `WORKFLOW.md`
- create `.workflow/state/runtime.yaml`
- create the role / constraint / evaluation docs referenced by `.workflow/context/index.md`
- keep root guides thin and route them back to `WORKFLOW.md`
- avoid restoring legacy entrypoints such as `.workflow/context/rules/workflow-runtime.yaml`

## Fallback

If the global `harness` CLI is unavailable, the local script at `.codex/skills/harness/scripts/harness.py` may be used as a thin fallback entrypoint.
