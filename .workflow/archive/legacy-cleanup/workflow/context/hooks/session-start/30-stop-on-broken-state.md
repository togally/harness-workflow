# Stop on Broken State

`session-start`

## Rules

- Stop immediately if `current_version` is missing, runtime/config disagree, or the version `meta.yaml` is missing.
- Do not manually simulate the workflow.
- Prefer asking the human to run `harness active "<version>"` or restore the missing files.
