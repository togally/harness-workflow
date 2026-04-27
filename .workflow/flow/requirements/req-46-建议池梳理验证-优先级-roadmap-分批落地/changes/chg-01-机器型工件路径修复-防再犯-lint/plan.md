# Change Plan

## 1. Development Steps

> 每步可被 executing 角色（sonnet）直接执行；步骤号在 session-memory.md 复用以标 ✅/❌。

### Step 1：物理回归 4 个机器型工件（git mv）

- 在 git 树根执行以下 4 条 `git mv`，把 req-46 现场 4 件机器型工件从 `artifacts/main/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/` 回 `.workflow/flow/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/`：
  ```bash
  git mv artifacts/main/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/requirement-review/session-memory.md \
         .workflow/flow/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/requirement-review/session-memory.md
  git mv artifacts/main/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/requirement-review/sug-audit.md \
         .workflow/flow/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/requirement-review/sug-audit.md
  git mv artifacts/main/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/planning/session-memory.md \
         .workflow/flow/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/planning/session-memory.md
  git mv artifacts/main/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/planning/roadmap.md \
         .workflow/flow/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/planning/roadmap.md
  ```
- 清理空 stage 子目录：`rmdir artifacts/main/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/{requirement-review,planning}` （仅当目录已空时；若有遗留文件先逐一审视）。
- **保留**：`artifacts/main/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/requirement.md`（§2 白名单 raw 副本）+ `.workflow/flow/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/requirement.md`（机器型权威）。
- 产出：4 个文件 `git mv` 到位 + 2 个空目录清理；`git status` 应只显示 4 条 renames + 2 条目录删除。

### Step 2：harness-manager.md 派发协议加 expected_artifact_paths 字段

- 编辑 `.workflow/context/roles/harness-manager.md` §3.6 派发协议章节：
  - 新增条款："派发任意 stage 角色（含 analyst / executing / testing / acceptance / regression / done）时，briefing JSON 必须显式列出该 stage 工件期望落点路径，键名 `expected_artifact_paths`，值为路径数组（按 stage + req-id + chg-id 由 dispatcher 计算）。"
  - 给出 analyst 派发示例：`expected_artifact_paths: [".workflow/flow/requirements/{req-id}-{slug}/requirement.md", ".workflow/flow/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/change.md", ".workflow/flow/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/plan.md", ".workflow/flow/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/session-memory.md"]`。
  - 字段先以**可选**形态引入，subagent 端不强校验，规避存量派发链路破坏（见 change.md §6 风险 3）。
- 同步 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` 同字段（见 Step 7）。

### Step 3：analyst.md / stage-role.md 加路径自检硬门禁

- 编辑 `.workflow/context/roles/analyst.md`：
  - §硬门禁 章节新增一条："**路径自检硬门禁**：产出任何 stage 工件前必读 `repository-layout.md` §3 路径表，对照确认落点；session-memory / 工作产出（sug-audit / roadmap / 等）必落 `.workflow/flow/requirements/{req-id}-{slug}/{stage}/` 或对应 `changes/{chg-id}-{slug}/` 子目录，**禁止**落 `artifacts/main/requirements/{req-id}-{slug}/{stage-name}/`。"
- 编辑 `.workflow/context/roles/stage-role.md`：
  - 契约 2（路径同构）下方加 SOP 检查点："**路径自检（操作层）**：subagent 在产出每件工件前，对照 `repository-layout.md` §3 路径表确认机器型 vs 对人型分类，机器型必落 `.workflow/flow/`，对人型仅限 §2 白名单且必落 `artifacts/{branch}/`。"
- 同步 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md` + `.../stage-role.md` 同变更。

### Step 4：升级 src/harness_workflow/validate_contract.py::check_artifact_placement

- 升级 `src/harness_workflow/validate_contract.py`（行 457-535 区域）：
  - **新增规则 0（路径模式扫）**：扫 `artifacts/main/requirements/{req-id}-{slug}/` 下任何 stage-name 子目录（白名单 = `requirement-review` / `planning` / `executing` / `testing` / `acceptance` / `done` / `regression` / `regressions`）→ FAIL 并报 `artifacts/ 下发现 stage-name 子目录：{path}`；
  - **修复白名单豁免**：`_MACHINE_TYPE_FILENAMES` 内 `requirement.md` 在 `artifacts/main/requirements/{req-id}-{slug}/requirement.md` 路径模式（恰为 §2 白名单 raw 副本位）下豁免，不命中 FAIL；
  - **扩展 `_MACHINE_TYPE_FILENAMES`**：加入 `sug-audit.md` / `roadmap.md`（req-46 现场遇到的工作产出文件名；后续 sug 沉淀更多按需加）；
  - 错误消息保持现有格式（`artifacts/ 下发现机器型文件：{rel}` + `契约引用：repository-layout.md §1 / §4 禁止行为`）。
- 产出：`check_artifact_placement` 函数体扩 ~30 行，加新规则 0 + 修白名单豁免 + 扩 frozenset；`artifacts/.../requirement.md` 不再误命中。

### Step 5：接入 stage 退出门禁

- 编辑 `.workflow/context/roles/analyst.md` 退出条件章节：
  - Part A（req_review）退出条件加：`[ ] harness validate --contract artifact-placement exit code = 0（未绿须 ABORT，不得放行）`；
  - Part B（planning）退出条件加同样一条。
- 编辑 `src/harness_workflow/cli.py` 或 `workflow_next` helper（具体位置 executing 阶段定位）：
  - `harness next` 在 analyst 两个流转点（`requirement_review → planning` / `planning → ready_for_execution`）跑 `check_artifact_placement`，exit ≠ 0 阻塞流转；
- 同步 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md` 同退出条件变更。

### Step 6：reviewer checklist 扩 artifact-placement 反向抽样条目

- 编辑 `.workflow/context/checklists/review-checklist.md` "制品完整性检查专节" → "根目录制品仓库" 子节：
  - 新增条目：`- [ ] artifact-placement 反向抽样（高）：grep 确认 artifacts/main/requirements/{req-id}-{slug}/ 下无 stage-name 子目录（requirement-review/planning/executing/testing/acceptance/done/regression/regressions）+ 无非 §2 白名单文件名。`
  - 同时在 "阶段速查表" → "requirement_review 阶段重点" / "planning 阶段重点" 各加一条 `[ ] artifact-placement 抽样（高）：本 stage 工件落点核查无 artifacts/ 下机器型文件残留。`
- 同步 `src/harness_workflow/assets/scaffold_v2/.workflow/context/checklists/review-checklist.md` 同变更。

### Step 7：scaffold_v2 mirror 同步

- 把以下文件改动镜像到 `src/harness_workflow/assets/scaffold_v2/.workflow/context/`：
  - `roles/harness-manager.md`（Step 2）
  - `roles/analyst.md`（Step 3 + Step 5）
  - `roles/stage-role.md`（Step 3）
  - `checklists/review-checklist.md`（Step 6）
- 必要时同步 `assets/scaffold_v2/.workflow/flow/repository-layout.md`（如需补 stage 级 session-memory 落位段）；本 chg 默认不动 repository-layout.md，仅当 Step 3 / 4 实施过程中发现路径表不完整再回补（视情况记 sug）。
- **同一 commit 同步**（reviewer 拦截硬门禁五）：Step 2/3/5/6 改动与本 Step 7 mirror 同步必须落同一次 commit，禁止分两次提交。

### Step 8：sug-35 状态翻转

- 编辑 `.workflow/flow/suggestions/sug-35-reviewer-checklist-artifact-placement-test-case-design-completeness-lint.md` frontmatter：
  - `status: pending` → `status: archived`
  - 新增 `applied_at: 2026-04-XX`（actual date by executing）
  - 新增 `applied_by_chg: chg-01`
- 按 sug 归档约定迁入 `.workflow/flow/archive/suggestions/`（如 CLI 自动迁则跑 `harness suggest --archive sug-35`，否则手工 `git mv`）。
- **执行时机**：必须在 acceptance PASS 后做（保留追溯链 + 防止 chg 失败时 sug 状态错位）。

### Step 9：测试用例编写 + 跑通

- 按本文件 §4 测试用例设计实现 TC-01 ~ TC-08 用例（pytest fixture + lint binary 调用），落 `tests/test_validate_contract_artifact_placement.py`（沿现有 tests/ 目录约定）；
- 跑通 `pytest tests/test_validate_contract_artifact_placement.py -v` 全绿；
- 跑通全仓库回归 `pytest -q`，确保升级 lint 不破坏既有用例（注意 fixture 内可能有故意构造的 artifacts/ 路径需更新）。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- **静态文件存在断言**：
  - `test -f .workflow/flow/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/requirement-review/session-memory.md` exit 0；
  - `test -f .workflow/flow/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/requirement-review/sug-audit.md` exit 0；
  - `test -f .workflow/flow/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/planning/session-memory.md` exit 0；
  - `test -f .workflow/flow/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/planning/roadmap.md` exit 0；
  - `! test -d artifacts/main/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/requirement-review` exit 0（目录应已 rmdir）；
  - `! test -d artifacts/main/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/planning` exit 0；
  - `test -f artifacts/main/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/requirement.md` exit 0（白名单 raw 副本保留）。
- **lint 跑无违规**：`python3 -m harness_workflow.cli validate --contract artifact-placement` 全仓库扫 exit 0。
- **scaffold_v2 mirror diff**：
  - `diff -rq .workflow/context/roles/ src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/` 无差异；
  - `diff -rq .workflow/context/checklists/ src/harness_workflow/assets/scaffold_v2/.workflow/context/checklists/` 无差异。
- **sug-35 frontmatter 字段断言**：
  - `grep "status: archived" .workflow/flow/archive/suggestions/sug-35-*.md` 命中 1 行；
  - `grep "applied_by_chg: chg-01" .workflow/flow/archive/suggestions/sug-35-*.md` 命中 1 行。
- **角色文件 grep**：
  - `grep "expected_artifact_paths" .workflow/context/roles/harness-manager.md` 命中；
  - `grep "harness validate --contract artifact-placement" .workflow/context/roles/analyst.md` 命中 ≥ 2 行（Part A + Part B）；
  - `grep "路径自检" .workflow/context/roles/stage-role.md` 命中 ≥ 1 行；
  - `grep "artifact-placement 反向抽样" .workflow/context/checklists/review-checklist.md` 命中 ≥ 1 行。

### 2.2 Manual smoke / integration verification

- 跑 `python3 -m harness_workflow.cli validate --contract artifact-placement` → 期望 exit 0 + stdout `PASS: artifact-placement lint — artifacts/ 下无机器型文件`；
- 模拟反例：手工 `mkdir -p artifacts/main/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/executing && touch artifacts/.../executing/session-memory.md`，再跑同命令 → 期望 exit 1 + 报告 stage-name 子目录 + session-memory.md 双违规；测试完后清理；
- 跑 `python3 -m harness_workflow.cli next`（在 analyst stage 跑前主动构造一个机器型违规文件）→ 期望 lint 失败阻塞流转，stdout 含 ABORT 提示；
- 跑 `pytest -q` → 全绿（含本 chg 新增 TC-01 ~ TC-08）。

### 2.3 AC Mapping

- **AC-1（4 文件物理回归）**：Step 1 + 2.1 静态文件存在断言（前 7 条）。
- **AC-2（lint exit 0）**：Step 4 + Step 5 + 2.1 lint 跑无违规 + 2.2 手动 smoke 第 1 条。
- **AC-3（lint 真敏感）**：Step 4 + Step 9（构造违规 TC-03/TC-05）+ 2.2 手动 smoke 第 2 条。
- **AC-4（白名单不误伤）**：Step 4 白名单豁免 + Step 9（TC-04 白名单测试）+ 2.1 `requirement.md` 保留断言。
- **AC-5（stage 退出门禁接入）**：Step 2 + Step 3 + Step 5 + 2.1 角色文件 grep 断言 + 2.2 手动 smoke 第 3 条。
- **AC-6（scaffold_v2 mirror 一致）**：Step 7 + 2.1 `diff -rq` 双断言。
- **AC-7（sug-35 落地翻转）**：Step 6 + Step 8 + 2.1 sug-35 frontmatter 字段断言 + checklist grep 断言。

## 3. Dependencies & Execution Order

- **硬序约束 1（Step 1 必须最先做）**：Step 1（git mv）必须在 Step 4（lint 升级）之前执行。理由：lint 升级后会立即把 req-46 现场 4 件违规命中阻塞本 chg 自身推进（自我命中导致工作流卡死，change.md §6 风险 2）；先把现状清理干净，再升级 lint。
- **硬序约束 2（Step 4 + Step 5 在 Step 1 之后）**：lint 升级（Step 4）+ 退出门禁接入（Step 5）必须在 Step 1 后；建议顺序为 `Step 1 → Step 4 → Step 5`。
- **硬序约束 3（Step 7 mirror 与 Step 2/3/5/6 同 commit）**：scaffold_v2 mirror 同步必须与对应 live 文件改动落同一次 commit（硬门禁五）；不允许分两 commit 提交。
- **硬序约束 4（Step 8 sug-35 翻转最后做）**：Step 8 必须在 acceptance PASS 后做；防止 chg 失败时 sug 状态错位失去追溯链。
- **Step 9 测试用例编写时机**：建议与 Step 4 / Step 5 同时进行（TDD 风格），先写测试再实现 lint 升级；最迟在 Step 7 commit 前跑通。
- **后续 chg 依赖**：本 chg acceptance PASS 后，方可启动 chg-02（按 roadmap 首批之 1）/ chg-03（首批之 2）/ chg-NN（首批之 3）等 req-46 主线 chg。
- **跨 repo 推广**：不在本 chg 内（change.md §4 Excluded）。

## 4. Test Case Design

> regression_scope: full
> 理由：lint 规则升级 + 工作流退出门禁改动，影响面覆盖全仓库 artifacts/ 扫描行为 + analyst/harness-manager/stage-role 三角色 + harness next CLI 流转 gate；非局部改动，须 full 回归。
>
> Affected interfaces (auto-generated from git diff --name-only + human supplement):
> - `src/harness_workflow/validate_contract.py`（lint 函数升级）
> - `src/harness_workflow/cli.py` / `workflow_helpers.py`（harness next 退出 gate 接入；具体文件 executing 时定位）
> - `.workflow/context/roles/harness-manager.md`（briefing 协议）
> - `.workflow/context/roles/analyst.md`（硬门禁 + 退出条件）
> - `.workflow/context/roles/stage-role.md`（契约 2/3 SOP 检查点）
> - `.workflow/context/checklists/review-checklist.md`（反向抽样条目）
> - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/{harness-manager,analyst,stage-role}.md`（mirror）
> - `src/harness_workflow/assets/scaffold_v2/.workflow/context/checklists/review-checklist.md`（mirror）
> - `.workflow/flow/suggestions/sug-35-*.md` / `.workflow/flow/archive/suggestions/sug-35-*.md`（状态翻转）
> - `tests/test_validate_contract_artifact_placement.py`（新增）

| Test Case | Input | Expected | AC Reference | Priority |
|-----------|-------|----------|--------------|----------|
| TC-01 | Step 1 后 4 文件落位 + 2 空目录清理 + `requirement.md` 保留 | 全部 7 个静态断言通过；`git status` 显示 4 renames + 2 dir 删除 | AC-1 | P0 |
| TC-02 | 干净仓库（无任何违规）跑 `validate --contract artifact-placement` | exit 0 + stdout `PASS: artifact-placement lint` | AC-2 | P0 |
| TC-03 | 构造反例：`mkdir -p artifacts/main/requirements/req-test-x/executing && touch artifacts/.../executing/session-memory.md` 后跑 lint | exit 1 + stdout 报 stage-name 子目录违规 + 报机器型文件违规 | AC-3 | P0 |
| TC-04 | `artifacts/main/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/requirement.md`（白名单 raw 副本）单独存在跑 lint | exit 0；该文件不被命中 FAIL（白名单豁免生效） | AC-4 | P0 |
| TC-05 | 在 analyst stage 故意构造一个机器型违规文件后跑 `harness next` 触发流转 | `harness next` 报 ABORT，stage 不流转，stdout 提示 lint 失败 | AC-5 | P0 |
| TC-06 | `diff -rq .workflow/context/roles/ src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/` + `diff -rq .workflow/context/checklists/ src/harness_workflow/assets/scaffold_v2/.workflow/context/checklists/` | 两条命令均 exit 0 无 stdout 输出（无差异） | AC-6 | P0 |
| TC-07 | sug-35 frontmatter 翻转后 grep `status: archived` + `applied_by_chg: chg-01` | 各命中 1 行；文件位于 `.workflow/flow/archive/suggestions/sug-35-*.md` | AC-7 | P0 |
| TC-08 | dogfood：本 chg 自身整个生命周期（executing → testing → acceptance）产生的工件分布 | 0 件机器型工件落 `artifacts/main/requirements/req-46-建议池梳理验证-优先级-roadmap-分批落地/{stage-name}/`；全部正确落 `.workflow/flow/requirements/req-46-.../changes/chg-01-机器型工件路径修复-防再犯-lint/` | AC-1 + AC-2 + AC-5（综合） | P1 |
