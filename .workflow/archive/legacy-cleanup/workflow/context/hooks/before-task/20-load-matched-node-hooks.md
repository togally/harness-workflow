# Load Matched Node Hooks

`before-task`

## Rules

- Identify the current invocation timing first, then load the node hooks that match the current stage.
- Load only matching hooks instead of bulk-reading every hook file.
