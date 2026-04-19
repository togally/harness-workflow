# Requirement

## 1. Title

建议为 req-12 补充更精确的 stage 时间戳：当前 req-12 的时间戳是在 executing 阶段后补录的，无法准确反映各阶段真实耗时。未来应确保 harness next 正确记录时间戳。

## 2. Goal

- 由于 req-12 已归档，精确回溯各阶段真实耗时已不可行
- 确保后续需求的阶段切换都能被 `harness next` 准确记录时间戳

## 3. Scope

**包含**：
- 确认 req-14 已解决 "harness next 正确记录所有阶段时间戳" 的问题
- 将 req-18 标记完成并归档

**不包含**：
- 修改已归档的 req-12 数据（无法获得真实时间）

## 4. Acceptance Criteria

- [ ] `harness next` 已能在所有阶段切换时自动记录时间戳（由 req-14 实现）
- [ ] req-18 已归档

## 5. Split Rules

- 无需拆分，直接确认完成并归档
