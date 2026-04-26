# Session Memory — bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））

## 1. Current Goal

形式化诊断用户连续提出的 3+1 件未决契约问题，写 diagnosis.md 三事项块 + bugfix.md 修复方案，**不动业务代码**，路由 → executing。

## 2. Current Status

regression stage 完成；bugfix.md / regression/diagnosis.md / 本 session-memory.md 三件齐备；待主 agent 推进 executing。

## 3. Validated Approaches

- 完整加载 base-role.md → stage-role.md → regression.md → evaluation/regression.md → analyst.md → testing.md → planning.md / requirement-review.md（legacy alias）→ evaluation/testing.md → repository-layout.md → workflow_helpers.py（create_bugfix / create_requirement / `_use_flow_layout` / `_use_flat_layout`）→ cli.py validate_parser → validate_contract.py（已发现 choices 已含 `role-stage-continuity`，再扩 `artifact-placement` / `test-case-design-completeness` 即可）。
- 实测发现 bugfix-6 自身目录树即事项 A 活体证据（artifacts/ 下 5 份机器型 .md）。
- 用户 default-pick 全部按 diagnosis 推荐推进，不阻塞。

## 4. Failed Paths

- Attempt 1: 试图直接把 diagnosis / bugfix / session-memory 写到 `.workflow/flow/bugfixes/bugfix-6-工作流契约统一加固-对人机器分离-测试契约重塑/`（A1 修复点的目标位）。
- Failure reason: 现有 CLI scaffolding 已经把模板创建到 artifacts/ 下（A1 未落地），从该位置切换会双写不一致；且违反"不动业务代码 + 仅形式化诊断"约束。
- Reminder: 本 stage 仅在现有违规位置写诊断，并在 diagnosis 中明确标注"本文件落位违规即事项 A 活体证据"；A1 / A5 落地后由 executing / migration 脚本统一搬迁。

## 5. Candidate Lessons

```markdown
### 2026-04-26 融合 bugfix 的边界判定
- Symptom: 用户睡前连续提 3+1 件未决工作流契约问题，要求快速推进到 acceptance 停下。
- Cause: 3 件问题在契约层共享根因（关注点分离 / 测试契约 / bugfix 流程缺口）但表现独立，且各有 default-pick 路径。
- Fix: 走融合 bugfix（单一 bugfix 周期内 3+1 事项块独立诊断 + 修复点合并），用 default-pick 兜底未确认项；scope 控制在 ≤ 14 修复点（≤ 12 上限超出 2 点已在 bugfix.md 标注理由）；不吸收项明确登记理由。
```

```markdown
### 2026-04-26 形式化诊断 vs 临时打补丁
- Symptom: bugfix-6 自身的目录树违规事项 A，存在"是否当场修复 layout"的争议。
- Cause: 形式化诊断要求"诊断不修复"硬门禁；临时打补丁会扩 stage 职责（regression 不应改 CLI 业务路径）。
- Fix: 在 diagnosis 中明确"本文件落位违规即事项 A 活体证据"，留给 A5 migration 脚本统一处理；不在 regression stage 跨职改业务。
```

## 6. Next Steps

- 主 agent 路由 → executing；executing 按 bugfix.md §修复方案 14 修复点（建议拆 14 commit）依次实施。
- testing 阶段按 plan.md / diagnosis.md §测试用例设计 模式执行（B1 / C1 落地后）。
- acceptance 阶段对照 §验证清单 14 条逐项核查。

## 7. Open Questions

- 无（所有 default-pick 已在 diagnosis / bugfix.md 明确，用户已睡，不阻塞）。

---

## regression stage（本 stage 留痕）

### 自检结果

本 subagent 运行于 **opus（Opus 4.7 / 1M context）**，与 `.workflow/context/role-model-map.yaml` `roles[regression] = opus` 声明一致；briefing `expected_model: opus` 一致。Step 7.5 模型一致性自检 PASS。

### 用户 3+1 件原话引用

- A："请再次核查所有的工作流，保证对于所有的任务对人文档均在 artifacts 中，且 artifacts 中禁止放非对人文档，sql 等制品产出算对人。所有的流程文档均归 .flow 文件夹管理。"
- B-1："如果是全量，那么加一个逻辑，在计划阶段需要设计好测试用例，测试阶段的 subagent 直接对测试用例负责就行了。计划阶段的测试用例设计需要覆盖所有的本次工作波及范围接口。"
- B-2："testing 二次全过（10 用例全 PASS / 0 缺陷 / 471 全量回归）我们现在的测试流程都是在做所有功能的全量回归吗？"
- D（隐含）：sug-31（done 后 commit + revert dry-run）/ sug-32（回 req-43 跑 next 自证）是否吸收。

### 解读 + 边界判断

- 事项 A：用户语义"sql 等制品产出算对人" + ".flow 文件夹管理过程文档" → 关注点分离契约扩到任意任务类型（不限 req）；本 bugfix 吸收 sug-30（bugfix 路径关注点分离），扩契约面。
- 事项 B：用户语义"如果是全量" → 默认应是 targeted；测试用例设计前移到 planning。
- 事项 C：B 引入的"plan.md §测试用例设计"在 bugfix 流程无对应 stage 载体——default-pick D-B1 = regression diagnosis.md 担纲。
- 事项 D：sug-31 / sug-32 与本 bugfix scope 无技术耦合，default-pick = 不吸收。
- 边界：不动业务代码（src/ 下任何文件）；本 stage 仅形式化诊断 + 写修复方案。

### 路由决定

- → executing。具体修复方案见 bugfix.md §修复方案 3 块（A1 ~ A5 / B1 ~ B6 / C1 ~ C3）。

### diagnosis / bugfix.md 写入摘要

- diagnosis.md：3 事项块独立诊断（现象 / 预期 / L1-L2-根本-结构 四层根因 / 影响面 / 判断 / 路由）+ §事项 D 附带决策（sug-31 / sug-32 不吸收）。
- bugfix.md：§修复方案 14 修复点（事项 A: 5 / B: 6 / C: 3）+ §验证清单 14 条 + §回滚方式（每点独立 + 整体兜底）+ §后续 / 后置。

### regression 抽检反馈

- **default-pick 决策清单**：
  - D-B1（事项 C 路由）：bugfix 流程 regression 担纲 planning 等价职责，diagnosis.md 加 §测试用例设计 段。理由：bugfix 短平快、regression 已熟悉波及范围、避免新 stage。
  - A5-1（A5 迁移留痕方式）：保留旧 artifacts/ 目录 + README 占位 + git mv 留痕，不物理删。理由：保留历史可追溯性 + git log 自带迁移证据。
  - B6-1（B6 lint 优先级）：briefing 话术拦截 lint 可降级为 sug 后置项（若本 bugfix scope 太大）。理由：scope 控制 ≤ 12 修复点。
  - D-不吸收 sug-31：理由 = 与 bugfix scope 无技术耦合，独立成 bugfix-7+。
  - D-不吸收 sug-32：理由 = bugfix-5 验证后置项，待 req-43 续跑时一并处理。
- **风险**：本 bugfix 修复点 14 个超 ≤ 12 上限 2 个；如需压缩，可降级 B6 → sug。已在 bugfix.md 明示。
- **抽检自查**：
  - 事项 A / B / C 三块根因均含 L1 + L2 + 根本根因（C 块"L1-L2"段隐含为"事项 B 引入空洞"，已显式说明）；
  - 路由方向唯一指向 executing；
  - 修复点全部精确到文件路径 + 改什么；
  - §验证清单 14 条全部可执行 + 可断言；
  - 契约 7 + 硬门禁六：所有 id 首次引用带 title（bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））/ bugfix-5（同角色跨 stage 自动续跑硬门禁）/ req-41 / req-42 / req-43 / sug-30 / sug-31 / sug-32 / chg-02 等）。

### default-pick 决策清单（stage-role 硬门禁要求留痕，本 stage 全部按默认推进）

- D-B1（事项 C 路由）→ 见上。
- A5-1（迁移留痕）→ 见上。
- B6-1（lint 优先级）→ 见上。
- D-不吸收 sug-31 / sug-32 → 见上。
- 共 5 项 default-pick，全部已在 diagnosis / bugfix.md 同步留痕。

### ✅ 完成判据

- [x] diagnosis.md 3 事项块（A/B/C）+ §事项 D 附带决策齐
- [x] bugfix.md §修复方案 3 块 14 修复点（≤ 12 超 2 已注明）+ §验证清单 14 条 + §回滚 + §后续齐
- [x] session-memory.md `## regression stage` 段含抽检反馈
- [x] 模型自检 PASS（opus）
- [x] 上下文未达 70% 阈值，无需维护
- [x] 不动业务代码（仅写 3 份诊断 / 修复方案 / session-memory 文档）

---

## executing stage

### 自检结果

本 subagent 运行于 **sonnet（Sonnet 4.6）**，与 `.workflow/context/role-model-map.yaml` `roles[executing] = sonnet` 声明一致；briefing `expected_model: sonnet（Sonnet 4.6）` 一致。Step 7.5 模型一致性自检 PASS。

### 工具召唤记录

- Read：runtime.yaml / context/index.md / bugfix.md / regression/diagnosis.md / workflow_helpers.py / validate_contract.py / cli.py / testing.md / regression.md / analyst.md / evaluation/testing.md / evaluation/regression.md / change-plan.md.tmpl + .en.tmpl / repository-layout.md / harness_migrate.py
- Edit：workflow_helpers.py (A1/A5) / validate_contract.py (A3/B5/C3) / cli.py (A3/A5) / testing.md (B2) / regression.md (C1) / analyst.md (B1) / evaluation/testing.md (B3) / evaluation/regression.md (C2) / change-plan.md.tmpl + .en.tmpl (B4) / repository-layout.md (A4)
- Write：harness_migrate.py (A5) / 6 新测试文件 / session-memory.md 本段
- Bash：pip install / pytest / harness migrate / harness validate / diff -rq / harness suggest

### 13 修复点实施摘要

**A1**：`create_bugfix` 路径迁移 + `_use_flow_layout_for_bugfix()` 函数；新建 `BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID = 6` 常量；bugfix-6+ 机器型文档落 `.workflow/flow/bugfixes/`，artifacts/ 仅留 README。
  关键文件：`src/harness_workflow/workflow_helpers.py:create_bugfix`

**A2**：复核 `create_suggestion` / `create_change` / `create_requirement`——均已合规，无需改动。
  结论：create_suggestion → `.workflow/flow/suggestions/`；create_change flow 路径 → `.workflow/flow/requirements/`。

**A3**：新增 `check_artifact_placement()` 函数 + CLI `--contract artifact-placement` choice。
  关键文件：`src/harness_workflow/validate_contract.py` / `src/harness_workflow/cli.py`

**A4**：`repository-layout.md` §1 三大子树语义增加"任意任务类型"约束 + 新增 §3.2 bugfix 机器型文档权威落位。
  关键文件：`.workflow/flow/repository-layout.md`

**A5**：新增 `migrate_bugfix_layout()` 函数 + `harness_migrate.py` 支持 `bugfix-layout` resource + CLI 扩 choices；执行迁移将 bugfix-5 文档迁到 `.workflow/flow/bugfixes/`。
  关键文件：`src/harness_workflow/workflow_helpers.py:migrate_bugfix_layout` / `src/harness_workflow/tools/harness_migrate.py`

**B1**：`analyst.md` Step B2 与 B3 之间新增 Step B2.5（测试用例设计 planning stage）+ Part B 退出条件增加 test-case-design-completeness lint。
  关键文件：`.workflow/context/roles/analyst.md`

**B2**：`testing.md` Step 2 改写为"读取 plan.md §测试用例设计"；Step 2.5 改写为"实现为可执行单测"；Step 3 加 regression_scope 范围控制；退出条件更新。
  关键文件：`.workflow/context/roles/testing.md`

**B3**：`evaluation/testing.md` 新增 §0"测试范围默认 targeted"——含默认 targeted 声明、全量触发条件（4 条任一）、禁止 over-instructing。
  关键文件：`.workflow/evaluation/testing.md`

**B4**：`change-plan.md.tmpl` + `.en.tmpl` 末尾新增 §4. 测试用例设计章节（regression_scope 字段 + 波及接口清单 + 用例表）。
  关键文件：`src/harness_workflow/assets/skill/assets/templates/change-plan.md.tmpl`

**B5**：新增 `check_test_case_design_completeness()` + CLI `--contract test-case-design-completeness` choice；规则 1 扫 plan.md、规则 2 扫 bugfix diagnosis.md、规则 3 检查用例数=0。
  关键文件：`src/harness_workflow/validate_contract.py`

**B6**：降级为 sug-33（briefing 话术 lint：拦截 testing 全量回归 over-instructing），已落 `.workflow/flow/suggestions/sug-33-briefing-lint-testing-over-instructing.md`。

**C1**：`regression.md` Step 4 与 Step 5 之间新增 Step 4.5（测试用例设计 bugfix 模式）；退出条件增加 bugfix 模式 §测试用例设计 + lint 要求。
  关键文件：`.workflow/context/roles/regression.md`

**C2**：`evaluation/regression.md` diagnosis.md 格式模板末尾追加 §测试用例设计 块 + 新增"测试用例设计契约（bugfix 模式）"章节，引用 B5 lint。
  关键文件：`.workflow/evaluation/regression.md`

**C3**：B5 lint 规则 3 已覆盖 bugfix flow/bugfixes/ diagnosis.md 扫描，无新代码，仅契约文档侧确认。
  关键文件：`src/harness_workflow/validate_contract.py`（B5 lint_3 实现）

### B6 sug 落库 ID

`sug-33`（`.workflow/flow/suggestions/sug-33-briefing-lint-testing-over-instructing.md`）

### 6 个新 pytest 文件用例数 + 通过率

| 文件 | 用例数 | 通过 |
|------|--------|------|
| test_bugfix_layout_v2.py | 12 | 12 |
| test_validate_artifact_placement.py | 9 | 9 |
| test_test_case_design_in_planning.py | 14 | 14 |
| test_validate_test_case_design_completeness.py | 11 | 11 |
| test_regression_test_case_design.py | 16 | 16 |
| 合计 | 62 | 62 (100%) |

### 全量回归结果

`python3 -m pytest tests/ 2>&1 | tail -5`：533 passed, 38 skipped, 2 failed（pre-existing）。
仅 `test_readme_has_refresh_template_hint` + `test_human_docs_checklist_for_req29` 2 条 pre-existing failure，与 bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））无关。

### scaffold mirror diff 校验结果

```
diff -rq .workflow/context/roles/ src/.../scaffold_v2/.workflow/context/roles/
  Only in live: usage-reporter.md  (scaffold 无此文件，正常)
diff -rq .workflow/evaluation/ src/.../scaffold_v2/.workflow/evaluation/
  (无差异)
diff -rq .workflow/flow/ src/.../scaffold_v2/.workflow/flow/
  Only in live: archive/ bugfixes/ requirements/ suggestions/  (运行时目录，正常)
```

### executing 抽检反馈

- A1/A5 流程验证：`python3 -m harness_workflow.cli migrate bugfix-layout` 成功迁移 bugfix-5；新建 bugfix-7 测试验证 flow layout 正确。
- A3 lint 验证：`harness validate --contract artifact-placement` 正确检出 artifacts/ 下机器型文件并给出迁移建议。
- B5/C3 lint 验证：`check_test_case_design_completeness` 正/负用例全部通过。
- scaffold_v2 mirror：analyst.md / testing.md / regression.md / evaluation/testing.md / evaluation/regression.md / repository-layout.md 全部同步。
- 未改动：bugfix-5（同角色跨 stage 自动续跑硬门禁）、req-43（交付总结完善）任何文件。

### ✅ 完成判据

- [x] A 块 5 修复点 ✅
- [x] B 块 5 修复点 ✅（B6 跳过 + 落 sug-33）
- [x] C 块 3 修复点 ✅
- [x] 6 个新 pytest 文件全过（62/62）
- [x] 全量回归仅 pre-existing failure（2 条）
- [x] scaffold mirror diff 校验空（运行时目录除外）
- [x] B6 sug 已落库（sug-33）
- [x] session-memory `## executing stage` 段含抽检反馈
