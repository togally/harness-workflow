---
id: sug-28
title: harness ff（无 --auto）从 executing 被倒推到 ready_for_execution 行为反直觉
status: pending
created_at: "2026-04-21"
priority: medium
---

# 背景

req-31（批量建议合集（20条））ff 模式推进时，在 `stage=executing` 状态下执行 `harness ff`（不带 `--auto`），CLI 把 stage 从 `executing` 倒推回 `ready_for_execution`，且未改 ff_mode。

这与用户预期（启用 ff 模式继续自动推进）严重不符。用户的直觉是 ff 让流程加速，不是倒退。

# 建议

- 方案 A：`harness ff`（无 `--auto`）stage 已到 executing 及以后时，报 "ff-mode already past executing; use --auto to enter auto-advance" 并拒绝倒推
- 方案 B：`harness ff` 统一要求 `--auto`，取消无 flag 的 degenerate 模式（逐步 deprecate）
- 方案 C：文档明确 `harness ff` 无 `--auto` = "重置 stage 到 ff 起点并开启 ff_mode"，让用户知情

# 关联

- `src/harness_workflow/cli.py` ff 子命令
- `src/harness_workflow/workflow_helpers.py` `workflow_fast_forward`
- `.workflow/flow/stages.md` §"启动 ff"
