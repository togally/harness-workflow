# Harness Workflow

## 全局硬门禁

1. 未读取 `.workflow/state/runtime.yaml` → 立即停止，不执行任何工作
2. 节点任务必须派发给 subagent，主 agent 不直接操作项目文件或代码
3. 无 `current_requirement` → 引导用户创建需求，不进入任何工作阶段
4. `conversation_mode: harness` → 锁定当前节点，不得漂移到其他需求或阶段

## 入口

请总结当前用户需求，然后立即读取 `.workflow/context/index.md`，在其中的角色索引表中找到你所需的角色，并严格按照 `.workflow/context/roles/role-loading-protocol.md` 的协议加载该角色文件，最后按角色 briefing 执行任务。
