# 行为边界

## 文件操作边界
- 只操作 `workflow/` 和项目代码，不操作系统文件
- 删除操作（>5个文件）必须在 session-memory 记录原因
- 大范围删除前必须确认无法通过其他方式实现目标

## 跨层边界
- `flow/` 只存工作文档（requirement/change/plan），不存状态数据
- `state/` 管理所有状态，session-memory 不散落在 flow/ 里
- 角色文件不写业务规则，规则归对应层管理
- 主 agent 不直接执行节点任务，节点任务归 subagent

## 阶段边界
- 当前 stage 的禁止行为以角色文件为准
- 不得跳过 planning 直接进入 executing
- `done` 状态的需求不得被重新打开（只能新建需求）
- testing / acceptance 阶段不得修改被测内容

## 状态边界
- `state/runtime.yaml` 只存全局运行状态，不存业务数据
- `state/requirements/{id}.yaml` 只存该需求的执行状态
- 经验沉淀到 `state/experience/`，不存在 session-memory 里长期留存
