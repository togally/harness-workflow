# Acceptance Stage Entry

`node-entry`

## Rules

- On entering the `acceptance` stage: read `acceptance/acceptance-checklist.md` — if it does not exist, create it from the template; read the requirement document to understand acceptance criteria.
- Dispatch a subagent to execute the acceptance checklist: subagent reads requirement, design docs, and the checklist, verifies each item against actual deliverables, writes results to `acceptance/acceptance-checklist.md` and `acceptance/sign-off.md`, and writes summary to `acceptance/session-memory.md`.
- After subagent completes, review `acceptance/sign-off.md`.
- Do not advance to `done` until sign-off decision is "Accepted".
