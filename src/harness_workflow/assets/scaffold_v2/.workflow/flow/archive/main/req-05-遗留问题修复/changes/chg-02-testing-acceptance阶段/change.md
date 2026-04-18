# Change: WORKFLOW_SEQUENCE 增加 testing/acceptance 阶段

## 目标

在 `WORKFLOW_SEQUENCE` 中的 `executing` 和 `done` 之间插入 `testing` 和 `acceptance` 两个结构化自验证阶段，使 `harness next` 按 `executing -> testing -> acceptance -> done` 推进。

## 范围

- 修改 `src/harness_workflow/core.py`：
  - `WORKFLOW_SEQUENCE` 常量
  - `workflow_next()` 函数（如有阶段特殊逻辑需适配）

## 验收标准

- [ ] `WORKFLOW_SEQUENCE` 包含 `testing` 和 `acceptance`（位于 `executing` 和 `done` 之间）
- [ ] `harness next` 从 executing 推进到 testing，再到 acceptance，再到 done（三步）
- [ ] 不影响现有阶段的流转逻辑

## 依赖

无
