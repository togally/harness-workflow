# Before Human Input Hooks

## Purpose

Ask the human for input only after local evidence has been collected and external information is still missing.

## Trigger

- before asking the human for configuration, data, credentials, or environment details

## Loading Order

1. Read `docs/context/hooks/before-human-input.md` first
2. Then read the general hooks under `docs/context/hooks/before-human-input/` in numeric order
3. If a subdirectory matches the current stage or node, read those files in numeric order too
4. Stop immediately if a hard gate blocks the action

## Contents

- `10-local-debug-first.md`
- `20-required-inputs-template-first.md`
