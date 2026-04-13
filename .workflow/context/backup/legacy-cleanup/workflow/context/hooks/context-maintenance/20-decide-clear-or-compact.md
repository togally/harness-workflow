# Decide Between /clear and /compact

`context-maintenance`

## Rules

- If previous context no longer affects the next task, run `/clear`, then re-read `workflow-runtime.yaml`, the current version `meta.yaml`, and the matched hooks.
- If previous context still matters but large details no longer do, run `/compact` and retain the current version, stage, artifact, active plan, unresolved issues, and critical paths.
- Do not clear context blindly when the current stage, focus object, or remaining verification work is still unclear.
