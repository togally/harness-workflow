# No Implementation Before Execution Confirmation

`during-task`

## Rules

- During `ready_for_execution`, do not read source code for implementation prep, write production code, or start execution tasks.
- Only after explicit human approval or `harness next --execute` may the workflow enter `executing`.
