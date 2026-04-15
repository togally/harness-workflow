# Change: chg-01

## Title
阶段时间戳自动记录

## Goal
在 `harness next` 切换阶段时，自动为当前需求记录进入新阶段的时间戳。

## Scope

**包含**：
- 修改 `core.py` 的 `workflow_next` 函数
- 更新 requirement state YAML 的 `stage_timestamps` 字段
- 确保 `stage_timestamps` 初始化为字典

**不包含**：
- 回溯补录历史需求（本次只做新流转）
- 修改 runtime.yaml 结构

## Acceptance Criteria

- [ ] `harness next` 成功切换阶段后，state YAML 中出现 `stage_timestamps.{next_stage}`
- [ ] 时间戳格式为 ISO8601（带时区）
- [ ] 已有 `stage_timestamps` 不会被覆盖清空
