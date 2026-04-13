# 行为边界

## 文件操作边界
- 只操作 `.workflow/` 和项目代码，不操作系统文件
- 删除操作（>5个文件）必须在 session-memory 记录原因
- 大范围删除前必须确认无法通过其他方式实现目标

## 跨层边界
- `.workflow/flow/` 只存工作文档（requirement/change/plan），不存状态数据
- `.workflow/state/` 管理所有状态，session-memory 不散落在 `.workflow/flow/` 里
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
- 经验沉淀到 `context/experience/`（stage/, tool/, risk/），不存在 session-memory 里长期留存

## 职责外问题处理规则

**触发条件**（以下任意一种均触发）：
1. AI 在执行过程中主动识别到当前角色职责范围外的 bug、需求或风险
2. 用户在对话中口头提出任何问题、想法或不满（不论是否使用了正式命令）

**各角色行为**：
- 不自行处理，不忽略
- 将问题标记为"职责外"，交主 agent 决策
- 继续当前节点任务，不因上报而中断

**上报格式**（角色向主 agent 的简短记录）：
```
来源阶段: <stage>
来源: AI识别 / 用户口头
问题描述: <一句话>
处置状态: pending
```

**主 agent 决策规则**：
1. 接收上报后，记录到当前 session-memory 的 `## 待处理捕获问题` 区块
2. 在当前节点任务完成时（或用户触发下一个 harness 命令前），逐条询问用户处置意向：
   - **A. 升级为正式 regression**：触发 `harness regression "<问题>"` 流程
   - **B. 本次忽略**：从待处理列表移除，不再提醒
   - **C. 下次再说**：保留 pending，下次会话继续提示
3. 未经用户决策前，不得擅自升级或忽略任何捕获问题
