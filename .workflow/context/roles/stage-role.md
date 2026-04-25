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

### 硬门禁：按新模板自我介绍（req-30（角色 model 对用户透出（自我介绍 + 派发说明补 model 字段））/ chg-02（stage-role.md Session Start 约定扩展（强制按新模板自我介绍）））

> 溯源：req-30（角色 model 对用户透出（自我介绍 + 派发说明补 model 字段））/ chg-02（stage-role.md Session Start 约定扩展（强制按新模板自我介绍）），并列生效于 chg-01（base-role.md 自我介绍硬门禁模板扩展（加 role_key / model 字段））模板底座。

- subagent 加载自身 role.md 后、任何实质工作前，**必须**按 `base-role.md` 硬门禁三新模板（`我是 {role_name}（{role_key} / {model}），接下来我将 {task_intent}。`）向用户做自我介绍。
- 与 `.workflow/context/roles/role-loading-protocol.md` Step 7.5 模型一致性自检**并列执行**，顺序为**先自检再自我介绍**——自检发现模型不符时直接报错中止，不给用户输出错误的自我介绍。
- `model` 字段取自 `.workflow/context/role-model-map.yaml`，未列出则回落 `default`（当前 `sonnet`）。

### 硬门禁：同阶段不打断 + default-pick 记录（req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance 精简 / 对人文档缩减 / 决策批量化到阶段边界））/ chg-05（S-E 决策批量化协议））

> 溯源：req-31 / chg-05；与 base-role.md `## 硬门禁四：同阶段不打断原则` 并列生效。

- 每个 stage 的 subagent 在**同一 stage 内**遇争议点，按 base-role 硬门禁四流程：列 options + 标 default-pick + 按默认推进 + stage 流转前 batched-report。
- **必须**在本 stage 的 `session-memory.md` 中留痕一节"default-pick 决策清单"（即使为空亦写"无"），汇总本 stage 所有按默认推进的决策与理由。
- 汇报时**必须**把 default-pick 清单归并到 stage-role.md `## 统一精简汇报模板（req-31 / chg-02）` 字段 3"开放问题 / default-pick"；不另起新段落。

#### stage 流转点豁免子条款（req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md）））

> 溯源：req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））；与本段原协议（req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance 精简 / 对人文档缩减 / 决策批量化到阶段边界））/ chg-05（S-E 决策批量化协议））**并列生效**，不替代。

- 原协议（req-31 / chg-05）止于**同一 stage 内**争议点的批量化推进；本子条款把豁免面扩展到**相邻同类型 stage 的流转点**：
  - `requirement_review → planning` 流转点**默认静默**：analyst 自主推进 chg 拆分，不邀用户对"是否进入 planning"作拍板决策（default-pick 直接按 HM-1 = A，harness-manager §3.6.1）；
  - `planning → ready_for_execution` **保留用户拍板**（拍板对象是"需求 + 推荐拆分"合并产物，analyst batched-report 后等待用户确认一次）；
- 豁免仅适用于 analyst 承载的两 stage（req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md）） 方向 C）；其他 stage 流转（executing → testing / testing → acceptance 等）不在本条款豁免面内，规约不变；
- 与 base-role 硬门禁四例外条款（数据丢失 / 不可回滚 / 合规三类）+ 硬门禁七（Ra/Rb/Rc 周转汇报）**并列生效**，不替代；任何数据丢失 / 不可回滚 / 合规风险仍须中断并报告；
- 用户 override 后门：用户说出 escape hatch 触发词（`我要自拆` / `我自己拆` / `让我自己拆` / `我拆 chg`）之一时，豁免撤销，回退手工拆分路径（详见 technical-director §6.2）。

## 继承自 base-role 的执行清单

`stage-role.md` 是所有 stage 角色的公共父类，必须将 `base-role.md` 中的抽象要求翻译为可执行、可检查的子类行为。以下清单中的每一项都**必须**在具体 stage 角色的 SOP 或职责描述中有明确的执行步骤和检查点。

| 序号 | base-role 要求 | 子类必须执行的具体行为 | 检查位置 |
|------|---------------|---------------------|---------|
| 1 | **硬门禁一：工具优先** | 在执行业务步骤前，必须先**委派** toolsManager subagent，由其匹配并推荐适合当前任务的工具；收到推荐后，优先使用匹配工具执行操作 | SOP 的"执行"部分 |
| 2 | **硬门禁二：操作说明与日志** | 每执行一个操作前说明"接下来我要执行 [操作名称]"；执行后说明"执行完成，结果是 [结果摘要]"；将摘要追加到 `.workflow/state/action-log.md` | SOP 的"执行"部分 |
| 3 | **硬门禁三：角色自我介绍** | 按 base-role 硬门禁三的格式执行，不在子角色中重复声明。格式："我是 {role_name}（{role_key} / {model}），接下来我将 {task_intent}。"；`{role_key} / {model}` 字段取自 `.workflow/context/role-model-map.yaml`，未列出回落 `default`（当前 `sonnet`） | SOP 的"初始化"部分 |
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

## 统一精简汇报模板（req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance 精简 / 对人文档缩减 / 决策批量化到阶段边界））/ chg-02（S-B 统一精简汇报模板（stage-role.md 新增 + executing/testing/acceptance 3 份 role.md 汇报段替换）））

> 溯源：req-31（角色功能优化整合与交互精简...）/ chg-02（S-B 统一精简汇报模板...）；并列生效于 base-role.md `## 上下文维护规则`、契约 7（id+title，req-30 chg-03）、req-30（角色 model 对用户透出）/ chg-02 自我介绍硬门禁三、chg-05（S-E 决策批量化协议）"同阶段不打断原则"。

所有 stage 执行角色与辅助角色（harness-manager 派发后的 subagent）向主 agent 汇报时，**必须**按以下四字段顺序输出，**不得**在模板之外叠加冗余自检清单：

### 字段 1：产出（≤ 3 行）

- 落地文件路径 / commit sha / 关键数值（如 pytest passed / failed 数、grep 命中数）。
- **契约 7 并列生效**：本字段若引用工作项 id（req / chg / sug / bugfix / reg），首次引用**必须**形如 `{id}（{title}）`，后续可简写。

### 字段 2：状态（单行）

- 取值：`PASS` / `FAIL` / `ABORT`，随后一句话原因。
- 语义：
  - `PASS` = 本 stage 退出条件全部满足
  - `FAIL` = 业务未达标但 subagent 主动退出请求主 agent 决策
  - `ABORT` = 遇硬门禁违反 / 外部事件 / 数据丢失风险，立即停止

### 字段 3：开放问题（≤ 3 条；若无写"无"）

- 每条形如 `- {问题一句话}。推荐默认 = {选项}。理由：{一句话}。`
- 与 chg-05（S-E 决策批量化协议）"default-pick 决策列表"语义重叠，本字段同时覆盖"本 stage 按默认推进的争议点"清单。
- > 3 条说明 stage 粒度过大，应拆 chg 或升级 regression。

### 字段 5：结尾硬约束（req-37（阶段结束汇报简化：周转时不给选项，只停下+报本阶段结束+报状态） / chg-01）

- 汇报末尾**必须**含一行 `**本阶段已结束。**`（或语义等价句式，如 `**本命令已执行完。**`）。
- **禁止**在本行之后追加「建议下一步」/「是否同意」/「要不要」/「A/B/C 选项」等诱导用户选择的句式（base-role 硬门禁七 Ra/Rb 并列生效）。
- **豁免**：破坏性 / 不可回滚 / 跨 repo 动作（清单见 base-role 硬门禁七「豁免清单」）允许保留用户确认句式。

### 与旧模板的差异（req-31 / chg-02）

- **去除**：契约 7 样本行（改由 `harness validate --contract all` / `harness status --lint` 自检）、每轮硬性上下文消耗评估（仅在 ≥ 70% 时按 base-role 规则主动上报）、硬约束自检块（内化进状态 = PASS/FAIL）、"是否准备好进下 stage"（融入建议下一步）；字段 4「建议下一步」（req-37（阶段结束汇报简化：周转时不给选项，只停下+报本阶段结束+报状态） / chg-01 废止，避免周转时诱导用户点头）
- **保留**：字段 1 对契约 7 的引用约束（与 req-30 chg-03 并列生效）、字段 3 对 default-pick 的承载（与 chg-05 并列生效）。

### 样本（复制-改几个字即可用）

```
**产出**：
- .workflow/flow/requirements/req-31（角色功能优化整合与交互精简...）/changes/chg-02/：change.md + plan.md 各 1 份（落位见 repository-layout.md §3）。
- pytest 288 passed，零回归。

**状态**：PASS。四字段新章节已在 stage-role.md 落地；executing/testing/acceptance 三份 role.md 汇报段已替换为引用新模板。

**开放问题**：
- 无。

**本阶段已结束。**
```

## 对人文档输出契约（req-26 / sug-06）

所有 stage 执行角色**在完成自身业务后**，除既有 agent 过程产物（requirement.md / change.md / plan.md / session-memory.md / regression/diagnosis.md 等）外，**必须额外按本契约产出一份面向用户的精炼中文文档**（下称"对人文档"），使用户仅读该文档即可掌握当前 stage 的关键结论。

### 契约 1：双轨不迁移

- `.workflow/flow/`、`.workflow/state/` 下现存的所有 agent 过程文档（requirement.md / change.md / plan.md / session-memory.md / regression/diagnosis.md / required-inputs.md / done-report.md 等）维持原路径，不得移动、删除、重写。
- 对人文档是**新增**输出，不是对现存文档的替换。

### 契约 2：路径同构

每个 stage 角色新产出的对人文档必须落到 `artifacts/{branch}/...` 下，与制品树同构。

> **详细路径定义、对人文档白名单（≥ 8 类）、机器型文档落位（见 `.workflow/flow/repository-layout.md` §3）、命名前缀约定、历史存量豁免范围（req-02 ~ req-37 保留旧结构，req-41+ 严格执行新规）见 `.workflow/flow/repository-layout.md`（req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C）） / chg-01（repository-layout 契约底座）升格为权威定义）。**

### 契约 3：中文命名 + 阶段粒度

> **完整白名单（含 SQL 脚本 / 部署文档 / 接入配置说明 / runbook / 手册 / 合同附件 / 其他需人执行或阅读的产物）见 `.workflow/flow/repository-layout.md` §2**（req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C）） / chg-01（repository-layout 契约底座）权威定义）。

| 阶段 | 文件名 | 粒度 | 产出角色 |
|------|-------|------|---------|
| ~~testing~~ | ~~测试结论.md~~ **不要求产出**（req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance 精简 / 对人文档缩减 / 决策批量化到阶段边界））/ chg-04（S-D 对人文档缩减）废止，数据写入 test-report.md） | ~~req~~ | ~~测试工程师~~ |
| ~~acceptance~~ | ~~验收摘要.md~~ **不要求产出**（req-31 / chg-04 废止，数据写入 acceptance-report.md） | ~~req~~ | ~~验收官~~ |
| done | 交付总结.md | req | 主 agent（done） |

> **req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C）） 废止**：requirement_review / planning / executing / regression 四类对人 brief（需求摘要.md / 变更简报.md / 实施说明.md / 回归简报.md）已由 req-41 废止，**req-id ≥ 41 起不再产出**；legacy req（req-02 ~ req-40）保留旧结构原地存档，不迁移。req-id ≥ 41 起，req 级对人文档仅为 `交付总结.md`（done 阶段产出）+ raw `requirement.md` 副本（artifacts/ 副本供外部审阅）；其他 stage 不产出对人 brief。

（命名本身不得变更。）

- `决策汇总.md`（ff --auto 模式产出，acceptance 前由 chg-03 工具自动生成，落位见 repository-layout.md §2，字段按 DecisionPoint）

#### 跨文档引用 frontmatter（req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance 精简 / 对人文档缩减 / 决策批量化到阶段边界））/ chg-04（S-D 对人文档缩减））

- `交付总结.md` 头部 frontmatter：`requirement_link: <path-to-requirement.md>`（路径见 repository-layout.md §3 req 级落位）
- 字段名采用 default-pick P-8 = A（英文语义化）；存量历史文档不回填。

### 契约 4：硬门禁

- **req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance 精简 / 对人文档缩减 / 决策批量化到阶段边界））/ chg-04（S-D 对人文档缩减）精简**：testing / acceptance 两阶段的对人文档已废止，契约 4 硬门禁对这两阶段**豁免**；其 agent 过程文档 `test-report.md` / `acceptance-report.md` 即结论载体。
- **req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C）） 废止**：req-id ≥ 41 起，req 级对人文档仅为 `交付总结.md`（done 阶段产出）+ raw `requirement.md` 副本；requirement_review / planning / executing / regression 四 stage 不产出对人 brief；契约 4 "对人文档已产出"硬门禁对以上四 stage（req-id ≥ 41 作用域）**豁免**。
- `done` 阶段退出条件**必须**包含："`交付总结.md` 已产出且字段完整"（落位见 repository-layout.md §2）。
- 每份对人文档必须 ≤ 1 页（屏幕一屏内读完），字段按各角色文件中的最小模板执行（字段名与字段顺序不得变更）。
- 禁止把对人文档写到 `.workflow/flow/` 或其他位置；禁止用 agent 过程文档（如 session-memory）替代对人文档。
- **req-31（批量建议合集（20条））/ chg-01（契约自动化 + apply-all bug）/ sug-15 升格条款**：stage 角色在 SOP 交接步骤之前，**必须**执行 `harness validate --contract all`（或 `harness status --lint`）；若输出违规则阻塞 stage 推进。该自检同时覆盖契约 3 / 4 / 6 / 7。

### 契约 5：反例核对

实施后必须能在 diff 中逐条证明：

- 未触碰 `.workflow/flow/` 下现存文档；
- 未触碰 `artifacts/bugfixes/bugfix-2/`、`artifacts/main/bugfixes/bugfix-{3,4,5}/` 下历史脏数据。

### 契约 6：sug 文件 frontmatter 统一约定（req-28 / chg-01，AC-15）

所有阶段角色在 `done-report.md` 建议转 suggest 池、或通过 `harness suggest` 新增 sug 文件时，写入的 sug 文件**必须**带完整 YAML frontmatter，统一包含以下字段：

| 字段 | 说明 |
|------|------|
| `id` | 形如 `sug-NN`，必须与文件名编号一致 |
| `title` | 一句话建议标题 |
| `status` | 初始值 `pending`；`--apply` / `--archive` 后由 CLI 自动翻转 |
| `created_at` | ISO 日期字符串 |
| `priority` | `high` / `medium` / `low` 三者之一 |

实施要求：

- sug 编号由 `create_suggestion` 统一分配，跨 `.workflow/flow/suggestions/` 与 `archive/` 子目录单调递增，禁止手工硬编码编号。
- 无 frontmatter 的历史 sug 不做回填，`harness suggest --apply / --delete / --archive` 通过 filename fallback（`sug-NN` 前缀匹配）兼容处理。
- 新增 sug 一律按本契约写入；未遵守的视为违反硬门禁，由 done 阶段和 reviewer 拦截。

### 契约 7：id + title 硬门禁（req-30（slug 沟通可读性增强：全链路透出 title））

> **并列生效**：本契约与契约 1-6 并列生效，不覆盖既有约束；仅对工作项 **id 引用格式**做强制约束。

所有 stage 角色在产出"对人 / 跨 agent 文档"时，对工作项 id（`req-*` / `chg-*` / `sug-*` / `bugfix-*` / `reg-*`）的引用必须遵守以下硬门禁，违反视为契约 7 违反：

#### 规则

- **首次出现必须带 title**：在每一个对人文档、session-memory 新写入段、done-report、subagent briefing、action-log 新写入行、`experience/index.md` 来源列的**首次引用点**，工作项 id 必须形如 `{id}（{title}）`（全角括号 `（）`）。
- **同上下文后续可简写**：同一文档同一上下文的后续引用可简写回纯 id，不必重复 title。
- **裸 id = 违规**：首次引用点单独的 `req-29` / `chg-02` / `sug-05` / `bugfix-3` 视为契约 7 硬门禁违反。
- **id 密集展示反向豁免条款（reg-01（对人汇报批量列举 id 缺 title 不可读） / chg-06（硬门禁六 + 契约 7 批量列举子条款补丁））**：以下场景"同上下文后续可简写"豁免**不生效**，每条 id 都按首次引用处理（带完整 title 或 ≤ 15 字描述，与硬门禁六批量列举子条款双向覆盖）——
  1. **DAG 完成度 / 进度概览表**：跨多个 chg 列状态时（如 `chg-01 done | chg-02 done | chg-03 in-progress`），每行 id 必带 title。
  2. **阶段收束汇报 / batched-report**：`本 stage 完成 chg-01 + chg-02 + chg-03 + ...` 形态属于密集展示，每个 chg id 必带 ≤ 15 字描述。
  3. **跨 chg 索引表 / 制品目录**：`changes/` 树枚举、跨 chg 引用清单、归档索引等表格场景，id 列必带 title 列。
  4. **触发判定**：同一段落 / 表格 / 列表 / TaskList / commit message / CLI stdout 中并列 ≥ 2 个不同 id 即触发反向豁免；与硬门禁六批量列举子条款共享判定边界。**注意**：TaskList / 进度条 / commit message 不在"id 密集展示反向豁免"的豁免面（即"同上下文后续可简写"豁免）之内——这些场景本身即属于密集展示，每条 id 必须带 title 或 ≤ 15 字描述，不得简写为裸 id。

#### 校验方式

- done 阶段六层回顾：`grep -nE "(req|chg|sug|bugfix|reg)-[0-9]+" artifacts/{branch}/requirements/{req-id}-{slug}/ --include=*.md -r`，对每个命中文件的首次命中行核对是否含"（...）"或行内已有 title 字段；未通过视为硬门禁违反。
- CLI 行为配合：`harness status` / `harness next` / `harness ff` / `harness suggest --list` 的 stdout 已由 `render_work_item_id` helper 统一带 title（req-30 chg-02 落地），agent 可直接复制 CLI 输出作为文档样本。

#### fallback

- **pending-title 占位**：若 title 在新建瞬间暂未定（极少数场景），允许首次引用写 `{id}（pending-title）`；但 done 阶段必须修正为正式 title，pending 残留同样视为违规。
- **legacy 引用**：本契约只对**本次提交之后**的新增 / 修改引用生效；历史文档内的裸 id 不被本契约追溯（仅 reviewer 按需补）。

#### 参考实现与自证样本

- 实现：`src/harness_workflow/workflow_helpers.py::render_work_item_id`（runtime 缓存 → state fallback → sug frontmatter → `(no title)` 降级）。
- 自证：req-30（slug 沟通可读性增强：全链路透出 title）自身的 `requirement.md` / 各 `change.md` / `plan.md` 首次引用工作项 id 时均带完整 title，作为新约定示范样本。

## task_context_index 回退语义（req-32 / chg-03）

> **req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ chg-03（CTO 派发 briefing 注入 task_context_index + 快照落盘）**：主 agent 派发 subagent 时，briefing JSON 中会携带 `task_context_index`（≤ 8 条，每条 `{"path", "reason"}`）与 `task_context_index_file`（快照相对路径，形如 `.workflow/state/sessions/{req-id}/task-context/{stage}-{seq}.md`）。

- `task_context_index` 是**建议清单**，不是强制加载清单；subagent 按路径加载若命中文件不存在（仓库形态动态变化），**静默 fallback** 到 `.workflow/context/index.md` 全量按需加载，不得报错或中断 stage。
- 对应 CLI 层提供 helper `workflow_helpers._resolve_task_context_paths(index, root) -> (existing, missing)` 用于过滤；CLI 不强制校验 subagent 行为，仅提供 helper 与单测覆盖。
- `task_context_index_file` 指向本次派发落盘的 frontmatter 快照，归档时由既有 `harness archive` 随 `.workflow/state/sessions/{req-id}/` 一并迁入 `artifacts/{branch}/requirements/{req-id}-{slug}/sessions/`。

## 流转规则（按需）

- 如需判断 stage 推进条件或归档规则，读取 `.workflow/flow/stages.md`
- stage 角色只关心本角色的进入条件、退出条件和必须产出
- 全局 stage 流转的守护职责由顶级角色（技术总监）承担
