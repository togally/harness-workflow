# Respect the Conversation Lock

`before-reply`

## Rules

- When `conversation_mode = harness`, inspect `locked_version`, `locked_stage`, `locked_artifact_kind`, and `locked_artifact_id` first.
- Do not let the reply drift away from the locked node.
- If a different context is required, suggest or run `harness exit` first.
