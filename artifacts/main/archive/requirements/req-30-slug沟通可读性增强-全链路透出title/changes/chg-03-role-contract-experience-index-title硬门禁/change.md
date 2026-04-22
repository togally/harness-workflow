# Change

## 1. Title

chg-03（角色契约 + 索引硬门禁）：`stage-role.md` 新增"id + title 硬门禁" + 7 stage 角色汇报模板 + `technical-director` briefing + `experience/index.md` 来源校验

## 2. Background

源自 req-30 方案 B 的 **L1 层目标**（Agent 输出 / 汇报模板）与 **L4 索引部分**，覆盖 **AC-01 / AC-02 / AC-08**：

- 现状：`.workflow/context/roles/stage-role.md` 已有"对人文档输出契约"章节（`req-26 / sug-06`），约束了对人文档名称与路径，但**没有对工作项 id 的引用格式做硬门禁**——agent 可以自由写 `req-29 已完成`，裸 id 不会被拦截。
- 各 stage 角色文件（`requirement-review.md` / `planning.md` / `executing.md` / `testing.md` / `acceptance.md` / `regression.md` / `done.md`）的"汇报 / 输出示例"章节普遍缺少 `{id}（{title}）` 格式样本。
- `technical-director.md` 派发 subagent 的 briefing 模板（约第 113 行附近）只提 id，不带 title，subagent 接收后第一件事还得反查 title（场景 4）。
- `.workflow/state/experience/index.md` 的"来源"列当前只写 `req-07 chg-04` 级 id（AC-08 要求升格到带 title 粒度）；新增经验条目无硬校验规则。

## 3. Goal

把"id + title 同时出现"从**软约定**升格为**契约硬门禁**，并让未来所有新写入的对人文档、subagent briefing、experience/index.md 新增条目都被契约强制覆盖：

- `stage-role.md` 新增一节"**对人文档输出契约 — id + title 硬门禁**"（或并入契约 4 作为子条款），明确："所有对人 / 跨 agent 的输出中，工作项 id **首次出现**必须形如 `{id}（{title}）`，裸 id 视为违规"；done 阶段的六层回顾清单包含一条 grep 校验。
- 7 个 stage 角色文件各自的"汇报 / 输出示例"章节补 `{id}（{title}）` 模板示范（至少一条示例行）。
- `technical-director.md` 的 "subagent briefing 模板" 章节补 `current_requirement` + `current_requirement_title` 双字段示范。
- `.workflow/state/experience/index.md` 新增条目校验规则：来源列必须写 `req-XX（title）chg-XX` 粒度，裸 `req-XX` 视为违规；并对现有经验文件的"来源"段提供新示范格式。
- **自证样本**：本 change 的 `change.md` / `plan.md`、本需求 req-30 自身的 `需求摘要.md`、以及后续 `实施说明.md` / `变更简报.md`，均按新契约写作（首次提到工作项时带 title），作为"新约定"的示范样本，done 阶段六层回顾点名验证（**AC-10 自证**）。

## 4. Requirement

- `req-30`

## 5. Scope

### 5.1 In scope

- **`.workflow/context/roles/stage-role.md`**：
  - 在"对人文档输出契约"章节下新增"契约 7：id + title 硬门禁"子节，明确：
    - 所有对人 / 跨 agent 的文档（session-memory / done-report / briefing / 对人文档 / action-log）中，工作项 id **首次出现**必须形如 `{id}（{title}）`；同上下文后续可简写回 id。
    - 校验方式：done 阶段六层回顾 grep 每个对人文档首段，无 title 视为硬门禁违反（`harness status --lint` 或 done checklist 的 validator）。
    - 缺失 title 的 fallback：若 title 暂时未定（极少数新建瞬间），允许写 `{id}（pending-title）` 但 done 阶段必须修正。
  - 保留并引用 `req-26 / sug-06` 既有契约 1-6（不覆盖）。
- **`.workflow/context/roles/requirement-review.md` / `planning.md` / `executing.md` / `testing.md` / `acceptance.md` / `regression.md` / `done.md`**：每个文件在"汇报模板"或"对人文档示例"章节增加 `{id}（{title}）` 模板行。具体编辑点：
  - `requirement-review.md`：对人文档 `需求摘要.md` 首行 `# 需求摘要：{id} {title}` 格式（已存在，本 change 显式在角色文档中强调此格式是硬门禁）。
  - `planning.md`：对人文档 `变更简报.md` 首行 `# 变更简报：{chg-id} {title}` 强调（模板中已有 `{chg-id} {title}`，本 change 加硬门禁注脚）。
  - `executing.md`：对人文档 `实施说明.md` 首行约定 + "向 testing 交接" 汇报模板带 title。
  - `testing.md` / `acceptance.md` / `regression.md`：汇报段示例统一升格。
  - `done.md`：done 报告与"转 suggest 池"条目的格式示例升格；done checklist 加 "id + title 硬门禁校验通过" 项。
- **`.workflow/context/roles/directors/technical-director.md`**：
  - "subagent briefing 模板" 章节（约 113 行附近）示范中的 `current_requirement: req-XX` 改为 `current_requirement: req-XX` + `current_requirement_title: {title}`（双字段示范）；同时在 briefing 正文段补 "本次任务目标：{id}（{title}）的 XXX 工作" 格式。
- **`.workflow/state/experience/index.md`**：
  - 在"经验沉淀规范"下新增"来源字段校验规则"：新增经验文件的"来源"段必须写 `req-XX（title）chg-XX` 级别，裸 id 视为违规。
  - 提供一个正例 + 反例短示范（≤4 行），便于 grep 断言。
- **经验文件回填示范（≥1 份）**：更新 `.workflow/context/experience/roles/planning.md` 已有经验"功能 + bugfix 合集需求的 change 拆分范式"的"来源"段，从 `req-29` 改为 `req-29（批量建议合集 2 条）`；作为本次契约的自证样本。
- **本 change 的自证**：本 `change.md` / `plan.md` / 后续 `变更简报.md` 都按新契约写作，首次提到 req-30 时带完整 title。

### 5.2 Out of scope

- 不改 CLI 代码（render 由 chg-02 负责）。
- 不改 runtime.yaml 字段（由 chg-01 负责）。
- 不做批量回填所有历史 experience 文件的"来源"段（只做 1 份示范；历史条目按"新增时校验、存量按需补"策略）。
- 不实现 `harness status --lint` 工具（作为后续 sug 登记）。
- 不改 `harness-manager.md` / `tools-manager.md` / `reviewer.md`（本 change 只改 7 个 stage 角色 + director + stage-role；辅助角色的模板更新作为后续 sug）。
- 不改归档目录 `_meta.yaml`（由 chg-04 可选负责）。

## 6. Definition of Done（≥3 条）

1. **DoD-1**：`.workflow/context/roles/stage-role.md` 的"契约 7：id + title 硬门禁"章节已新增，包含"规则 + 校验方式 + fallback"三段，`grep -n "契约 7" stage-role.md` 命中。
2. **DoD-2**：7 个 stage 角色文件（requirement-review / planning / executing / testing / acceptance / regression / done）每个都含至少 1 行 `{id}（{title}）` 格式示例（grep `（{title}）` 或 `{id}（` 模式命中）。
3. **DoD-3**：`.workflow/context/roles/directors/technical-director.md` 的 briefing 模板同时含 `current_requirement` 和 `current_requirement_title` 两字段示范。
4. **DoD-4**：`.workflow/state/experience/index.md` 新增"来源字段校验规则"段；至少 1 份经验文件（planning.md）的"来源"段按新格式改写。
5. **DoD-5**：本 change 产出的 `change.md` / `plan.md` / 变更简报.md 首次提到 req-30 时均带完整 title，可作为自证样本被 done 阶段点名验证（AC-10）。

## 7. 关联 AC

| AC | 说明 | 本 change 覆盖方式 |
|----|------|-----------------|
| AC-01 | session-memory / done-report / briefing / acceptance 报告中 id 首次出现必须带 title | stage-role.md 契约 7 + 7 stage 角色模板 + director briefing |
| AC-02 | 旧模板已更新 | 7 个 stage 角色文件"汇报模板"章节编辑 + stage-role.md 契约 7 |
| AC-08 | experience/index.md 来源列带 title | `.workflow/state/experience/index.md` 新增校验规则 + planning.md 经验来源回填示范 |
| AC-10（自证） | req-30 自身文档作为新约定示范样本 | 本 change 的文件（change.md / plan.md / 变更简报.md）首次引用 req-30 时带 title，done 阶段点名验证 |

## 8. 依赖 / 顺序

- **本 change 不强制依赖 chg-01 / chg-02**：契约更新可与代码层并行推进。
- **推荐顺序**：chg-01 → chg-02 → **chg-03** → chg-04。理由：chg-02 落地后 agent 能直接复制 CLI 输出的 `req-30（...）` 作为样本；chg-03 更新契约时，新契约与 CLI 行为一致，不会自相矛盾。
- **自证依赖**：本 change 的文档本身是对契约的示范，落地顺序应当在 chg-01 / chg-02 之后（避免契约文档说 "CLI 会渲染带 title"，但 CLI 代码还没改）。

## 9. 风险与缓解

- **R1 契约与 CLI 不同步**：若 chg-03 先落地（契约说 `{id}（{title}）`），但 chg-02 未落地（CLI 仍裸打 id），用户会看到契约与 stdout 不一致的观感。
  - **缓解**：推荐顺序 chg-02 → chg-03；若 ff 模式下 chg-03 先跑完，在本 change 中注明"本契约生效时机 = chg-02 完成 + CLI 输出已带 title"；done 阶段六层回顾统一校验。
- **R2 角色文件改动过多造成 diff 污染**：7 个 stage 角色 + director + stage-role = 9 个文件同时改，reviewer 难审。
  - **缓解**：executing 阶段按"单文件 1 commit"拆分，每个 commit 说明改了哪段；PR description 附改动清单；done 阶段 reviewer 检查每个文件至少含 1 行新模板示例。
- **R3 契约 7 与契约 1-6 冲突**：既有契约已规定对人文档名与路径，契约 7 新增"id + title 硬门禁"可能被理解为覆盖。
  - **缓解**：在契约 7 开头显式写 "本契约与契约 1-6 并列生效，不覆盖既有约束；仅对 id 引用格式做强制约束"。
- **R4 experience/index.md 校验规则影响历史文件**：若新规则过严，所有历史经验文件将全部视为违规。
  - **缓解**：明确"新增时校验、存量按需补"策略（req-30 AC-08 已写明）；在 index.md 校验规则段显式标注"规则仅对本次提交之后的新增/修改条目生效"。
- **R5 AC-10 自证样本漂移**：后续 chg-04 / 实施说明 / 交付总结若未按新契约写，AC-10 会失败。
  - **缓解**：本 change 的 session-memory 交接事项中，明确"后续 executing / testing / acceptance / done 阶段的所有对人文档首次提到 req-30 时必须带 title"；done 阶段六层回顾作为最终拦截点。
