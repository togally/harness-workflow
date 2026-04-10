# Before Task Hooks

## Purpose

Before reading code, writing docs, coding, or running commands, confirm that the action matches the current node.

## Trigger

- before starting a concrete task
- before reading or writing files, or running commands

## Loading Order

1. Read `docs/context/hooks/before-task.md` first
2. Then read the general hooks under `docs/context/hooks/before-task/` in numeric order
3. If a subdirectory matches the current stage or node, read those files in numeric order too
4. Stop immediately if a hard gate blocks the action

## Contents

- `10-route-runtime-and-meta.md`
- `20-load-matched-node-hooks.md`
- `30-reindex-experience.md`
