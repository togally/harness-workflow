# harness use "<req-id>"

## 前置条件
- 目标需求存在于 `workflow/flow/requirements/` 或 `state/requirements/`

## 执行步骤
1. 写当前需求的 handoff.md（如有 current_requirement 且正在工作中）
   路径：`state/sessions/{current-req-id}/handoff.md`
2. 更新 `state/runtime.yaml` 的 `current_requirement` 为目标 req-id
3. 读 `state/requirements/{target-req-id}.yaml` 获取目标需求状态
4. 加载目标需求对应 stage 的角色文件
5. 读目标需求的 session-memory.md（检查 handoff.md 或断点）
6. 输出目标需求当前状态摘要

## 错误处理
- 目标需求不存在 → 提示可用需求列表
- 目标需求已归档 → 提示需求已完成归档，无法切换进入
