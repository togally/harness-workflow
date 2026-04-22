# Change Plan

## 1. Development Steps

### Step 1: 新增 `stage-role.md` 契约 7

- **操作意图**：把"id + title 硬门禁"沉淀为可 grep、可 lint 的契约。
- **涉及文件**：`.workflow/context/roles/stage-role.md`（对人文档输出契约章节末尾，现有契约 6 之后）。
- **关键代码思路**：
  - 新增标题 `### 契约 7：id + title 硬门禁（req-30）`。
  - 3 个子段：
    - **规则**：所有对人 / 跨 agent 的输出（session-memory.md / done-report.md / 对人文档 / briefing 正文 / action-log.md 新写入）中，工作项 id（`req-*` / `chg-*` / `sug-*` / `bugfix-*` / `reg-*`）**首次出现**时必须形如 `{id}（{title}）`；同一文档上下文的后续引用可简写回 id。
    - **校验方式**：done 阶段六层回顾执行 `grep -nE "(req|chg|sug|bugfix|reg)-[0-9]+" artifacts/{branch}/requirements/{req-id}-{slug}/ --include=*.md`，对每个命中文件的首次命中行核对是否含"（...）"。未通过视为硬门禁违反。
    - **fallback**：若 title 在新建瞬间暂未定，允许写 `{id}（pending-title）`；done 阶段必须修正为正式 title，pending 残留视为违规。
  - 在契约 7 开头显式写 "本契约与契约 1-6 并列生效，不覆盖既有约束；仅对 id 引用格式做强制约束"（R3 缓解）。
- **验证方式**：`grep -n "契约 7：id + title 硬门禁" .workflow/context/roles/stage-role.md` 命中一处。

### Step 2: 更新 7 个 stage 角色文件的"汇报 / 输出示例"章节

- **操作意图**：让每个 stage 角色在汇报和对人文档示例中显式带 title。
- **涉及文件**（逐一编辑）：
  - `.workflow/context/roles/requirement-review.md`
  - `.workflow/context/roles/planning.md`
  - `.workflow/context/roles/executing.md`
  - `.workflow/context/roles/testing.md`
  - `.workflow/context/roles/acceptance.md`
  - `.workflow/context/roles/regression.md`
  - `.workflow/context/roles/done.md`
- **关键代码思路**：
  - 每个文件至少 1 处 Edit：
    - 若有"对人文档"章节：将模板首行加固为 `# {文件名}：{id} {title}`（如 `# 需求摘要：{id} {title}` 已是现状，补充注释"`{id}` 与 `{title}` 均不可省略（req-30 契约 7）"）。
    - 若有"汇报段 / 向主 agent 汇报"示例：示例升格为 `req-30（slug 沟通可读性增强：全链路透出 title）已进入 executing，3 个 change 已拆分`（自证样本）。
  - `done.md` 特别：done checklist 新增一条 "id + title 硬门禁校验：本需求产出文档首次提到工作项时均带 title"。
- **验证方式**：
  - 对每个文件 `grep -E "（.*title.*）|（.+）" {file}` 命中至少 1 行新样本。
  - `done.md` grep "id + title 硬门禁" 命中。

### Step 3: 更新 `technical-director.md` briefing 模板

- **操作意图**：subagent 接收 briefing 后无需额外查 title（场景 4）。
- **涉及文件**：`.workflow/context/roles/directors/technical-director.md`（约 113 行附近 "subagent briefing" 段）。
- **关键代码思路**：
  - 原有 briefing 示例（如 `current_requirement: req-XX`）追加 `current_requirement_title: {title}` 字段；briefing 正文段示范写 "本次任务目标：{id}（{title}）的 XXX 工作"。
  - 在 briefing 模板开头加注脚："所有 subagent 的 briefing 必须同时提供 id 与 title（req-30 契约 7）"。
- **验证方式**：`grep -n "current_requirement_title" .workflow/context/roles/directors/technical-director.md` 命中。

### Step 4: 更新 `.workflow/state/experience/index.md` 校验规则

- **操作意图**：让新增经验条目被强制带 title 粒度来源。
- **涉及文件**：`.workflow/state/experience/index.md`（在"经验沉淀规范"章节下添加）。
- **关键代码思路**：
  - 新增小节 `### 来源字段校验规则（req-30 契约 7）`：
    - 规则：新增经验文件的"来源"段必须写 `req-XX（title）chg-XX` 级别；裸 `req-XX` 视为违规。
    - 示范：
      - 正例：`req-29（批量建议合集 2 条）chg-04`
      - 反例：`req-29 chg-04`
    - 规则生效时机：本次提交之后的**新增 / 修改**条目（R4 缓解）；存量条目按需补。
- **验证方式**：`grep -n "来源字段校验规则" .workflow/state/experience/index.md` 命中。

### Step 5: 示范性回填 `.workflow/context/experience/roles/planning.md` 来源段

- **操作意图**：至少 1 份经验文件作为"新约定"示范样本。
- **涉及文件**：`.workflow/context/experience/roles/planning.md`（现有"功能 + bugfix 合集需求的 change 拆分范式"经验的"来源"段，约第 42 行）。
- **关键代码思路**：
  - 原：`req-29 — sug-01（ff --auto）+ sug-08（archive 判据）合集，5 个 change 并行 + 最后 smoke 收尾`。
  - 改为：`req-29（批量建议合集 2 条）— sug-01（ff --auto）+ sug-08（archive 判据）合集，5 个 change 并行 + 最后 smoke 收尾`。
- **验证方式**：`grep -n "req-29（" .workflow/context/experience/roles/planning.md` 命中。

### Step 6: 编写对人文档"变更简报.md"并自证样本

- **操作意图**：按 `planning.md` 角色退出条件，每个 change 都要产出 `变更简报.md`。作为 AC-10 自证。
- **涉及文件**：
  - `artifacts/main/requirements/req-30-slug沟通可读性增强-全链路透出title/changes/chg-01-state-schema-title冗余字段/变更简报.md`
  - `artifacts/main/requirements/req-30-slug沟通可读性增强-全链路透出title/changes/chg-02-cli-render-work-item-id-helper/变更简报.md`
  - `artifacts/main/requirements/req-30-slug沟通可读性增强-全链路透出title/changes/chg-03-role-contract-experience-index-title硬门禁/变更简报.md`
  - （chg-04 独立文件，在 chg-04 内产出）
- **关键代码思路**：
  - 按 `planning.md` "对人文档输出" 章节的最小字段模板（`# 变更简报：{chg-id} {title}` + 变更名 / 解决什么问题 / 怎么做 / 影响范围 / 预期验证）。
  - 首次提到 req-30 时写 `req-30（slug 沟通可读性增强：全链路透出 title）`（契约 7 自证）。
  - ≤ 1 页。
- **验证方式**：
  - 每个 change 目录下存在 `变更简报.md`；首行格式符合 `# 变更简报：{chg-id} {title}`。
  - grep `req-30（slug` 命中首次出现行。

### Step 7: 校验 & 自证

- **操作意图**：把契约 7 的 grep 校验跑一遍，确认本 change 产出的全部文档都符合约定。
- **涉及文件**：全部 Step 1-6 产出文件。
- **关键代码思路**：
  - 组合 grep：`grep -nE "(req|chg|sug|bugfix|reg)-[0-9]+" artifacts/main/requirements/req-30-*/ --include=*.md -r`，目视检查首次命中行都有 `（...）` 括号结构。
- **验证方式**：无回归；如发现漏写 title 的点，原地 Edit 修正。

## 2. Verification Steps

### 2.1 Document / static checks

- `grep -n "契约 7" .workflow/context/roles/stage-role.md` 命中。
- `grep -l "{id}（{title}）\|req-30（\|chg-0.（" .workflow/context/roles/*.md` 涉及的 7 stage + director 文件均命中。
- `grep -n "来源字段校验规则" .workflow/state/experience/index.md` 命中。
- `grep -n "req-29（批量建议合集" .workflow/context/experience/roles/planning.md` 命中。
- 每个 chg 目录下 `变更简报.md` 存在，首行格式正确。

### 2.2 Manual review

- 读一遍 `stage-role.md` 契约 7 全文，确认规则 / 校验方式 / fallback 三段俱全。
- 随机抽查 2 个 stage 角色文件的新增样本行，确认措辞自然、不破坏原有章节结构。
- 读一遍 `technical-director.md` 的 briefing 模板，确认字段示范完整。

### 2.3 AC Mapping

- AC-01 → Step 1（契约 7）+ Step 2（7 stage 样本）+ Step 3（director briefing）。
- AC-02 → Step 2（旧模板更新）+ Step 3（director 模板）。
- AC-08 → Step 4（index.md 校验规则）+ Step 5（planning.md 经验回填示范）。
- AC-10（自证）→ Step 6（变更简报.md）+ 本 change.md / plan.md 全部引用带 title。

## 3. 执行依赖顺序

1. **前置推荐**：chg-01 + chg-02 已落地。理由见 R1 缓解。
2. Step 1 先：契约 7 是其他 Step 的规则源。
3. Step 2 / 3 / 4 / 5 / 6 可并行，但 Step 2 和 Step 6 有一些互相参考（变更简报的模板复用 planning.md 已有段落）。
4. Step 7 最后统一校验。
5. **可选前置**：用户可在 chg-01 / chg-02 未完成时独立推进 chg-03（契约与代码解耦）；本 change 内容不 import 任何代码。

## 4. 回滚策略

- **粒度**：每个 Step 一个 commit；契约 7（Step 1）必须独立提交以便审查。
- **回滚触发**：
  - 契约 7 措辞引发歧义（reviewer 发现与契约 1-6 冲突）→ 按 R3 缓解重写契约 7 开头注脚；必要时 revert Step 1，单独迭代。
  - 7 stage 角色文件改动破坏已有章节结构 → 单文件回滚，保留其他 6 个文件的改动。
  - Step 6 变更简报内容有误 → 直接 Edit 修正，不需要 revert（对人文档非代码）。
- **兜底**：所有修改都是文档（`.md`）+ yaml frontmatter；`git revert` 可完整回滚，无代码副作用。

## 5. 风险表

| 风险 ID | 风险描述 | 缓解措施 |
|---------|---------|---------|
| R1 | 契约 7 生效时机与 CLI 行为（chg-02）不同步 | 推荐顺序 chg-02 → chg-03；契约 7 注脚"生效时机 = chg-02 完成后" |
| R2 | 9 个角色文件同时改，diff 污染 | 单文件 1 commit；PR description 附改动清单 |
| R3 | 契约 7 与契约 1-6 语义冲突 | 契约 7 开头显式"并列生效不覆盖" |
| R4 | 校验规则影响历史经验条目 | 规则只作用于新增 / 修改（index.md 显式写明） |
| R5 | AC-10 自证样本漂移（后续 executing / testing 等阶段漏写 title） | session-memory 交接事项明确要求；done 阶段六层回顾作为最终拦截 |
| R6 | 契约 7 的 grep 校验对首次 / 非首次的识别不准（误报率高） | 允许 done reviewer 目视复核；后续 sug 可做更精细的 lint 工具 |
