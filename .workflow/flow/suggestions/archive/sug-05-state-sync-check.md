# Suggestion: 状态同步检查机制

> **状态**: 已归档 (archived)
> **归档时间**: 2026-04-18
> **应用时间**: 2026-04-18
> **修改文件**: `.workflow/context/roles/acceptance.md`

## 建议标题
acceptance → done 流转时自动检查状态一致性

## 问题描述
在 req-24 的 done 阶段回顾中发现，`requirement state.yaml` 的 stage 与 `runtime.yaml` 的 stage 不一致，导致需要手动修复。

## 改进建议
在 acceptance → done 流转时，应自动检查 `requirement state.yaml` 与 `runtime.yaml` 的一致性，防止类似状态不一致问题再次发生。

## 预期收益
- 减少人工修复状态不一致的工作
- 提高工作流状态可靠性

## 来源
req-24 done 阶段六层回顾

## 优先级
中
