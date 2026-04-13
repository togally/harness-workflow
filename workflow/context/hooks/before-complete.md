# Before Completion Hooks

## Purpose

Before claiming completion, enforce compile, startup, and regression gates.

## Trigger

- before claiming a change is complete
- before claiming a requirement is complete
- before claiming a version is complete

## Loading Order

1. Read `workflow/context/hooks/before-complete.md` first
2. Then read the general hooks under `workflow/context/hooks/before-complete/` in numeric order
3. If a subdirectory matches the current stage or node, read those files in numeric order too
4. Stop immediately if a hard gate blocks the action

## Contents

- `10-require-mvn-compile.md`
- `20-require-startup-validation.md`
- `30-failure-to-regression.md`
- `40-require-session-memory-sync.md`
- `50-require-experience-promotion-check.md`
- `testing/10-require-all-cases-recorded.md`
- `acceptance/10-require-sign-off.md`
