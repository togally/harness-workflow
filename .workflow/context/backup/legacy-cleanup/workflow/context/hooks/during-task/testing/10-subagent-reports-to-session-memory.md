# Testing Stage: Subagent Reporting

`during-task`

## Rules

- Subagents must write all test results to `testing/test-cases.md` (update Status column).
- Each discovered bug must be written to `testing/bugs/<bug-id>.md` using the bug template.
- Subagents must write a summary to `testing/session-memory.md` before exiting.
- Main agent reads `testing/session-memory.md` to determine next steps.
