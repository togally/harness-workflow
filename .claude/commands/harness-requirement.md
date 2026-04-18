---
description: Run harness requirement and continue work inside the current Harness workflow state
argument-hint: "<title>"
---

This command maps to `harness requirement`.

## Hard Gate

Do not act until `WORKFLOW.md`, `.workflow/context/index.md`, and `.workflow/state/runtime.yaml` have been read.
If any of those files are missing, inconsistent, or unreadable, stop immediately and do not fall back to a legacy entrypoint.

Before acting:

1. Read the root `WORKFLOW.md`
2. Read `.workflow/context/index.md`
3. Then read `.workflow/state/runtime.yaml`
4. Load any additional role / experience / constraint files by following `.workflow/context/index.md`
5. Prefer the root `AGENTS.md`
6. If `.kimi/skills/harness/SKILL.md`, `.qoder/skills/harness/SKILL.md` or `.claude/skills/harness/SKILL.md` exists, follow the main Harness skill

Execution rules:

- center the task around `harness requirement`
- do not bypass the workflow with manual requirement / change / plan / execution steps
- if workflow state is missing or inconsistent, handle by command type:
  - install/init/update/language/status are standalone commands; no current_requirement needed
  - other commands require current_requirement; if missing, stop and prompt user
- if compilation fails, startup fails, or human-provided external input is required, enter regression first
- if human input is required, fill the related change `regression/required-inputs.md` before asking for it

If the user adds more instruction, combine it with the current workflow state to decide the next step.

Focus:

- confirm there is an active version first; if not, guide the user to `harness version` or `harness active`
- after creating the requirement, fill in background, goal, scope, and acceptance boundaries first
- do not jump into implementation; discuss whether the requirement is correct
- once the requirement is approved, point to splitting changes or running `harness next`
