# Requirement

## 1. Title

slug 沟通可读性增强：全链路透出 title

---

## 2. 背景

### 2.1 用户原话

> "现在使用 req chang 等形式说明需求功能，沟通起来让人很模糊"

### 2.2 问题本质

Harness workflow 在需求（requirement）、变更（change）、建议（suggestion）、回归（regression）、bugfix 等工作项上都采用"短 slug + 递增编号"作为内部唯一标识（`req-29`、`chg-02`、`sug-08`、`bugfix-3` 等）。这个 slug 对 CLI / 存储层足够好，但对**人类读者和跨 agent 协作**是一种"信息丢失"：**slug 不携带语义**，读者必须额外跳转到索引或打开文件才能知道它在说什么功能。

这在以下**四个场景**里都已经或正在造成沟通摩擦（用户已明确四个场景"全都算"）：

#### 场景 1：Agent 对人汇报时只说 slug

典型示例：

> "req-29 已完成，全部 5 个 change 通过验收。"

读者需要反查"req-29 到底是什么"才能确认这是不是他在跟踪的那件事。对**多需求并行**的用户尤其痛：面对 `active_requirements: [req-28, req-29, req-30]` 三个 slug，看不出哪个是"ff --auto"、哪个是"slug 可读性"。

#### 场景 2：CLI 参数用 slug 不直观

典型示例：

```
harness next req-29
harness change chang-01
harness regression "..." --req req-28
```

用户输入时必须先记住或查表对照 slug。**本 req-30 自身的长 slug**（`req-30-slug沟通可读性增强-全链路透出title`）就是一个反面案例：slug 在目录名里已超过 20 个字符，但命令行里出现的仍然只是 `req-30` 三个字符，长 slug 的信息在沟通入口被截断。

#### 场景 3：归档 / 索引文件里只有 slug，回看时看不出内容

典型示例：

- `.workflow/state/experience/index.md` 的"来源"列只写 `req-02 planning 阶段`、`req-07 chg-04`，读者看经验时没有即刻上下文。
- `artifacts/main/archive/requirements/` 下现存 `req-28-批量建议合集（7条）/` 等目录名虽已带一部分中文，但统一性不足；且子层（`changes/chg-01-xxx/`、`regressions/reg-01-xxx/`）的标题不一定沉淀到人能读的层级。

#### 场景 4：Agent 之间交接用 slug，接收方缺背景

典型示例：

> Director 派发 subagent 时写 `current_requirement: req-30`，但 briefing 里若没同时给 title，接收 agent 第一件事就得去打开文件找标题，浪费一次工具调用也拖慢交接。

### 2.3 根因

- **runtime.yaml / state/\*.yaml 等状态文件**只存 id，不冗余存 title。
- **CLI stdout 渲染器**（`harness status` / `harness next` / `harness ff` 等）对 id 的打印没有"补 title"这一步。
- **Agent 汇报 / 日志模板**（action-log.md、session-memory.md、done-report.md）缺约定：汇报时应写 `req-29（批量建议合集 2 条）` 而不是 `req-29`。
- **归档目录命名约定**虽允许中文，但未**强制**落到每一个工作项，子层（change、regression、bugfix 归档）也没统一。

---

## 3. 目标

**一句话**：让任何人在任何场景看到一个工作项（req / chg / sug / reg / bugfix）的引用时，都能**不额外跳转**就知道它在说什么。

**分层目标**：

| 层 | 目标状态 |
|----|---------|
| L1 - Agent 输出 / 汇报模板 | 所有对人/跨 agent 的汇报（status、done-report、session-memory、action-log、director → subagent briefing）默认以 `{id}（{title}）` 形式出现，单独的 `req-29` 视为违规。 |
| L2 - Harness CLI stdout 渲染 | `harness status` / `harness next` / `harness ff` / `harness suggest` 等命令打印 id 时，自动带上 title（读自 state 或 yaml 元数据）。 |
| L3 - Runtime / state yaml 字段 | `runtime.yaml` 和 `state/requirements/*.yaml` 在关键 id 字段旁冗余 `*_title` 字段，使 agent 读取 state 即可拿到 title，无需二次打开文件。 |
| L4 - 归档 / 索引文件命名 | `artifacts/{branch}/archive/` 下所有工作项目录必须带 title；`experience/index.md` 的"来源"列带 title。 |

---

## 4. 范围

### 4.1 包含（In scope）

- L1-L4 四层的"读 / 写 title"改造：字段定义、模板更新、渲染逻辑、命名约定。
- 对现有工作项的"title 回填"迁移：为存量 req / chg / sug / bugfix / regression 补齐 title 元数据（优先新建 + 活跃项，存量已归档项按成本决定是否回填）。
- 角色文件中"汇报模板"章节的文本更新（requirement-review、planning、executing、testing、acceptance、regression、done、director 均涉及）。
- 至少一条回归测试 / 单元测试覆盖 CLI 渲染带 title 的主路径。
- 本需求自身的 `requirement.md` / `需求摘要.md` / `变更简报.md` 等对人文档要作为"新约定"的示范样本。

### 4.2 不包含（Out of scope）

- **不重命名 slug / 不改 id 编号规则**：slug 作为内部稳定键仍保留不变（id 是机器友好、title 是人友好，两者互补而非替换）。
- **不改目录层级 / 路径结构**：`artifacts/{branch}/requirements/{req-id}-{slug}/` 等路径同构约定（req-27 成果）不被本需求重构。
- **不回写历史 action-log / session-memory 的旧行**：只从改造生效后的"新写入"开始带 title，不回溯。
- **不做多语言 / 国际化**：title 维持当前中文 + 英文混用形态，不做 i18n 化。
- **不引入外部元数据服务**：title 存储走 yaml + markdown frontmatter 内嵌，不新增 db / cache。
- **不覆盖 `.workflow/archive/legacy-cleanup/` 等 legacy 目录**：遗留目录按"只读保留"处理。

---

## 5. 验收标准（Acceptance Criteria）

验收标准按四层组织，每层 1-2 条可观察、可验证的 AC。

### L1 - Agent 输出 / 汇报

- **AC-01（汇报模板强制 title）**：`session-memory.md` / `done-report.md` / director → subagent briefing / acceptance 报告中，所有对工作项的引用**首次出现时**必须形如 `{id}（{title}）`（后续同上下文可简写回 id）。对 req-30 自身而言，subagent 首次提到本需求时必须写 `req-30（slug 沟通可读性增强：全链路透出 title）`。可在 PR diff 或 action-log 中 grep 验证。
- **AC-02（旧模板已更新）**：`.workflow/context/roles/` 下各 stage 角色文件的"汇报/输出示例"章节、以及 `stage-role.md` 的"对人文档输出契约"章节，已显式写明"id + title 双字段"的模板。未更新的视为违规。

### L2 - Harness CLI stdout

- **AC-03（CLI 默认带 title）**：`harness status` / `harness next` / `harness ff [--auto]` / `harness suggest --list` 等命令的 stdout 在打印任意工作项 id 时，默认**同行附带 title**（格式示例：`current_requirement: req-30  slug 沟通可读性增强：全链路透出 title`）。至少一条单元测试断言此渲染。
- **AC-04（title 缺失降级）**：当 state 里确实没有 title（极少数 legacy 记录）时，CLI 退化为只打印 id 并附加 `(no title)` 标记，不报错退出。

### L3 - Runtime / state yaml 字段

- **AC-05（state yaml 含 \*_title）**：`runtime.yaml` 的 `current_requirement` / `current_regression` / `locked_requirement` 等关键 id 字段旁**增加同名 + `_title` 的冗余字段**（例如 `current_requirement_title: "slug 沟通可读性增强：全链路透出 title"`）；`state/requirements/*.yaml` 已有 `title` 字段保持不变，但会被 CLI 主动用作 L2 渲染数据源。活跃需求（active_requirements 列表中的所有 id）的 title 字段必须非空。
- **AC-06（写入路径统一）**：所有对 state yaml 写入 id 的代码路径（CLI 命令、create_suggestion helper、归档 helper 等）都必须**同步写入对应 title**，新建工作项缺 title 视为失败。至少一条单元测试覆盖。

### L4 - 归档 / 索引

- **AC-07（归档目录命名规范）**：`artifacts/{branch}/archive/` 下新产生的 `requirements/{req-id}-{slug}/`、`bugfixes/{bugfix-id}-{slug}/`、`requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/`、`regressions/{reg-id}-{slug}/` 等目录名中的 `{slug}` 已是人可读的中文短语（当前约定保持）；同时每个归档目录下的**索引/摘要**（如 `需求摘要.md` 的首行 `# 需求摘要：{id} {title}` 或新增的 `_meta.yaml`）显式包含 title 字段，便于批量扫描。
- **AC-08（经验索引带 title）**：`.workflow/state/experience/index.md`（或其指向的 `context/experience/**/*.md` 中"来源"列）在记录"来源"时，至少写到 `req-29（批量建议合集 2 条）chg-04` 这一粒度，单独裸写 `req-29` 视为违规。历史条目按"新增时校验、存量按需补"的策略处理。

### 综合 AC

- **AC-09（测试覆盖）**：L2 / L3 改造至少覆盖 2 条单元测试 + 1 条端到端 smoke，零回归（保持现有 180+ test 通过）。
- **AC-10（自证样本）**：req-30 自身的 `需求摘要.md` / `变更简报.md` / `实施说明.md` 作为"新约定"的示范，被 done 阶段六层回顾点名认可。

---

## 6. 候选方案

> **✅ 最终选型（2026-04-21 用户确认）：方案 B — 结构 + 渲染双管齐下**

用户明确"我先描述痛点，你和需求分析师一起提方案"——以下提出 **3 个候选方案**，按"改造幅度 × 一致性收益"维度排布，供用户在需求澄清环节选择。

### 方案 A：轻量"渲染层"方案（成本 S）

**一句话**：只改渲染/汇报输出，id 仍是一等公民，title 由 CLI / agent 运行时"现查现补"。

**四层做法**：

- L1：只更新角色文件的汇报模板说明，要求 agent 每次写 id 时同步写 title（title 来源：读 state 或 requirement.md）；无新字段。
- L2：`harness status` / `harness next` 等命令在打印 id 前先 lookup 一次 title（从 `state/requirements/*.yaml` 的 `title` 字段），拼接后输出。
- L3：**不动** runtime.yaml 字段结构，仅依赖已存在的 `state/requirements/*.yaml` 的 `title`。
- L4：归档目录命名保持现状；仅在 `experience/index.md` 的"来源"列后追加 title。

**优势**：
- 改造面小，不破坏任何现有字段 / 存储结构。
- 风险可控，可渐进上线。
- 迁移成本低：无需回填 runtime.yaml 冗余字段。

**劣势**：
- L3 不做字段冗余，意味着任何读 runtime.yaml 的代码若想拿 title，都得额外打开一次 `state/requirements/{id}.yaml`——subagent briefing 场景下多一次 IO。
- 一致性依赖"模板自觉"而非"结构硬约束"：仍可能退化回裸 id。

**适用场景**：用户希望"先解决沟通摩擦，结构改动越少越好，后续视效果再迭代"。

**实施成本**：S（估 1 个 change，工时 0.5 天）。

---

### 方案 B：结构 + 渲染双管齐下（成本 M，推荐）

**一句话**：runtime.yaml / state 冗余 `*_title` 字段 + CLI 渲染层统一补 title + 汇报模板硬约束。

**四层做法**：

- L1：同方案 A，但把"id + title"双字段写进 `stage-role.md` 的对人文档契约作为**硬门禁**，done 阶段检查项明确"裸 id 视为违规"。
- L2：CLI 渲染层统一实现一个 `render_work_item_id(id, state)` helper，输出 `{id}（{title}）`；所有命令走这个 helper。
- L3：`runtime.yaml` 新增 `current_requirement_title` / `current_regression_title` / `locked_requirement_title` 三个冗余字段，由写 runtime.yaml 的 helper 统一维护；对应的 `state/requirements/*.yaml` 保留 `title` 为权威源，runtime.yaml 的 `*_title` 为 cache。活跃需求（当前 req-28 / req-29 / req-30）一次性回填。
- L4：归档 helper（`resolve_archive_root` / 迁移相关）在写归档目录时，除了 slug 目录名外，额外落一份 `_meta.yaml` 或在现有 `需求摘要.md`、`交付总结.md` 首行强制带 title；`experience/index.md` 新增条目硬校验 title。

**优势**：
- 结构 + 行为双保险：就算 agent 汇报模板漏写，CLI 渲染层仍会补 title；就算 CLI 漏印，state 字段仍可被下游消费。
- subagent 跨层传递效率最高：读一次 runtime.yaml 就拿到 id + title。
- 一致性收益全面覆盖四层场景。

**劣势**：
- 改动面中等：涉及 runtime.yaml schema、写入 helper、渲染 helper、角色模板四处。
- 有"缓存一致性"风险：runtime.yaml 的 `*_title` 与 `state/requirements/*.yaml` 的 `title` 不同步会造成错显，需约定"写入时同步、读取时以 state 为准"。

**适用场景**：用户希望"一次做对，一劳永逸地解决四层痛点"。

**实施成本**：M（估 3-4 个 change：schema 扩展 / 渲染 helper / 模板更新 / 归档命名 + 回填；工时 1.5-2 天）。

---

### 方案 C：激进"title 一等公民"方案（成本 L）

**一句话**：所有 CLI 参数 / 引用位置都允许 title 子串匹配，id 退为次级标识。

**四层做法**：

- L1-L2：在方案 B 基础上，进一步让 CLI 接受 title 子串作为参数输入（如 `harness next "slug 可读性"` 可解析到 req-30）。
- L3：state yaml 中 title 升格为"第二键"，支持反向索引（title → id）。
- L4：归档目录命名从 `{id}-{slug}` 改为 `{slug}` 或 `{title-short}`（但违反本需求"不包含改路径结构"约束）。

**优势**：人机交互最自然，CLI 参数可直接说人话。

**劣势**：
- 与"不重命名 slug / 不改路径结构"约束直接冲突，等价于需要另开一个需求做大重构。
- title 作为参数存在歧义（两个 req 的 title 有重叠子串时如何消歧？需要新的 UX）。
- 工具链侵入深，回归风险高。

**适用场景**：用户希望"重构 slug 体系，title 直接作为一等键"——但这已超出 req-30 的当前范围。

**实施成本**：L（估 6+ 个 change，工时 4+ 天），且需要先用另一个需求解决参数歧义 UX。

**建议**：本次**不选**方案 C；若用户长远有此诉求，提建议（sug）登记到后续批次处理。

---

## 7. 候选方案对比速查表

| 维度 | 方案 A 轻量 | 方案 B 双管（推荐） | 方案 C 激进 |
|------|-----------|-------------------|------------|
| L1 模板硬门禁 | 仅文档约定 | 契约硬门禁 | 契约硬门禁 |
| L2 CLI 渲染 | 有 | 有（统一 helper） | 有 + 支持反向解析 |
| L3 state 冗余字段 | 无 | 有 `*_title` | 有 + 反向索引 |
| L4 归档命名 | 保持现状 | 强制 title 落 meta | 结构重构 |
| slug 是否保留 | 保留 | 保留 | 不建议保留 |
| 单元测试数 | 1-2 | 3-5 | 8+ |
| 与既有约束冲突 | 无 | 无 | 与"不改路径结构"冲突 |
| 上线节奏 | 单 change | 3-4 change | 独立需求 |
| 推荐度 | 次选 | **首选** | 不建议 |

> 本次决策：采用方案 B；方案 A 次选不采纳；方案 C 的"title 作为 CLI 参数"作为 sug 登记到后续批次。

---

## 8. Split Rules（留给 planning 阶段）

- 本需求建议拆为 3-4 个 change（对应方案 B）：
  1. **chg-01**：state schema 扩展 + 写入 helper 同步维护 title（L3）。
  2. **chg-02**：CLI 渲染层 `render_work_item_id` helper + 覆盖现有命令（L2）。
  3. **chg-03**：角色文件 / stage-role 对人文档契约补 title 硬门禁（L1 + L4 索引部分）。
  4. **chg-04**（可选）：归档 helper 强制 title meta 落盘 + `experience/index.md` 校验（L4）。
- 每个 change 独立可交付，验收后合并。
- 本需求完成时填 `completion.md`，记录启动验证成功。
- 按方案 B 的 L1-L4 映射到 chg-01~chg-04（L3 → chg-01、L2 → chg-02、L1+L4 索引 → chg-03、L4 归档 meta → chg-04 可选）。

---

## 9. 风险与建议

- **风险 1：缓存一致性**（方案 B 特有）——runtime.yaml 的 `*_title` 与 state yaml 的 `title` 不同步会错显。规避：约定"state 为权威源，CLI 读 runtime.yaml 的 `*_title` 失败时 fallback 到 state"，并有单元测试覆盖。
- **风险 2：agent 模板退化**——即使写明"id + title"硬门禁，仍可能有 agent 漏写。规避：done 阶段六层回顾显式检查、`harness status` 有"lint 本需求产出是否含 title"的轻量校验。
- **风险 3：存量回填工作量失控**——历史 req / bugfix / chg 若全部回填 title 成本高。规避：只回填"当前活跃 + 未来新建"，历史归档按需处理；明确写入 AC-05 的"活跃需求必须"作为边界。
- **建议**：推荐采纳**方案 B**；方案 C 的"title 作为 CLI 参数"作为 sug 登记到后续批次。
