# req-22: agent引导流程优化

## 背景

当前 Harness Workflow 中，agent 在不同 stage 的引导流程存在不清晰、不连贯的问题。上下文加载规则、角色切换、流转条件等散落在多个文档中，导致 agent 在执行任务时容易出现理解偏差，用户也难以判断当前所处阶段和下一步动作。需要对 agent 引导流程进行系统梳理和优化，使整体流程更直观、可执行。

## 目标

1. 梳理并明确 agent 在 Harness Workflow 各 stage 的引导路径和职责边界
2. 优化关键引导节点（如 session start、stage 切换、ff 模式、regression 恢复等）的提示和文档
3. 让流程逻辑更清晰，降低 agent 偏离工作流和用户困惑的概率

## 范围

### 包含

- 梳理 `.workflow/context/index.md`、`.workflow/context/roles/`、`.workflow/flow/stages.md` 中的引导逻辑
- 优化 agent 进入各 stage 时的上下文加载和角色定位
- 明确 `harness` 系列命令对应的触发条件和 agent 行为
- 检查和补充关键引导节点的缺失说明（如 ff 模式、regression、done 阶段等）

### 不包含

- 修改 Harness Workflow 的核心六层架构
- 引入新的外部工具或 MCP
- 大规模重构 `.workflow` 目录结构（除非梳理过程中发现的小范围优化）

## 验收标准

- [ ] 各 stage 的引导文档和角色职责一致，无明显冲突或遗漏
- [ ] `harness` 命令触发条件与 agent 行为对应关系明确
- [ ] ff 模式、regression、done 等关键节点的引导说明完整
- [ ] 完成一轮 agent 全流程走查验证，确保引导逻辑可执行

## 备注

- 本需求可能涉及多个现有文档的联动更新，建议按变更拆分逐步推进
- 相关参考：`.workflow/context/index.md`、`.workflow/flow/stages.md`、`.workflow/context/roles/`
