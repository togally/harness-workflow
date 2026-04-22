# Context 角色索引

本文件是 Harness Workflow 的**角色索引表**。所有 agent 在被唤醒后，请先根据下方索引确认自己的角色，然后严格按照 `.workflow/context/roles/role-loading-protocol.md` 加载角色文件并执行。

---

## 角色索引

### 顶级角色（Director）

| 角色名称 | 职责 | 文件路径 | model |
|---------|------|---------|-------|
| **技术总监**（yaml key: technical-director） | 编排整个工作流，维护 stage 按研发流程图流转，监控上下文负载和异常，在 done 阶段执行六层回顾 | `.workflow/context/roles/directors/technical-director.md` | opus |

### Stage 执行角色

| 角色名称 | 职责 | 文件路径 | model |
|---------|------|---------|-------|
| **需求分析师**（yaml key: requirement-review） | 澄清用户意图，识别边界和风险，编写并确认 `requirement.md` | `.workflow/context/roles/requirement-review.md` | opus |
| **架构师**（yaml key: planning） | 将需求拆分为独立变更，为每个变更制定 `change.md` + `plan.md` | `.workflow/context/roles/planning.md` | opus |
| **开发者**（yaml key: executing） | 严格按照 `plan.md` 执行变更，完成后进行内部测试 | `.workflow/context/roles/executing.md` | sonnet |
| **测试工程师**（yaml key: testing） | 独立设计并执行测试，客观评估实现是否达到需求要求 | `.workflow/context/roles/testing.md` | sonnet |
| **验收官**（yaml key: acceptance） | 对照需求文档和变更文档逐条核查，辅助人工做出最终验收判定 | `.workflow/context/roles/acceptance.md` | sonnet |
| **诊断师**（yaml key: regression） | 独立分析问题，判断是否是真实问题，确定根因，决定路由方向 | `.workflow/context/roles/regression.md` | opus |
| **主 agent（done 阶段）**（yaml key: done） | 对整个需求周期进行六层回顾检查，输出回顾报告，转 suggest 池 | `.workflow/context/roles/done.md` | opus |

### 辅助角色

| 角色名称 | 职责 | 文件路径 | model |
|---------|------|---------|-------|
| **命令引导中心（harness-manager）**（yaml key: harness-manager） | 作为所有 harness 命令的统一入口，解析命令意图、调度角色、管理 skill 生命周期 | `.workflow/context/roles/harness-manager.md` | opus |
| **工具管理员（toolsManager）**（yaml key: tools-manager） | 在其他 agent 执行操作前，为其搜索、匹配并推荐最合适的工具 | `.workflow/context/roles/tools-manager.md` | sonnet |
| **审查员（reviewer）**（yaml key: reviewer） | 按 checklist 逐条审查变更产物，客观评估产出质量 | `.workflow/context/roles/reviewer.md` | sonnet |
| **项目现状报告官（project-reporter）**（yaml key: project-reporter） | 按 10 节精简模板扫本仓库实况、产出 `artifacts/main/project-overview.md`；禁编造 / 禁推测 / 禁代写 §11（req-32（新设 project-reporter 角色按节生成项目现状报告到 artifacts/main/project-overview.md）） | `.workflow/context/roles/project-reporter.md` | opus |

### 抽象父类

| 角色名称 | 职责 | 文件路径 |
|---------|------|---------|
| **基础角色（base-role）** | 所有角色（含 Director、toolsManager、stage 角色）的通用规约，定义通用硬门禁、工具优先原则、经验沉淀规则、上下文维护规则 | `.workflow/context/roles/base-role.md` |
| **Stage 角色公共规约（stage-role）** | 所有 stage 执行角色和辅助角色的公共父类，继承 base-role 并叠加 Session Start 约定、Stage 切换交接、经验文件加载规则、流转规则 | `.workflow/context/roles/stage-role.md` |

### 通用协议

| 协议名称 | 用途 | 文件路径 |
|---------|------|---------|
| **角色加载协议** | 定义所有角色的通用加载步骤，所有 agent 必须遵循 | `.workflow/context/roles/role-loading-protocol.md` |

---

> **权威来源**：`.workflow/context/role-model-map.yaml` 是角色→模型映射的唯一权威源。
> 本 `index.md` 中各表的 `model` 列是镜像展示，任何一方修改必须同步另一方；
> 出现冲突时一律以 `.workflow/context/role-model-map.yaml` 为准。
> 详细选择依据见 `.workflow/context/experience/tool/harness.md`（chg-04 沉淀）。

