# Hooks Directory

## Purpose

This directory organizes hooks by invocation timing. The agent should identify the current timing first, then read the timing overview and the matching hook files.

## Matching Order

1. Read `docs/context/rules/workflow-runtime.yaml`
2. Use `current_version` to read the active version `meta.yaml`
3. Identify the current invocation timing, such as `session-start`, `before-reply`, `before-task`, `during-task`, `before-human-input`, `after-task`, or `before-complete`
4. Read the matching `<timing>.md` overview document
5. Read the general hook files under `<timing>/` in numeric order
6. If there is a stage-specific subdirectory such as `requirement-review/`, `executing/`, or `regression/`, load those files in numeric order as well
7. If any hard gate blocks the action, stop immediately

## Timings

- `session-start.md`: Session Start Hooks. When a session starts, resumes, or explicitly enters Harness mode, route state, self-check, and load experience first.
- `session-start/`: concrete hook files and node subdirectories for that timing
- `before-reply.md`: Before Reply Hooks. Before every substantive reply, verify that the next response still stays inside the current Harness node.
- `before-reply/`: concrete hook files and node subdirectories for that timing
  - `10-context-maintenance-check.md`: 主动检查 session 上下文状态，防止上下文累积过高（轮次、文件数、阶段切换触发）
  - `20-conversation-lock-check.md`: 检查对话锁状态
  - `30-workflow-drift-check.md`: 检查工作流是否偏离当前节点
  - `40-stage-boundary-check.md`: 检查阶段边界
- `node-entry.md`: Workflow Node Hooks. Load node-specific constraints that define what is allowed and forbidden in the current workflow node.
- `node-entry/`: concrete hook files and node subdirectories for that timing
- `before-task.md`: Before Task Hooks. Before reading code, writing docs, coding, or running commands, confirm that the action matches the current node.
- `before-task/`: concrete hook files and node subdirectories for that timing
- `during-task.md`: During Task Hooks. During execution, keep checking whether the current behavior has drifted outside the locked node or stage boundary.
- `during-task/`: concrete hook files and node subdirectories for that timing
- `before-human-input.md`: Before Human Input Hooks. Ask the human for input only after local evidence has been collected and external information is still missing.
- `before-human-input/`: concrete hook files and node subdirectories for that timing
- `after-task.md`: After Task Hooks. Review and capture lessons immediately after a task so new constraints and failed paths are not lost.
- `after-task/`: concrete hook files and node subdirectories for that timing
- `before-complete.md`: Before Completion Hooks. Before claiming completion, enforce compile, startup, and regression gates.
- `before-complete/`: concrete hook files and node subdirectories for that timing
