# 角色切换规则

## 机制
角色切换是**隐式**的：主 agent 读取 `state/runtime.yaml` 中的 `stage` 字段，自动加载对应角色文件。无需显式声明或命令触发。

## 规则
- 每次会话启动时，必须读取当前 stage 并加载对应角色文件
- stage 变更时，立即切换到新角色文件
- 角色文件包含该阶段的完整行为约束，是 subagent 的完整 briefing
- 主 agent 派发 subagent 时，必须将对应角色文件内容作为 briefing 传入

## Stage → 角色文件

| Stage | 文件 |
|-------|------|
| `requirement_review` | `roles/requirement-review.md` |
| `planning` | `roles/planning.md` |
| `executing` | `roles/executing.md` |
| `testing` | `roles/testing.md` |
| `acceptance` | `roles/acceptance.md` |
| `regression` | `roles/regression.md` |
