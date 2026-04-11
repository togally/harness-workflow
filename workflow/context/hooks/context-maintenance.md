# Context Maintenance Hooks

## Purpose

When entering a new node, starting a new subtask, or nearing token limits, decide whether context should be kept, compacted, or cleared and switch to the appropriate loading mode.

## Trigger

- after entering a new node
- before a new subtask starts
- after a sub-feature/module completes
- when accumulated context may distort the next step

## Loading Order

1. Read `workflow/context/hooks/context-maintenance.md` first
2. Then read the general hooks under `workflow/context/hooks/context-maintenance/` in numeric order
3. If a subdirectory matches the current stage or node, read those files in numeric order too
4. Stop immediately if a hard gate blocks the action

## Contents

- `10-classify-project-scale.md`
- `20-decide-clear-or-compact.md`
- `30-switch-plan-and-act-mode.md`
- `idle/10-keep-only-routing-and-user-intent.md`
- `requirement-review/10-keep-requirement-context-only.md`
- `changes-review/10-keep-change-split-context-only.md`
- `plan-review/10-keep-active-plan-context-only.md`
- `executing/10-keep-active-plan-and-code-context.md`
- `regression/10-keep-diagnostic-context-only.md`
- `done/10-clear-implementation-context-after-capture.md`
- `testing/10-keep-testing-context-only.md`
- `acceptance/10-keep-acceptance-context-only.md`
