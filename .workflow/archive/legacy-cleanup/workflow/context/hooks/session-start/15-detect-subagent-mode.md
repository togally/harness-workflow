# Detect Subagent Mode

`session-start`

## Rules

- If you were dispatched as a subagent to execute a specific task: do NOT read `workflow-runtime.yaml` or attempt to route through workflow state; read your task context from the file or prompt you were given; execute only the assigned task; write results to `session-memory.md` in the assigned change/testing/acceptance directory; do not run `harness next` or any stage-advancing command; exit after completing your task.
- If you are the main agent (you entered via `harness enter` or a harness slash command): proceed with normal workflow routing; you control stage transitions and subagent dispatch.
