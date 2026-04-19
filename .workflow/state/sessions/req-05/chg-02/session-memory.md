# Session Memory: chg-02

## Change
自动推进与状态流转机制

## Status
✅ 已完成

## Steps
- [x] 读取当前 `runtime.yaml` 结构
- [x] 增加 `ff_mode: false` 和 `ff_stage_history: []` 字段
- [x] 在 `stages.md` 中补充 ff 自动推进的详细逻辑
- [x] 在 `stages.md` 中定义 ff 模式下 `session-memory` 保存规范
- [x] 在 `stages.md` 中定义 ff 暂停/退出机制
- [x] 检查与现有 state/ 结构的兼容性

## Internal Test
- [x] `runtime.yaml` 包含 `ff_mode` 字段
- [x] `runtime.yaml` 包含 `ff_stage_history` 字段
- [x] `stages.md` 中定义了自动推进逻辑
- [x] `stages.md` 中定义了 session-memory 规范
- [x] `stages.md` 中定义了暂停/退出机制

## Notes
当前 `runtime.yaml` 已被更新，新增字段对非 ff 模式无影响，兼容性良好。
