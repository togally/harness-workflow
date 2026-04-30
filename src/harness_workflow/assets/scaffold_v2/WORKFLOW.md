# Harness Workflow

## 全局硬门禁

1. 未读取 `.workflow/state/runtime.yaml` → 立即停止，不执行任何工作
3. 无 `current_requirement` → 引导用户创建需求，不进入任何工作阶段

> 历史降级（req-54（硬门禁体系简化-砍4条降级-加1条项目级brief强约束））：
> - 原全局 2「节点任务必须派发给 subagent」→ 降级为指导原则（重大改动必派；微调（单文件 / 状态文件 / 文档）主 agent 可直接做）
> - 原全局 4「conversation_mode: harness 锁定节点」→ 合并到状态机文档（`.workflow/flow/stages.md`），不再硬门禁；conversation_mode 语义并入状态机文档（.workflow/flow/stages.md / role-loading-protocol.md Step 1 异常处理）

## 入口

请总结当前用户需求，然后立即读取 `.workflow/context/index.md`，在其中的角色索引表中找到你所需的角色，并严格按照 `.workflow/context/roles/role-loading-protocol.md` 的协议加载该角色文件，最后按角色 briefing 执行任务。
