# Regression Decision

## 1. Decision Status

- `analysis`
- `confirmed` ✅
- `rejected`
- `cancelled`
- `converted` ✅

## 2. Final Notes

该回归问题已确认为真实设计缺口。问题的核心在于 context-maintenance 的触发机制完全依赖被动和主观判断，缺乏自动检查机制。

**问题确认**：
- Session 上下文会持续累积，导致 token 浪费、回复变慢
- 现有 hook 触发条件全部是被动/主观的
- 没有周期性/阈值型自动检查机制

**解决方案**：
- 在 before-reply 阶段添加主动触发 hook
- 实现三种触发条件：轮次触发、文件数触发、阶段切换强制
- 添加 session 状态追踪机制（轮次计数、已读文件数）
- 提供配置支持，允许自定义阈值

## 3. Follow-Up

✅ 已将回归转换为正式变更：**before-reply-context-maintenance-hook**

**创建的变更内容**：
- 新增 hook 文件：`workflow/context/hooks/before-reply/10-context-maintenance-check.md`
- 更新模板文件：`workflow/templates/session-memory.md`
- 更新文档：`workflow/context/hooks/README.md`
- 更新配置：`workflow/context/rules/workflow-runtime.yaml`
- 变更状态：completed

**实施结果**：
- 所有文件已创建且格式正确
- 三种触发条件已实现
- 向后兼容性良好
- 验收测试通过

**经验捕获**：
此次变更积累了关于主动上下文维护的经验，建议考虑将相关经验捕获到 `workflow/context/experience/debug/context-maintenance.md`。
