---
id: bugfix-3
title: CLI sug-12 / sug-13 复发：harness next 在 regression/planning 后吞 stage（执行至 testing 跳过应有的 planning/executing），且 runtime.yaml ↔ state/requirements/req-*.yaml 的 stage 字段不同步（多次手工修复）
created_at: 2026-04-23
---

# Problem Description

CLI 两个常发缺陷，跨 req-32/33/34/35/36 持续复发，每次需手工修 `runtime.yaml` + `state/requirements/req-*.yaml`。

## 缺陷 1（sug-12）：harness next 吞 stage

- 触发：`harness regression "<issue>"` 创建 reg → reg 决策 = 路由到 planning（拆新 chg）→ 主 agent 跑 `harness next`
- 期望：state regression → planning（按 reg.decision 路由）
- 实际：state 直接跳到 testing（跳过 planning + executing）

req-36 内 reg-01 / reg-02 复现 2 次，每次都是手工 Edit runtime.yaml + req-*.yaml stage 字段从 testing 改回 planning。

## 缺陷 2（sug-13）：runtime.yaml ↔ req-*.yaml stage 不同步

- 触发：某些 stage 切换后（特别是 regression / archive 触发的状态变更）
- 实际：`runtime.yaml.stage` 与 `state/requirements/req-*.yaml.stage` 不一致
- 影响：harness status 输出矛盾（runtime 显示一个 stage，requirement_stage 显示另一个）

# Root Cause Analysis

待 regression 阶段定位。**初判**：
- 缺陷 1：`harness next` 在 stage=executing + current_regression 非空时，未读 reg.decision 决定下一站，按默认 sequence 推进（executing → testing），忽略 regression 路由意图
- 缺陷 2：状态写入侧 transactional 不闭合，runtime 与 req-*.yaml 写盘有竞态/路径分叉

# Fix Scope

- `src/harness_workflow/cli.py` next/regression 子命令 + 相关 helper
- `src/harness_workflow/workflow_helpers.py` advance_stage / save_runtime / save_requirement_state 等
- `src/harness_workflow/state/*` 写盘协议
- 新建 `tests/test_state_sync_invariants.py` 防回归

**不在范围**：base-role / harness-manager 等角色文件改动

# Fix Plan

regression 阶段定位 → executing TDD 实现：

1. 缺陷 1 红用例：mock state runtime + reg.decision 路由 = planning，跑 `harness next`，期望 stage = planning（当前断红）
2. 缺陷 2 红用例：跑任意 stage 切换 → 断言 runtime.stage == req-*.yaml.stage（当前断红）
3. 实现：harness next 读 current_regression 时检查 decision.md 路由优先于默认 sequence；状态写盘统一走 transactional helper（一次写两个文件，失败回滚）
4. 跑 pytest 全套零回归

# Validation Criteria

- `tests/test_state_sync_invariants.py` 全绿
- 手动验证：触发 regression → 跑 next → 状态正确进入 reg.decision 指定 stage（不再跳到 testing）
- 回归：req-36 archive 后状态文件无任何 mismatch
- 跨 5 个 stage 切换循环跑 `harness status` 输出 runtime_stage == requirement_stage
