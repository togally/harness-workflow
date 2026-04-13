# During Task Hooks

## Purpose

During execution, keep checking whether the current behavior has drifted outside the locked node or stage boundary.

## Trigger

- while a task is in progress
- before continuing with additional actions

## Loading Order

1. Read `workflow/context/hooks/during-task.md` first
2. Then read the general hooks under `workflow/context/hooks/during-task/` in numeric order
3. If a subdirectory matches the current stage or node, read those files in numeric order too
4. Stop immediately if a hard gate blocks the action

## Contents

- `10-stay-inside-locked-node.md`
- `idle/10-no-implementation-prep.md`
- `requirement-review/10-no-source-code.md`
- `requirement-review/20-no-auto-stage-advance.md`
- `changes-review/20-no-auto-stage-advance.md`
- `plan-review/20-no-auto-stage-advance.md`
- `ready-for-execution/10-no-implementation-before-confirmation.md`
- `done/10-no-closeout-before-lesson-capture.md`
- `regression/10-no-direct-rework.md`
- `executing/10-follow-plan-and-verify.md`
- `testing/10-subagent-reports-to-session-memory.md`
- `acceptance/10-checklist-driven-only.md`
