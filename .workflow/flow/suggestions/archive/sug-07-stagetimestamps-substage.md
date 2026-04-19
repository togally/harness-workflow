# Suggestion: stage_timestamps 支持 sub-stage 事件记录

> **状态**: 已归档 (archived)
> **归档时间**: 2026-04-18
> **应用时间**: 2026-04-18
> **修改文件**: `.workflow/state/requirements/req-24-....yaml` (更新格式以支持 events)

## 建议标题
扩展 stage_timestamps 记录 regression 等 sub-stage 事件

## 问题描述
req-24 在 acceptance 阶段被驳回后触发了 regression 流程，产生了 chg-05 和 chg-06。但 regression 过程未在 `stage_timestamps` 中记录，导致时间线不完整。

## 改进建议
建议扩展 `stage_timestamps` 支持记录 sub-stage 事件（如 regression、re-review 等），或在 `requirement state.yaml` 中增加 `events` 列表记录关键节点。

## 预期收益
- 完整保留需求执行的时间线
- 便于回溯和分析流程瓶颈

## 来源
req-24 done 阶段六层回顾

## 优先级
低
