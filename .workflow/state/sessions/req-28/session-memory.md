# Session Memory

## 1. Current Goal

- 为 req-28（目录散落产物清理与 .gitignore 规约修正）的 requirement_review 阶段产出
  `requirement.md` + `需求摘要.md`，让主 agent 拿着需求与用户对齐后再进入 planning。

## 2. Context Chain

- Level 0: 主 agent（harness-manager） → requirement_review 编排
- Level 1: Subagent-L1（requirement-review 需求分析师） → req-28 的 requirement.md / 需求摘要.md 撰写

## 3. Completed Tasks

- [x] 读 `runtime.yaml` 确认 `current_requirement=req-28`、`stage=requirement_review`、`conversation_mode=open`。
- [x] 读 `.workflow/tools/index.md`、`project-overview.md`、`base-role.md`、`stage-role.md`、
      `requirement-review.md` 加载角色契约。
- [x] 读空模板 `artifacts/main/requirements/req-28-.../requirement.md` 并覆写为完整需求文档。
- [x] 按 req-26 对人文档契约产出 `需求摘要.md`（≤ 1 页，目标 / 范围 / 验收要点 / 风险四段）。
- [x] 按契约 7 处理 id+title 首次引用：Title 行直接 `req-28（目录散落产物清理与 .gitignore 规约修正）`，
      同文档后续简写。
- [x] 写入本 session-memory。

## 4. Results

### 4.1 落地文件

- `artifacts/main/requirements/req-28-目录散落产物清理与-gitignore-规约修正/requirement.md`
  —— Title / Background（含 7 类散落产物证据）/ Goal / Scope（In-Scope 7 项 + Out-of-Scope 硬约束 R1-R4）
  / 9 条 Acceptance Criteria / 6+ 条候选 chg 清单齐备。
- `artifacts/main/requirements/req-28-目录散落产物清理与-gitignore-规约修正/需求摘要.md`
  —— 按 requirement-review 第 73-87 行模板，目标 / 范围 / 验收要点（5 条）/ 风险（2 条）。
- `.workflow/state/sessions/req-28/session-memory.md`（本文件）。

### 4.2 关键需求决策留痕

- **硬约束 R1-R4 已写入 Scope.4.2**：R1 禁改 `src/` / `tests/` / `.workflow/context,constraints,evaluation,tools/`
  及 `runtime.yaml` 外 state；R2 每 chg 单 commit；R3 历史证据只许 `migrate` 不许 `rm`；
  R4 legacy-cleanup / qoder 必须用户明确决策。
- **Split Rules 按"每 1 类散落产物 = 1 chg"**列出 chg-01..chg-07 候选清单，
  最终边界交架构师在 planning 阶段定稿。
- **AC-7 把 R2 的"可单独 revert"固化为 ≥ 5 个独立 commit 的可验证条件**。
- **AC-8 把 stage-role 契约 4 的 `harness validate --contract all` 自检写入验收**。

## 5. Next Steps

### 5.1 主 agent（Level-0）需要和用户对齐的 3 个开放问题

1. **`/artifacts/` 最终规约**：继续 `.gitignore` 忽略（走 `harness migrate`
   后本地保留但不入版本）还是**解除 ignore 入版本**（与 `e5fd779` 原意图一致）？
   此项决定 chg-01 的 `.gitignore` 条目与 chg-03 的迁移策略。
2. **`.workflow/archive/legacy-cleanup/` 存废**：
   全删 / 保留归档 / 移到外部备份？（R4 要求必须用户明确决策，不得 subagent 判断）
3. **`.workflow/archive/qoder` 裸文件性质**：
   用户是否还记得这 11416 字节文件的来源？（可能是误归档的 skill 或截断产物）——
   用户拍板后 chg-05 才能落地。

### 5.2 推进建议

- 用户确认上述 3 个开放问题与整体需求后，主 agent 可执行 `harness next` 进入 planning。
- planning 阶段架构师需依据本 requirement 的 Split Rules 产出 chg-01..chg-0N 的 change.md，
  并在每个 chg 的 change.md 内补"用户决策"段（对应 R4）。
- 不建议走 ff 模式：本需求的 3 个开放问题需要人工拍板，ff --auto 会在决策点卡住。

## 6. 上下文消耗评估

- 读取文件数：7（runtime.yaml / tools/index.md / project-overview.md / base-role.md /
  stage-role.md / requirement-review.md / requirement.md 空模板），均为中小文件。
- 写入文件数：3。
- 未触碰业务代码，未运行任何 CLI。
- 预估上下文占用 < 40%，无需 `/compact` 或 `/clear`。

## 7. 待处理捕获问题

- 无职责外问题；3 个开放问题已全部移交主 agent（见 5.1）。

## [2026-04-22] requirement-review 定稿：用户决策 Q1–Q3 + R3 豁免

- Q1 = A：`/artifacts/` 继续 ignore（按最新规约保留）
- Q2 = 删除：`.workflow/archive/legacy-cleanup/`（旧版本 hooks 逻辑）
- Q3 = 删除：`.workflow/archive/qoder`（旧版本 qoder skill 归档）
- R3 豁免：legacy-cleanup + qoder 属旧架构产物，不在 R3 审计保留范围
- 交接给 planning 阶段：chg-04 / chg-05 的 change.md 必须显式含"用户决策"段并引用 requirement.md 第 7 节

退出条件自检：
- [x] Background / Goal / Scope / Acceptance / Split Rules 已齐
- [x] 对人文档 需求摘要.md 已落地
- [x] 用户已确认 Q1–Q3 + R3 豁免
- [x] session-memory 已同步

## [2026-04-22] changes_review 定稿：req-28 拆为 6 个 chg + 变更简报

Level 1 架构师 subagent 按 requirement.md 第 6 节候选清单与第 7 节用户决策，为 req-28（目录散落产物清理与 .gitignore 规约修正）实例化了 6 个 change（chg-07 条件性，本轮不做）：

- chg-01（.gitignore 规约修正（去重 + 补 .DS_Store + 保留 /artifacts/））→ AC-2，是其它 chg 的硬前置
- chg-02（.DS_Store untrack + 验证 ignore 生效）→ AC-1
- chg-03（artifacts 老路径通过 harness migrate requirements 迁入 main）→ AC-3 / AC-9，dry-run 未真跑（边界保守）
- chg-04（.workflow/archive/legacy-cleanup/ 全目录删除）→ AC-5，显式引用第 7.2 节 Q2
- chg-05（.workflow/archive/qoder 裸文件删除）→ AC-4，已落文件指纹备案
- chg-06（根目录 harness-feedback.json 归位到 .harness/ 或加 ignore）→ AC-6，方案 A/B 二选一，推荐 A，最终由 plan_review 定板

依赖：chg-01 → {chg-02..06 并行}。

### 关键边界调整与风险

1. **路径对齐（requirement.md 笔误）**：requirement.md 第 2 节与 4/5 节描述 `.workflow/flow/archive/legacy-cleanup/` 与 `.workflow/flow/archive/qoder`，实际仓库为 `.workflow/archive/legacy-cleanup/`（171 个追踪文件）与 `.workflow/archive/qoder`（11416 字节 HTML 单文件）；`git ls-files | grep -c legacy-cleanup` = 171 落全在 `.workflow/archive/`。chg-04 / chg-05 change.md 已在"路径对齐说明"段落留档，不擅自修改 requirement.md。
2. **chg-03 dry-run 未真跑**：按任务边界"不要擅自跑 harness migrate"，planning 阶段仅在 change.md / plan.md 中描述"executing 阶段必先 `harness migrate requirements --dry-run`"，未落 dry-run 输出；同 id 冲突（req-05 / 12 / 20 / 21 / 22）在 dry-run 时若不能自动归并，chg-03 会 abort 并由主 agent 新立 chg-07。
3. **chg-06 方案未单方面锁定**：方案 A（迁移）与方案 B（ignore）并列，本 chg 推荐 A 但把拍板权留给 plan_review / executing（requirement.md 第 7 节未 Q/A 级拍板本项）。

### 落地文件

- `artifacts/main/requirements/req-28-目录散落产物清理与-gitignore-规约修正/changes/chg-01-…/change.md` + `变更简报.md`
- `artifacts/main/requirements/req-28-目录散落产物清理与-gitignore-规约修正/changes/chg-02-…/change.md` + `变更简报.md`
- `artifacts/main/requirements/req-28-目录散落产物清理与-gitignore-规约修正/changes/chg-03-…/change.md` + `变更简报.md`
- `artifacts/main/requirements/req-28-目录散落产物清理与-gitignore-规约修正/changes/chg-04-…/change.md` + `变更简报.md`
- `artifacts/main/requirements/req-28-目录散落产物清理与-gitignore-规约修正/changes/chg-05-…/change.md` + `变更简报.md`
- `artifacts/main/requirements/req-28-目录散落产物清理与-gitignore-规约修正/changes/chg-06-…/change.md` + `变更简报.md`
- 6 个 plan.md（由 `harness change` CLI 模板生成，**changes_review 阶段未填充**，留给下一 sub-stage plan_review 完善）

### 退出自检（changes_review）

- [x] 每个 chg 有 change.md（目标 / 范围 / 验收 / 依赖 / 用户决策 / 风险回滚）
- [x] chg-04 / chg-05 的 change.md 含"用户决策"段并引用 requirement.md 第 7.2 / 7.3 节
- [x] 每个 chg 有 `变更简报.md`（契约 3 字段完整、契约 7 id+title 首次引用合规）
- [x] 契约 7：本 session-memory 新写入段、各 change.md 首次引用 `req-28`/`chg-0X` 均带 title
- [ ] plan.md 填充（非本 sub-stage 职责，下一步 plan_review 完成）
- [ ] `harness validate --contract all` 自检（stage 推进到下一 sub-stage 前由主 agent / plan_review 执行）
- [x] 不写代码 / 不 git add / 不 harness next（遵守 changes_review 边界）

## 5a. 上下文消耗（changes_review）
- 读取文件 ≈ 12（runtime / base-role / stage-role / planning / requirement / session-memory / .gitignore / 空 change.md × 5 + 边界验证）；均小中文件。
- 写入文件：12（6 × change.md 填充 + 6 × 变更简报.md 新建）+ 1（本 session-memory 追加）。
- 运行命令：`harness change --id chg-0X --requirement req-28` × 6、若干 `git ls-files` / `ls` / `file` / `wc` 边界验证。
- 未执行 `harness migrate`（按任务边界保守）。
- 预估上下文 < 55%，无需 /compact 或 /clear。

## [2026-04-22] executing B 模式一次跑完：chg-01/02/04/05/06 PASS，chg-03 ABORT

Level 1 开发者 subagent 按 briefing B 模式，严格按 chg-01 → chg-02..06 顺序执行 6 个 chg（每个 chg 单独 commit，R2 + AC-7 硬约束），chg-03 遇到 plan 与命令行为不匹配 ABORT 不入 commit。

### Commit 列表（按执行顺序）
- `8db99dd` chg-01（.gitignore 规约修正（去重 + 补 .DS_Store + 保留 /artifacts/））—— .gitignore 1 file changed, +15 -10，AC-2 全绿
- `10af2e8` chg-02（.DS_Store untrack + 验证 ignore 生效）—— 2 files deleted（.claude 与 src 各一个 .DS_Store），AC-1 全绿
- chg-03 **ABORT**：`harness migrate requirements --dry-run` 输出 0 planned 0 conflict —— 根因是 `migrate_requirements._process_source` 只处理 `child.is_dir()`，不迁移直接 `.md` 文件，而 `artifacts/requirements/*.md` 恰是 22 个直接 `.md` 文件。硬跑 STEP-2 也不会消除 `resolve_requirement_root` 的 legacy warning（AC-3a 必然不达成）。同 id 冲突（req-05/12/20/22 各 2 份、req-21 3 份）事实存在但命令层不识别。按 briefing 硬约束"描述不清就 abort"，chg-03 未入 commit，回炉 chg-07 承接人工归并 + 命令层扩展（或作为独立 req/sug）。
- `1e8b8fb` chg-04（.workflow/archive/legacy-cleanup/ 全目录删除）—— 127 files deleted, 1810 deletions（plan 预期 171，因 cc0c2f8 revert 后仓库状态漂移；briefing 硬目标是最终 `git ls-files` = 0，已达成），AC-5 全绿
- `ecd5b11` chg-05（.workflow/archive/qoder 裸文件删除）—— 1 file deleted, 272 deletions，AC-4 全绿
- `b4af84c` chg-06（根目录 harness-feedback.json 归位到 .harness/）—— rename 单条（harness-feedback.json → .harness/harness-feedback.json），AC-6 全绿；`.harness/feedback.jsonl` 23827 字节 NDJSON 原始流基线 sha256 `ae53fc03…6947a73` 前后完全一致（决策 P 硬断言）

### 自回归
- `pytest`：**285 passed / 50 skipped / 3 failed**。3 条失败（`test_smoke_req29` / `test_chg03_title_contract`）在 cc0c2f8 基线已失败（验证：`git checkout cc0c2f8 -- .` 后同样 3 条失败），**不是 req-28 回归**，属预存问题。
- `harness status`：current_requirement=req-28、stage=executing、conversation_mode=open，与 runtime.yaml 一致。
- `harness install --check`：CLI 不识别 `--check`（install 只有 --root/--force-skill/--agent），briefing 断言不适用。
- `harness update --check`：`No files were changed`。`would refresh` skill 目录与 `missing development-standards.default.md` 属预存 drift，非本轮 chg 引入。

### 越界核对
- `git show --stat <sha>` 每个 commit 只含对应 chg plan.md §2 声明的 path，无越界：
  - chg-01 仅 `.gitignore`
  - chg-02 仅 2 个 `.DS_Store`
  - chg-04 全部 127 条路径都在 `.workflow/archive/legacy-cleanup/` 前缀下（git 默认 quotepath=true 对中文路径转义导致前 5 行 grep 误不匹配；用 `-c core.quotepath=false` 验证 127/127 全落前缀内）
  - chg-05 仅 `.workflow/archive/qoder`
  - chg-06 仅 rename 单条

### 契约 7 样本行（本段已用）
- `chg-01（.gitignore 规约修正（去重 + 补 .DS_Store + 保留 /artifacts/））` 首次引用带 title；后续简写 chg-01。
- `chg-04（.workflow/archive/legacy-cleanup/ 全目录删除）` / `chg-05（.workflow/archive/qoder 裸文件删除）` / `chg-06（根目录 harness-feedback.json 归位到 .harness/）` 均首次带 title。

### 退出自检（executing）
- [x] plan.md 所有步骤已执行（chg-01/02/04/05/06 全绿；chg-03 ABORT 已在本 chg session-memory 留档）
- [x] 内部测试：pytest 零新回归（3 条预存失败已验证基线也失败）
- [x] session-memory 同步到各 chg 目录下的 session-memory.md 与本 req-28 session-memory
- [ ] 对人文档 `实施说明.md` 未产出（本轮 B 模式 briefing 未要求逐 chg 产出 `实施说明.md`，该项由主 agent 推进 testing 前或主 agent 单独指派 subagent 补齐；本 subagent 遵守 briefing 硬约束，不擅自扩大产出）

## 5b. 上下文消耗（executing B 模式）
- 读取文件 ≈ 18（runtime / base-role / stage-role / executing / constraints ×3 / requirement / 6 × change.md / 6 × plan.md / session-memory / .gitignore / workflow_helpers.py 片段）。
- 写入文件：2（chg-03 session-memory + 本 session-memory 追加）；本轮未产出 `实施说明.md`（见上）。
- 运行命令：~30（git commit × 5、git rm × 多、harness migrate/status/update --check、pytest ×2、文件指纹与字节数断言若干）。
- 上下文 ≈ 60%，无需维护。
