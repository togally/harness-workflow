# slug沟通可读性增强-全链路透出title

> req-id: req-30 | 完成时间: 2026-04-21 | 分支: main

## 需求目标

**一句话**：让任何人在任何场景看到一个工作项（req / chg / sug / reg / bugfix）的引用时，都能**不额外跳转**就知道它在说什么。

**分层目标**：

| 层 | 目标状态 |
|----|---------|
| L1 - Agent 输出 / 汇报模板 | 所有对人/跨 agent 的汇报（status、done-report、session-memory、action-log、director → subagent briefing）默认以 `{id}（{title}）` 形式出现，单独的 `req-29` 视为违规。 |
| L2 - Harness CLI stdout 渲染 | `harness status` / `harness next` / `harness ff` / `harness suggest` 等命令打印 id 时，自动带上 title（读自 state 或 yaml 元数据）。 |
| L3 - Runtime / state yaml 字段 | `runtime.yaml` 和 `state/requirements/*.yaml` 在关键 id 字段旁冗余 `*_title` 字段，使 agent 读取 state 即可拿到 title，无需二次打开文件。 |
| L4 - 归档 / 索引文件命名 | `artifacts/{branch}/archive/` 下所有工作项目录必须带 title；`experience/index.md` 的"来源"列带 title。 |

---

## 交付范围

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

## 验收标准

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

## 变更列表

- **chg-01** chg-01（state schema — title 冗余字段）：runtime.yaml / state yaml 扩展 `*_title` 并由统一写入 helper 维护：在**不破坏现有路径与字段结构**的前提下，把 title 作为一等元数据落到 state 层：
- **chg-02** chg-02（CLI 渲染 — render_work_item_id helper）：统一 CLI stdout 打印工作项时"id + title"双字段渲染：为 CLI 打印层提供**唯一的 id→显示字符串转换 helper**，覆盖主流命令输出，实现"一次改对、处处一致"：
- **chg-03** chg-03（角色契约 + 索引硬门禁）：`stage-role.md` 新增"id + title 硬门禁" + 7 stage 角色汇报模板 + `technical-director` briefing + `experience/index.md` 来源校验：把"id + title 同时出现"从**软约定**升格为**契约硬门禁**，并让未来所有新写入的对人文档、subagent briefing、experience/index.md 新增条目都被契约强制覆盖：
- **chg-04** chg-04（归档 meta — title 落盘）【**optional — 2026-04-21 executing 阶段延期**】：归档 helper 强制 `_meta.yaml` 或"需求摘要.md"首行 title 格式：在归档链路上补一道"title 落盘"硬门禁，让归档目录即使目录名被 slug 清洗截断，也能通过内部文件恢复完整 title：
