# chg-01: 创建技术总监角色，优化主 agent 引导入口

## 目标

将 `WORKFLOW.md` 中主 agent 的编排逻辑提炼为正式角色文件，使 Harness Workflow 中所有参与者（包括主 agent 和 subagent）都有明确的角色定义。同时精简 `WORKFLOW.md`，将执行细节下沉到角色文件中。

## 范围

### 包含

- 创建 `.workflow/context/roles/directors/technical-director.md`，承载主 agent 的完整职责定义和 SOP
- 将 `WORKFLOW.md` 中主 agent 的职责迁移到技术总监角色中：
  - 上下文维护监控
  - ff 模式协调
  - 职责外问题捕获与处置
  - done 阶段六层回顾
  - subagent 任务派发
- 精简 `WORKFLOW.md`：保留全局硬门禁、六层架构简介、引导到 `context/index.md`
- 更新 `.workflow/context/index.md`：增加顶级角色选择逻辑，开发场景默认加载技术总监角色
- 若 `context/roles/directors/` 目录不存在则创建

### 不包含

- 修改各 stage 角色的具体内容（由 chg-02 负责）
- 修改命令说明和关键节点文档（由 chg-03 负责）
- 修改六层架构的定义

## 验收标准

- [ ] `technical-director.md` 文件存在且内容完整
- [ ] `technical-director.md` 包含：角色定义、SOP、允许/禁止行为、上下文维护职责、ff 协调职责、职责外问题处理、done 阶段行为、subagent 派发规则
- [ ] `WORKFLOW.md` 变薄，但仍保留不可逾越的全局硬门禁和六层架构简介
- [ ] `context/index.md` 的加载顺序中包含顶级角色选择，开发场景能正确路由到技术总监角色
- [ ] 创建后进行一次读取验证，确保文件结构正确
