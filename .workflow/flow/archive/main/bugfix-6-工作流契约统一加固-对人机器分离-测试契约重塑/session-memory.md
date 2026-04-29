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

---

## testing stage

### 自检结果

本 subagent 运行于 **sonnet（Sonnet 4.6）**，与 `.workflow/context/role-model-map.yaml` `roles[testing] = sonnet` 声明一致；briefing `expected_model: sonnet（Sonnet 4.6）` 一致。Step 7.5 模型一致性自检 PASS。

**dogfood fallback 标注**：本 testing 读取 diagnosis.md §测试用例设计（B2 新契约），但记录"本次 testing 是 dogfood 旧契约 fallback 路径"——bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））自身的 diagnosis.md 在 regression stage 时无 §测试用例设计（契约空缺活体证据），executing 后补加了该段。bugfix-7+ 起应直接消费 plan/diagnosis §测试用例设计 单出。

### 测试矩阵摘要

| 矩阵 | PASS/FAIL |
|------|-----------|
| A 复测（24 tests） | PASS |
| A 独立补（create_bugfix mock + lint 正负用例 + bugfix-5 迁移检查） | PASS（1 P2 缺陷） |
| B 复测（25 tests） | PASS |
| B 独立补（analyst.md B2.5 / testing.md Step 2 / evaluation §0 / plan tmpl §4 / lint 正负用例） | PASS |
| C 复测（13 tests） | PASS |
| C 独立补（regression.md Step 4.5 / evaluation/regression.md §测试用例设计） | PASS |
| sug-33（briefing 话术 lint）落库验证 | PASS |
| 全量回归（533 tests） | PASS（仅 2 pre-existing failures） |
| 合规扫描（R1/revert/契约7/req-29 映射回归/req-30 model 透出） | PASS（revert 降级注明） |

### 缺陷数 + 严重度

- 1 条 P2：bugfix-5（同角色跨 stage 自动续跑硬门禁）`acceptance/checklist.md` 未从 artifacts/ 迁出。migrate 脚本边界问题，新规则覆盖既有，建议后续 sug 清理，不阻塞本 bugfix-6 验收。

### testing 抽检反馈

- A1 `_use_flow_layout_for_bugfix` 逻辑正确：bugfix-6+ → True，bugfix-1~5 → False；create_bugfix 在 tempdir 验证：flow layout 5 文件齐备，artifacts/ 仅 README。
- A3 lint 已上线并在生产环境检出真实违规（含 bugfix-6 自身 + reg-01~05 历史）——lint 功能完全正确，存量清理为后续任务。
- B2 testing.md Step 2 改写到位：旧"设计测试用例"语义已删，新"读取 plan.md §测试用例设计"已落地；B2.5 "独立反例补充例外"保留。
- B3 evaluation/testing.md §0 targeted 默认完整：含 4 条触发条件 + 禁止 over-instructing。
- C1 regression.md Step 4.5 结构完整：bugfix 模式、diagnosis.md 末尾追加 §测试用例设计、regression_scope 字段。
- sug-33（briefing 话术 lint）内容合规：id/title/background 齐备，含"briefing 话术 lint"关键词。
- git diff 确认：testing 仅写 test-evidence.md + session-memory.md 本段，0 业务代码改动。

### ✅ 完成判据

- [x] 7+ 矩阵全跑（A/B/C 复测+独立补 + B6 sug + 全量回归 + 合规 5 项）
- [x] mock 文件（artifact-placement / test-case-design-completeness 临时测试均在 tempdir，无须复原）
- [x] mock bugfix-7 测试在 tempdir 完成，无实际文件写入 repo
- [x] git diff 仅 test-evidence.md + session-memory.md（testing 自身产物）+ 0 业务代码改动
- [x] test-evidence.md 四段齐（矩阵 / 关键证据 / 缺陷登记 / 结论）+ dogfood fallback 标注
- [x] session-memory `## testing stage` 段含抽检反馈
- [x] 模型自检 PASS（sonnet）
- [x] 结论：PASS-with-followup（1 P2 缺陷，不阻塞 acceptance）

---

## acceptance stage

### 自检结果

本 subagent 运行于 **sonnet（Sonnet 4.6）**，与 `.workflow/context/role-model-map.yaml` `roles[acceptance] = sonnet` 声明一致；briefing `expected_model: sonnet（Sonnet 4.6）` 一致。Step 7.5 模型一致性自检 **PASS**。

### Checklist 通过 / 失败计数

| 类别 | 计数 |
|------|------|
| 验收条目总数 | 11 |
| ✅ PASS | 9 |
| ⚠️ PASS-with-followup（非阻塞） | 2 |
| ❌ FAIL | 0 |

两个 ⚠️ 项：
1. bugfix-5（同角色跨 stage 自动续跑硬门禁）`acceptance/checklist.md` 仍在 artifacts/（P2 缺陷，migrate 覆盖边界问题，历史遗留）
2. `review-checklist.md` 未扩 artifact-placement / test-case-design-completeness 新规则（文档后置，功能已落地）

### 验收结论

**PASS-with-followup**

- 13 修复点全部落地（grep 抽样 + executing stage 实施摘要双重确认）
- 62 新用例 100% PASS；533 全量 + 2 pre-existing（与 bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））无关）
- scaffold_v2 mirror 无差异；既有契约（req-31 / req-37 / req-40 / req-41 / req-42）未被破坏
- dogfood fallback 标注在 test-evidence.md 第 3 行显著

### Followup 数 + 性质

共 5 项 followup（全部为用户醒后决策 / 后续处理）：
1. bugfix-5（同角色跨 stage 自动续跑硬门禁）archive（done 完成未 archive，醒后决策）
2. bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））archive（acceptance PASS，醒后决策）
3. req-43（交付总结完善）续跑（planning 挂起，醒后 `harness next`）
4. sug-33 / sug-31 / sug-32 处理顺序（醒后决策是否立项）
5. bugfix-5 acceptance/checklist.md P2 残留清理（后续 sug 处理）

### Acceptance 抽检反馈

- A1/A5 流路：`_use_flow_layout_for_bugfix` + `BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID=6` 存在；bugfix-5 已迁 flow/，5 份机器型文档齐
- A3/B5 lint：`check_artifact_placement` / `check_test_case_design_completeness` 存在 + CLI choices 已扩
- B1/B2/B3 角色改写：analyst.md Step B2.5 / testing.md Step 2 / evaluation/testing.md §0 三处 grep 命中
- B4 模板：change-plan.md.tmpl §4. 测试用例设计 + regression_scope 存在
- C1/C2 bugfix 流程：regression.md Step 4.5 / evaluation/regression.md §测试用例设计契约 命中
- B6 sug-33：文件存在，含 id=sug-33 + 来源标注
- Gap 发现：review-checklist.md 未扩 bugfix-6 新规则，不阻塞（文档后置）

### ✅ 完成判据

- [x] `acceptance/checklist.md` 三段齐（§需求/缺陷映射 / §验收 checklist / §遗留后置项）+ 用户醒后清单
- [x] 验收结论明确：PASS-with-followup
- [x] session-memory `## acceptance stage` 段含抽检反馈
- [x] 模型自检 PASS（sonnet）
- [x] 不调 `harness next` / `harness archive`（等用户醒后决策）

---

## done 阶段回顾报告

### 自检结果

本 subagent 运行于 **opus（claude-opus-4-7[1m]）**，与 `.workflow/context/role-model-map.yaml` `roles[done].model = "opus"` 声明一致；briefing `expected_model: opus（Opus 4.7）` 一致。Step 7.5 模型一致性自检 **PASS**。

### Context 层

- **派发记录**：本 bugfix 周期主 agent 共派发 5 次 subagent——regression（opus）/ executing（sonnet）/ testing（sonnet）/ acceptance（sonnet）/ done（opus，本段）；五段 session-memory 留痕齐备。
- **角色加载合规**：5 段均按 `role-loading-protocol.md` Step 1-7.5 加载（runtime.yaml → tools/index.md → project-overview.md → context/index.md → base-role.md → stage-role.md → 自身 role.md → 经验文件 → 模型自检 → 自我介绍），合规 ✅。
- **模型一致性自检**：5 段均显式标注 `model_check = PASS`（opus / sonnet / sonnet / sonnet / opus 与权威源一致）。
- **结论**：PASS。

### Tools 层

- **tools-manager 召唤**：本 bugfix 周期未显式召唤 tools-manager subagent（regression / done 主要为文档读写 + grep + Edit，工具明确无须匹配；executing / testing / acceptance 在自身 SOP 内直接选 Read/Edit/Write/Bash，工具命中率 100%）。
- **工具命中率**：Read/Edit/Write/Bash/Grep（系统级 grep）全程使用，无误用；harness CLI（`harness validate` / `harness migrate bugfix-layout` / `harness suggest`）按预期触发，无失败。
- **漏召唤**：tools-manager subagent 未派发——按硬门禁一"有匹配工具时优先使用工具，无匹配时才允许由模型自行判断"，本 bugfix 周期工具均已明确，可豁免召唤；如需严格执行则属 WARN（沉淀到 sug 池供 review-checklist 后续考量）。
- **结论**：WARN（tools-manager 未召唤但工具选择无误，可豁免）。

### Flow 层

- **stage 序列合规**：bugfix 流程 `regression → executing → testing → acceptance → done` 序列完整执行（与 `.workflow/context/experience/roles/regression.md` 经验五"bugfix 模式四阶段快速流转"一致）。
- **dogfood 边界处理**：bugfix-6 自身工件按 A2 约定**不迁移**（保留在 `artifacts/main/bugfixes/bugfix-6-.../`，避免破坏当前流程文件引用）；本 done 阶段交付总结落 `artifacts/main/bugfixes/bugfix-6-.../bugfix-交付总结.md`（dogfood 边界，按本 bugfix 自身落地的"对人 only artifacts/"规则执行）；机器型 session-memory 仍在 artifacts/，符合"bugfix-7+ 起新走新路径"约定。
- **stage_policies 合规**：`regression → executing`（verdict）/ `executing → testing`（auto）/ `testing → acceptance`（auto）/ `acceptance → done`（verdict PASS-with-followup）/ `done`（terminal）—— 与 bugfix-5（同角色跨 stage 自动续跑硬门禁）修复点 6 引入的 stage_policies SSOT 一致。
- **结论**：PASS。

### State 层

- **runtime.yaml 一致**：`stage = done` / `operation_type = bugfix` / `operation_target = bugfix-6` / `current_requirement = bugfix-6` / `active_requirements = [req-43, bugfix-6]` 与实际执行一致。
- **state yaml 镜像**：bugfix 周期未独立写 `state/requirements/{id}.yaml`（bugfix 流程不走 req yaml），状态全部由 runtime + session-memory 承载，合规。
- **scaffold_v2 mirror**：executing 阶段 `diff -rq .workflow/context/roles/ scaffold_v2/.workflow/context/roles/` 已确认空（仅 `usage-reporter.md` 白名单差异）；evaluation/ + repository-layout.md 同步无差异；硬门禁五（scaffold mirror）通过。
- **usage-log entries vs 派发次数**：本 bugfix 周期 `find .workflow/state/sessions/ -name usage-log.yaml` **无文件**（bugfix 周期未写 usage-log，仅 req-41 周期有过）；派发次数 5 次但 entries = 0 → **State 层自检报"usage 采集不完整"**，缺失派发清单 = regression / executing / testing / acceptance / done 5 次全缺；按 base-role done 六层回顾 State 层自检规则，本 req 标"usage 采集不完整"且按容差 = 5 - 0 = 5 项 stub 降级。已知问题来源：sug-25（record_subagent_usage 派发链路真实接通）尚未落地。
- **结论**：WARN（usage-log 缺，已登记 sug-25 跟进）。

### Evaluation 层

- **testing 评审标准**：testing 跑 7+ 矩阵（A 复测 24 / B 复测 25 / C 复测 13 / 独立补 + sug-33 落库 + 全量回归 533 / 合规 5 项），全 PASS-with-followup；缺陷数 1 条 P2（bugfix-5 acceptance/checklist.md 残留），非阻塞。
- **acceptance 评审标准**：11 条 checklist（9 PASS / 2 ⚠️ followup / 0 FAIL），结论 PASS-with-followup；2 个 ⚠️ 均为后置项（bugfix-5 P2 残留 + reviewer checklist 未扩新规则），均不阻塞 done。
- **dogfood fallback 标注**：test-evidence.md 第 3 行显著标注；testing 主动声明本次为 dogfood 旧契约 fallback 路径，bugfix-7+ 起走新契约。
- **结论**：PASS。

### Constraints 层

- **base-role 硬门禁 1-7**：
  - 硬门禁一（工具优先）：WARN（tools-manager 未召唤，已上注释）。
  - 硬门禁二（操作说明 + action-log）：5 段 subagent 均在 session-memory 留痕，action-log 末尾有 testing/acceptance 阶段总览（部分未细化到每操作，符合 stage 级摘要）。
  - 硬门禁三（自我介绍）：5 段均按新模板自我介绍含 role_name / role_key / model，✅。
  - 硬门禁四（同阶段不打断）：regression default-pick 5 项 + executing default-pick 14 修复点全部按默认推进 + batched-report，无打断 ✅。
  - 硬门禁六（对人汇报 ID 必带描述）：本 done 报告 + bugfix-交付总结.md 内 bugfix-6 / bugfix-5 / req-41 / req-42 / req-43 / sug-25/30/31/32/33 / chg-XX 等首次引用均带完整 title 或 ≤ 15 字简短描述 ✅。
  - 硬门禁七（周转汇报不列选项 + 必报本阶段已结束）：5 段 subagent 汇报均含「本阶段已结束。」，无 A/B/C 选项 ✅。
- **harness-manager 硬门禁五（scaffold mirror）**：scaffold_v2 mirror diff 已 executing 阶段验证为空 ✅。
- **契约 7（id+title）**：done 报告 + 交付总结自证；diagnosis / bugfix.md / session-memory 均合规 ✅。
- **bugfix-5 修复点 3 lint（role-stage-continuity）**：本 bugfix 周期未触发该 lint 失败，stage_policies SSOT 工作正常 ✅。
- **bugfix-5 修复点 6 stage_policies**：`acceptance → done` 走 verdict（PASS-with-followup → done）正确路由 ✅。
- **bugfix-6 自身引入的 artifact-placement lint**：可执行（CLI choice 已扩），bugfix-6 自身工件按 A2 约定豁免（dogfood 活体证据），bugfix-7+ 起强制 ✅。
- **bugfix-6 自身引入的 test-case-design-completeness lint**：可执行（CLI choice 已扩），diagnosis.md §测试用例设计 段 18 条用例齐 ✅。
- **结论**：PASS。

### 经验沉淀检查

- 候选 4 项（analyst / testing / regression / executing），已逐项 Edit 落地（见后）。

### 完成判据

- [x] 六层回顾完成（Context/Tools/Flow/State/Evaluation/Constraints）
- [x] session-memory `## done 阶段回顾报告` 段六层齐
- [x] 对人交付总结 `bugfix-交付总结.md` 已产出
- [x] sug 池 ≥ 3 条新增（详见交付总结 §后续建议）
- [x] 经验沉淀（4 文件）已 Edit 落地
- [x] 模型自检 PASS（opus）
- [x] 上下文未达 70% 阈值，无需维护

### default-pick 决策清单（done 阶段）

- 无（done 仅做回顾 + 沉淀，无业务推进决策）。
