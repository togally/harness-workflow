# Workflow Node Hooks

## Purpose

Load node-specific constraints that define what is allowed and forbidden in the current workflow node.

## Trigger

- when entering a workflow node
- after the stage or mode changes

## Loading Order

1. Read `docs/context/hooks/node-entry.md` first
2. Then read the general hooks under `docs/context/hooks/node-entry/` in numeric order
3. If a subdirectory matches the current stage or node, read those files in numeric order too
4. Stop immediately if a hard gate blocks the action

## Contents

- `idle/10-formalize-workspace-first.md`
- `requirement-review/10-discussion-only.md`
- `requirement-review/20-wait-for-human-approval.md`
- `changes-review/20-wait-for-human-approval.md`
- `changes-review/10-change-doc-first.md`
- `plan-review/10-plan-before-code.md`
- `plan-review/20-wait-for-human-approval.md`
- `ready-for-execution/10-wait-for-explicit-confirmation.md`
- `executing/10-execution-only.md`
- `regression/10-diagnosis-before-fix.md`
- `experience-capture/10-capture-lessons.md`
