# After Task Hooks

## Purpose

Review and capture lessons immediately after a task so new constraints and failed paths are not lost.

## Trigger

- after a stage-level task ends
- before fully closing the current action

## Loading Order

1. Read `workflow/context/hooks/after-task.md` first
2. Then read the general hooks under `workflow/context/hooks/after-task/` in numeric order
3. If a subdirectory matches the current stage or node, read those files in numeric order too
4. Stop immediately if a hard gate blocks the action

## Contents

- `10-update-session-memory.md`
- `20-promote-mature-lessons.md`
