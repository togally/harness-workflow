---
id: sug-43
title: `requirement_review` / `changes_review` 加入 state yaml stage_timestamps 白名单
status: pending
created_at: "2026-04-22"
priority: high
---

# 背景

req-31（批量建议合集（20条））/ chg-02（工作流推进 + ff 机制）/ sug-16（stage_timestamps 白名单 + 总是初始化）定义的 `_STAGE_TIMESTAMP_WHITELIST` 包含：

```
requirement_review  # ✅
plan_review         # ✅
ready_for_execution # ✅
planning / executing / testing / acceptance / regression / done / archive
```

但实测 req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）的 state yaml 只记录了 `plan_review` 以后的时间戳，`requirement_review` / `changes_review` 缺失。

两种可能：
1. 白名单已含但 `_sync_stage_to_state_yaml` 调用路径在 requirement_review 阶段未触发
2. `changes_review` 未在白名单中（`requirement_review` 应在里但未被实际写入）

# 建议

- 审阅 `_STAGE_TIMESTAMP_WHITELIST` 内容，确保含 `requirement_review` + `changes_review`
- 追踪 `harness requirement "<title>"` 创建时是否调 `_sync_stage_to_state_yaml("requirement_review", ...)`，如缺失则补
- 追踪 `harness next` 从 `requirement_review` 切到 `changes_review` 是否记录两个时间戳

# 验收

- 新建 req，harness status 显示 stage=requirement_review 时，state yaml `stage_timestamps.requirement_review` 已有 ISO 时间
- `harness next` 推到 changes_review 后 `stage_timestamps.changes_review` 也有
- TDD 红绿
