---
description: Run harness change and continue work inside the current Harness workflow state
argument-hint: "<title>"
---

This command maps to `harness change`.

Before acting:

1. Read `docs/context/rules/workflow-runtime.yaml`
2. Use `current_version` to read the active version `meta.yaml`
3. Then read:
   - `docs/context/rules/development-flow.md`
   - `docs/context/hooks/README.md`
   - `docs/context/rules/agent-workflow.md`
   - `docs/context/rules/risk-rules.md`
   - `docs/context/experience/index.md`
4. Prefer the root `AGENTS.md`
5. If `.qoder/skills/harness/SKILL.md` or `.claude/skills/harness/SKILL.md` exists, follow the main Harness skill

Execution rules:

- center the task around `harness change`
- do not bypass the workflow with manual requirement / change / plan / execution steps
- if workflow state is missing or inconsistent, stop and tell the user to run `harness active "<version>"`
- if compilation fails, startup fails, or human-provided external input is required, enter regression first
- if human input is required, fill the related change `regression/required-inputs.md` before asking for it

If the user adds more instruction, combine it with the current workflow state to decide the next step.

Focus:

- decide whether this change belongs to a requirement or stands alone
- after creating the change, fill in intent, impact scope, risk points, and acceptance method first
- remind the user that every completed change must include `mvn compile`
- once the change is clear, point to `harness plan` or `harness next`
