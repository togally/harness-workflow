# Load Runtime

`session-start`

## Rules

- Read `workflow/state/runtime.yaml` first.
- Use `current_requirement` + `stage` fields to route the session to the correct role file and experience categories.
- If `current_requirement` is empty or the `stage` field is missing, state clearly that the session is not yet routed and guide the user to create a requirement with `harness requirement "<title>"`.
