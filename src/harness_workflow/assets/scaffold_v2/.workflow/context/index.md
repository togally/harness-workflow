# Context 角色索引

本文件是 Harness Workflow 的**角色索引表**。所有 agent 在被唤醒后，请先根据下方索引确认自己的角色，然后严格按照 `.workflow/context/roles/role-loading-protocol.md` 加载角色文件并执行。

---

## 角色索引

### 顶级角色（Director）

| 角色名称 | 职责 | 文件路径 |
|---------|------|---------|
| **技术总监** | 编排整个工作流，维护 stage 按研发流程图流转，监控上下文负载和异常，在 done 阶段执行六层回顾 | `.workflow/context/roles/directors/technical-director.md` |

### Stage 执行角色

| 角色名称 | 职责 | 文件路径 |
|---------|------|---------|
| **需求分析师** | 澄清用户意图，识别边界和风险，编写并确认 `requirement.md` | `.workflow/context/roles/requirement-review.md` |
| **架构师** | 将需求拆分为独立变更，为每个变更制定 `change.md` + `plan.md` | `.workflow/context/roles/planning.md` |
| **开发者** | 严格按照 `plan.md` 执行变更，完成后进行内部测试 | `.workflow/context/roles/executing.md` |
| **测试工程师** | 独立设计并执行测试，客观评估实现是否达到需求要求 | `.workflow/context/roles/testing.md` |
| **验收官** | 对照需求文档和变更文档逐条核查，辅助人工做出最终验收判定 | `.workflow/context/roles/acceptance.md` |
| **诊断师** | 独立分析问题，判断是否是真实问题，确定根因，决定路由方向 | `.workflow/context/roles/regression.md` |
| **主 agent（done 阶段）** | 对整个需求周期进行六层回顾检查，输出回顾报告，转 suggest 池 | `.workflow/context/roles/done.md` |

### 辅助角色

| 角色名称 | 职责 | 文件路径 |
|---------|------|---------|
| **工具管理员（toolsManager）** | 在其他 agent 执行操作前，为其搜索、匹配并推荐最合适的工具 | `.workflow/context/roles/tools-manager.md` |

### 抽象父类

| 角色名称 | 职责 | 文件路径 |
|---------|------|---------|
| **基础角色（base-role）** | 所有角色（含 Director、toolsManager、stage 角色）的通用规约，定义通用硬门禁、工具优先原则、经验沉淀规则、上下文维护规则 | `.workflow/context/roles/base-role.md` |
| **Stage 角色公共规约（stage-role）** | 所有 stage 执行角色和辅助角色的公共父类，继承 base-role 并叠加 Session Start 约定、Stage 切换交接、经验文件加载规则、流转规则 | `.workflow/context/roles/stage-role.md` |

### 通用协议

| 协议名称 | 用途 | 文件路径 |
|---------|------|---------|
| **角色加载协议** | 定义所有角色的通用加载步骤，所有 agent 必须遵循 | `.workflow/context/roles/role-loading-protocol.md` |
