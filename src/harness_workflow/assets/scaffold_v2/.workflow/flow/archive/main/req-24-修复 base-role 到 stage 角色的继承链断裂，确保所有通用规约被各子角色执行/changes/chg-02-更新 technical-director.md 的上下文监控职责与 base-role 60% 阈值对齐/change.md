# Change: 更新 technical-director.md 的上下文监控职责，与 base-role 60% 阈值对齐

## 目标

确保技术总监（主 agent）的上下文监控职责从 60% 评估阈值开始，与子角色的主动监控要求保持一致。

## 范围

- 修改 `.workflow/context/roles/directors/technical-director.md`

## 验收标准

- [x] `technical-director.md` 的"监控职责"中明确加入 60% 评估阈值（~61440 tokens）
- [x] 明确 60% 阈值时的动作：检查 subagent 返回后/阶段转换前是否触发 compact/clear 需求
- [x] "检查时机"增加：subagent 任务启动前、subagent 返回后、阶段转换前
- [x] 原有 70%/85%/95% 阈值保留并调整描述层级
