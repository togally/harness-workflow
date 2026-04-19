# Stage 角色公共规约（stage-role）

本文件继承 `.workflow/context/roles/base-role.md` 的通用规约，是所有 **stage 执行角色**（requirement-review、planning、executing、testing、acceptance、regression、done）和 **辅助角色**（toolsManager）的公共父类。

加载顺序：`base-role.md → stage-role.md → {具体角色}.md`

## Session Start 约定

每个 stage 角色被加载时，应默认已完成以下前置加载：
1. `runtime.yaml` 已被读取
2. `base-role.md` 已被读取
3. `stage-role.md` 已被读取
4. 本 stage 角色文件正在被读取
5. （若适用）对应的经验文件和评估文件已被加载

subagent 不需要重复读取 `runtime.yaml`、`base-role.md` 或 `stage-role.md`，除非任务明确要求。

## 继承自 base-role 的执行清单

`stage-role.md` 是所有 stage 角色的公共父类，必须将 `base-role.md` 中的抽象要求翻译为可执行、可检查的子类行为。以下清单中的每一项都**必须**在具体 stage 角色的 SOP 或职责描述中有明确的执行步骤和检查点。

| 序号 | base-role 要求 | 子类必须执行的具体行为 | 检查位置 |
|------|---------------|---------------------|---------|
| 1 | **硬门禁一：工具优先** | 在执行业务步骤前，必须先**委派** toolsManager subagent，由其匹配并推荐适合当前任务的工具；收到推荐后，优先使用匹配工具执行操作 | SOP 的"执行"部分 |
| 2 | **硬门禁二：操作说明与日志** | 每执行一个操作前说明"接下来我要执行 [操作名称]"；执行后说明"执行完成，结果是 [结果摘要]"；将摘要追加到 `.workflow/state/action-log.md` | SOP 的"执行"部分 |
| 3 | **硬门禁三：角色自我介绍** | 按 base-role 硬门禁三的格式执行，不在子角色中重复声明。格式："我是 [角色名称]，接下来我将 [任务意图]。" | SOP 的"初始化"部分 |
| 4 | **上下文维护规则：70% 评估阈值** | 任务执行过程中主动监控上下文；达到 70%（~71680 tokens）时必须评估是否使用 `/compact` 或 `/clear`；达到 85% 时必须立即执行维护 | "上下文维护职责" + SOP 的"执行"部分 |
| 5 | **经验沉淀规则** | 任务即将完成时，检查是否有可泛化的经验需要沉淀；若有，按格式写入对应经验文件 | SOP 的"退出"部分 |
| 6 | **SOP 结构约定** | SOP 必须覆盖：初始化 → 执行 → 退出 → 交接，四个阶段完整无遗漏 | SOP 整体结构 |
| 7 | **状态保存与交接** | 阶段结束前，关键决策和进度必须保存到 `session-memory.md`；向主 agent 报告结果时包含上下文消耗评估 | SOP 的"交接"部分 |

**注意**：以上清单是强制要求，不能被具体角色的业务步骤所覆盖或省略。若 `base-role.md` 与本清单冲突，以 `base-role.md` 为准；若本清单与具体 stage 角色文件冲突，以 `base-role.md` 和本清单为准。

## 通用 SOP 结构模板

所有 stage 执行角色的标准工作流程（SOP）必须遵循以下结构框架。各角色应在此框架内填充自身特有的业务逻辑，但框架的 4 个部分不得删减或调换顺序。

```
### Step 0: 初始化
1. 确认前置上下文已加载（runtime.yaml、base-role.md、stage-role.md、本角色文件）
2. 按 base-role 硬门禁三向用户做自我介绍
3. 加载必要的经验文件、评估文件、约束文件
4. 评估当前上下文负载，如已达 70% 阈值，先执行维护动作再开始任务

### Step 1~N: 执行（业务步骤）
- 每一步实质性操作前，委派 toolsManager subagent 匹配并推荐工具（工具优先），收到推荐后优先使用匹配工具
- 每执行一个操作前/后，按硬门禁二进行说明并记录到 action-log.md
- 执行过程中持续监控上下文，达到 70% 时评估维护，达到 85% 时必须立即维护
- 完成角色的核心业务任务（需求分析、计划制定、代码修改、测试执行等）

### Step N+1: 退出检查
1. 检查角色的业务退出条件是否满足
2. 检查是否有可泛化的经验需要沉淀（base-role 经验沉淀规则）
3. 检查上下文负载，报告预估消耗

### Step N+2: 交接
1. 将关键决策、进度、结论保存到 session-memory.md
2. 向主 agent 报告任务完成，报告中包含上下文消耗评估和维护建议
3. 如有待处理的职责外问题，明确上报
```

## Stage 切换上下文交接约定

当从一个 stage 推进到下一个 stage 时：
1. 原 stage 的 subagent 应确认关键决策和进度已保存到 `session-memory.md`
2. 主 agent（技术总监）负责更新 `runtime.yaml` 到目标 stage
3. 新 stage 的 subagent 应首先读取 `session-memory.md` 了解已完成的工作
4. 上下文负载达到强制维护阈值时，优先执行维护动作再加载新 stage

## 经验文件加载规则

subagent 在被主 agent 派发任务后，除读取本 stage 特有文档外，还应按以下约定加载必要的共享上下文：

### 按角色加载经验文件
- 读取 `.workflow/state/experience/index.md` 获取加载规则
- 按当前角色名加载对应经验文件（路径为 `context/experience/roles/{角色名}.md`）：
  - `requirement-review` → `context/experience/roles/requirement-review.md`
  - `planning` → `context/experience/roles/planning.md`
  - `executing` → `context/experience/roles/executing.md`
  - `testing` → `context/experience/roles/testing.md`
  - `acceptance` → `context/experience/roles/acceptance.md`
  - `regression` → `context/experience/roles/regression.md`
  - `done` → 不强制加载特定经验文件，但可加载同阶段相关经验
  - `toolsManager` → `context/experience/tool/` 下相关工具经验
- **不得批量加载整棵经验目录树**，只加载与当前角色匹配的分类

### 团队与项目上下文（before-task）
- 在开始实质性任务（生成代码、修改文件、制定计划）前加载：
  - `.workflow/context/team/development-standards.md`：团队开发规范、代码风格约束
  - 如 `development-standards.md` 不存在或为空，自动加载 `.workflow/context/team/development-standards.default.md` 作为回退

### 自动生成机制（planning/executing 阶段可选）
当检测到项目根目录存在标志性文件（`package.json`、`pom.xml`、`go.mod`、`Cargo.toml`、`pyproject.toml` 等）时，可由 toolsManager 建议触发自动生成项目专属规范：
- 扫描项目技术栈、目录结构、已有代码风格
- 基于 `development-standards.default.md` 生成项目专属 `development-standards.md`
- 以下场景应触发重新生成：技术栈重大变更、目录结构显著调整、用户提出相关改进建议

### 风险文件（before-task 必须）
- 读取 `.workflow/constraints/risk.md`，扫描高风险关键词
- 约束文件层级参考 `.workflow/constraints/index.md`：
  - `constraints/boundaries.md`：行为边界细则（before-task 时按需加载）
  - `constraints/risk.md`：风险扫描规则（before-task 必须执行）
  - `constraints/recovery.md`：失败恢复路径（遇到失败时加载）

## 对人文档输出契约（req-26 / sug-06）

所有 stage 执行角色**在完成自身业务后**，除既有 agent 过程产物（requirement.md / change.md / plan.md / session-memory.md / regression/diagnosis.md 等）外，**必须额外按本契约产出一份面向用户的精炼中文文档**（下称"对人文档"），使用户仅读该文档即可掌握当前 stage 的关键结论。

### 契约 1：双轨不迁移

- `.workflow/flow/`、`.workflow/state/` 下现存的所有 agent 过程文档（requirement.md / change.md / plan.md / session-memory.md / regression/diagnosis.md / required-inputs.md / done-report.md 等）维持原路径，不得移动、删除、重写。
- 对人文档是**新增**输出，不是对现存文档的替换。

### 契约 2：路径同构

每个 stage 角色新产出的对人文档必须落到 `artifacts/{branch}/...` 下，与制品树同构：

- 需求级：`artifacts/{branch}/requirements/{req-id}-{slug}/`
- 变更级：`artifacts/{branch}/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/`
- Bugfix 级：`artifacts/{branch}/bugfixes/{bugfix-id}-{slug}/`
- Regression 级：`artifacts/{branch}/requirements/{req-id}-{slug}/regressions/{reg-id}-{slug}/`
  （如 regression 属于 bugfix，路径相应落在 bugfix 子树下）

### 契约 3：中文命名 + 阶段粒度

| 阶段 | 文件名 | 粒度 | 产出角色 |
|------|-------|------|---------|
| requirement_review | 需求摘要.md | req | 需求分析师 |
| planning | 变更简报.md | change | 架构师 |
| executing | 实施说明.md | change | 开发者 |
| testing | 测试结论.md | req | 测试工程师 |
| acceptance | 验收摘要.md | req | 验收官 |
| regression | 回归简报.md | regression | 诊断师 |
| done | 交付总结.md | req | 主 agent（done） |

（命名本身不得变更；planning 阶段可在不偏离契约 1/2 的前提下微调表述措辞。）

### 契约 4：硬门禁

- 每个 stage 角色的"退出条件"清单中**必须**包含一条："对人文档 `{文件名}.md` 已产出且字段完整"。
- 每份对人文档必须 ≤ 1 页（屏幕一屏内读完），字段按各角色文件中的最小模板执行（字段名与字段顺序不得变更）。
- 禁止把对人文档写到 `.workflow/flow/` 或其他位置；禁止用 agent 过程文档（如 session-memory）替代对人文档。

### 契约 5：反例核对

实施后必须能在 diff 中逐条证明：

- 未触碰 `.workflow/flow/` 下现存文档；
- 未触碰 `artifacts/bugfixes/bugfix-2/`、`artifacts/main/bugfixes/bugfix-{3,4,5}/` 下历史脏数据。

## 流转规则（按需）

- 如需判断 stage 推进条件或归档规则，读取 `.workflow/flow/stages.md`
- stage 角色只关心本角色的进入条件、退出条件和必须产出
- 全局 stage 流转的守护职责由顶级角色（技术总监）承担
