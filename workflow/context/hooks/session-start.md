# Session Start Hooks

## Purpose

When a session starts, resumes, or explicitly enters Harness mode, route state, self-check, and load experience first.

## Trigger

- a new session starts
- a suspended session resumes
- `harness enter` is called explicitly

## Loading Order

1. Read `docs/context/hooks/session-start.md` first
2. Then read the general hooks under `docs/context/hooks/session-start/` in numeric order
3. If a subdirectory matches the current stage or node, read those files in numeric order too
4. Stop immediately if a hard gate blocks the action

## Contents

- `10-load-runtime.md`
- `20-load-experience-and-risk.md`
- `30-stop-on-broken-state.md`
