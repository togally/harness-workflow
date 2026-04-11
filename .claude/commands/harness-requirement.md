---
description: Run harness requirement and continue work inside the current Harness workflow state
argument-hint: "<title>"
---

This command maps to `harness requirement`.

Before acting:

1. Read `workflow/context/rules/workflow-runtime.yaml`
2. Use `current_version` to read the active version `meta.yaml`
3. Then read:
   - `workflow/context/rules/development-flow.md`
   - `workflow/context/hooks/README.md`
   - `workflow/context/rules/agent-workflow.md`
   - `workflow/context/rules/risk-rules.md`
   - `workflow/context/experience/index.md`
4. Prefer the root `AGENTS.md`
5. If `.qoder/skills/harness/SKILL.md` or `.claude/skills/harness/SKILL.md` exists, follow the main Harness skill

Execution rules:

- center the task around `harness requirement`
- do not bypass the workflow with manual requirement / change / plan / execution steps
- if workflow state is missing or inconsistent, stop and tell the user to run `harness active "<version>"`
- if compilation fails, startup fails, or human-provided external input is required, enter regression first
- if human input is required, fill the related change `regression/required-inputs.md` before asking for it

If the user adds more instruction, combine it with the current workflow state to decide the next step.

Focus:

- confirm there is an active version first; if not, guide the user to `harness version` or `harness active`
- after creating the requirement, fill in background, goal, scope, and acceptance boundaries first
- do not jump into implementation; discuss whether the requirement is correct
- once the requirement is approved, point to splitting changes or running `harness next`
