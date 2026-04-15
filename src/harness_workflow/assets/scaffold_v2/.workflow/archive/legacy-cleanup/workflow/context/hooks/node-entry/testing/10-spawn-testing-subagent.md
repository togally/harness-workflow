# Testing Stage Entry

`node-entry`

## Rules

- On entering the `testing` stage: read `testing/test-plan.md` — if it does not exist, create it from the template before proceeding; read `testing/test-cases.md` — if it does not exist, create it from the template.
- Dispatch a subagent to execute the test plan: subagent reads the plan and cases, updates the status column in `testing/test-cases.md`, and writes a summary to `testing/session-memory.md`.
- After subagent completes, review `testing/test-cases.md` for failures; if failures exist, ensure each failure has a corresponding bug file in `testing/bugs/`.
- Do not advance to `acceptance` until all test cases pass and no bugs are open.
