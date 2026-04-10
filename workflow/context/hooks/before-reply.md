# Before Reply Hooks

## Purpose

Before every substantive reply, verify that the next response still stays inside the current Harness node.

## Trigger

- before a substantive reply to the human
- before explaining the next step or recommended action

## Loading Order

1. Read `docs/context/hooks/before-reply.md` first
2. Then read the general hooks under `docs/context/hooks/before-reply/` in numeric order
3. If a subdirectory matches the current stage or node, read those files in numeric order too
4. Stop immediately if a hard gate blocks the action

## Contents

- `10-respect-conversation-lock.md`
- `requirement-review/10-request-human-review-first.md`
- `changes-review/10-request-change-review-first.md`
- `plan-review/10-request-plan-review-first.md`
- `ready-for-execution/10-request-execution-confirmation.md`
- `idle/10-offer-only-workflow-actions.md`
- `20-block-workflow-drift.md`
- `30-check-stage-boundary.md`
