# agent引导流程优化

> req-id: req-22 | 完成时间: 2026-04-17 | 分支: main

## 需求目标

1. 梳理并明确 agent 在 Harness Workflow 各 stage 的引导路径和职责边界
2. 优化关键引导节点（如 session start、stage 切换、ff 模式、regression 恢复等）的提示和文档
3. 让流程逻辑更清晰，降低 agent 偏离工作流和用户困惑的概率

## 交付范围

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

## 变更列表

- **chg-01** chg-01-创建技术总监角色优化主agent引导入口：将 `WORKFLOW.md` 中主 agent 的编排逻辑提炼为正式角色文件，使 Harness Workflow 中所有参与者（包括主 agent 和 subagent）都有明确的角色定义。同时精简 `WORKFLOW.md`，将执行细节下沉到角色文件中。
- **chg-02** chg-02-统一stage角色引导逻辑：梳理并统一 Harness Workflow 各 stage 角色文件的上下文加载、SOP、流转规则，消除角色之间的冲突和遗漏，使 agent 在各 stage 的引导路径连贯一致。
- **chg-03** chg-03-优化关键节点与命令说明：明确 `harness` 系列命令的触发条件和 agent 行为，补充 ff 模式、regression、done 等关键节点的引导说明，完成一轮 agent 全流程走查验证。
- **chg-04** chg-04-重构角色继承体系与base-role定位：修正 req-22 在角色架构设计层面的核心缺陷：base-role 的适用范围被错误地窄化为"stage 角色的抽象父类"，且角色加载协议缺失模型一致性约束。通过重新定位 base-role 为"所有角色的通用规约"、新建 stage-role 承接 stage 专属公共规则、在协议中声明模型一致性，建立清晰的三层角色继承体系。
- **chg-05** chg-05-重构经验文件目录与加载规则：将经验文件从按 stage 划分改为按角色划分，使经验加载的粒度与角色粒度对齐，消除同一 stage 内不同角色经验污染或遗漏的问题。
