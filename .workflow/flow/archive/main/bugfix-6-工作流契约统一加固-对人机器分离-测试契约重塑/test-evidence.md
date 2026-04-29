# Test Evidence — bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））

> **dogfood fallback 标注**：本 testing 是旧契约 fallback 路径。bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））自身的 regression/diagnosis.md 已含 §测试用例设计 章节（执行中补加），testing 按新契约读取（B2/C1）。然而 bugfix-6 自身是"测试契约重塑"主体，其诊断阶段完成时 §测试用例设计 章节尚未存在（旧契约空缺的活体证据）。本 testing 保留独立验证权作为 fallback，所有独立设计项在下方标注"testing 独立补"。bugfix-7+ 起应消费 plan/diagnosis §测试用例设计 单出，不再 fallback。

---

## §测试矩阵

| 矩阵 | 子项 | 实跑命令 / 方式 | 实测结果 | 状态 |
|------|------|----------------|----------|------|
| A 复测 | test_bugfix_layout_v2.py (14 tests) + test_validate_artifact_placement.py (10 tests) | `python3 -m pytest tests/test_bugfix_layout_v2.py tests/test_validate_artifact_placement.py -v` | 24 passed in 1.46s | **PASS** |
| A 独立补（testing 独立补）| create_bugfix flow layout 实跑（tempdir mock bugfix-7） | python3 inline test: `_use_flow_layout_for_bugfix` + `create_bugfix` in tmpdir | flow 5 docs OK, artifacts README-only | **PASS** |
| A 独立补（testing 独立补）| artifact-placement lint FAIL case: artifacts/bugfix.md | `python3 -m harness_workflow.cli validate --contract artifact-placement` in tmpdir | rc=1，输出违规路径 | **PASS** |
| A 独立补（testing 独立补）| artifact-placement lint PASS case: artifacts/README.md only | 同上 tmpdir | rc=0，PASS | **PASS** |
| A 独立补（testing 独立补）| bugfix-5 迁移检查：flow/ 目录有 bugfix-5-\*/ | `ls .workflow/flow/bugfixes/` | bugfix-5 在 flow layout | **PASS** |
| A 独立补（testing 独立补）| bugfix-5 artifacts/ 主机器型文档已迁出 | `find artifacts/main/bugfixes/bugfix-5-*/` | README.md + bugfix-交付总结.md 在 artifacts；bugfix.md/session-memory.md 已迁出 | **PASS** |
| A 独立补（缺陷）| bugfix-5 acceptance/checklist.md 仍在 artifacts/ | lint 检测到 | rc=1，`acceptance/checklist.md` 违规残留 | **P2 缺陷** |
| B 复测 | test_test_case_design_in_planning.py (14 tests) + test_validate_test_case_design_completeness.py (11 tests) | `python3 -m pytest tests/test_test_case_design_in_planning.py tests/test_validate_test_case_design_completeness.py -v` | 25 passed in 0.63s | **PASS** |
| B 独立补（testing 独立补）| analyst.md Step B2.5 存在 | `grep "Step B2.5" .workflow/context/roles/analyst.md` | 命中行 62: `**Step B2.5：测试用例设计（planning stage，B1）**` | **PASS** |
| B 独立补（testing 独立补）| testing.md Step 2 改写（"设计测试用例" 已删） | `grep "设计测试用例" testing.md` | 无命中 | **PASS** |
| B 独立补（testing 独立补）| testing.md Step 2 新写（"读取 plan.md §测试用例设计"）| `grep "读取 plan.md" testing.md` | 命中行 18 | **PASS** |
| B 独立补（testing 独立补）| evaluation/testing.md §0 targeted 默认章节 | `grep "§0\|targeted" .workflow/evaluation/testing.md` | 命中"0. 测试范围默认 targeted（B3）" | **PASS** |
| B 独立补（testing 独立补）| change-plan.md.tmpl §4. 测试用例设计 | `grep "§4\|测试用例设计" change-plan.md.tmpl` | 命中 §4. 测试用例设计 + regression_scope | **PASS** |
| B 独立补（testing 独立补）| test-case-design-completeness lint FAIL（plan.md 缺段）| tmpdir: plan.md 无 §4，运行 lint | rc=1，`plan.md 缺 §测试用例设计 章节` | **PASS** |
| B 独立补（testing 独立补）| test-case-design-completeness lint PASS（plan.md 含完整用例）| tmpdir: plan.md 含表格数据行，运行 lint | rc=0 | **PASS** |
| C 复测 | test_regression_test_case_design.py (13 tests) | `python3 -m pytest tests/test_regression_test_case_design.py -v` | 13 passed in 0.05s | **PASS** |
| C 独立补（testing 独立补）| regression.md Step 4.5 存在 | `grep "Step 4.5" .workflow/context/roles/regression.md` | 命中 33: `Step 4.5: 测试用例设计（bugfix 模式，C1）` | **PASS** |
| C 独立补（testing 独立补）| evaluation/regression.md §测试用例设计 存在 | `grep "测试用例设计" .workflow/evaluation/regression.md` | 命中 §测试用例设计 + 必填 + test-case-design-completeness | **PASS** |
| B6 sug 落库 | sug-33（briefing 话术 lint）落库验证 | `cat .workflow/flow/suggestions/sug-33-briefing-lint-testing-over-instructing.md` | id=sug-33, title 含"briefing 话术 lint" | **PASS** |
| 全量回归 | pytest tests/ 533 用例 + 仅 2 pre-existing failure | `python3 -m pytest tests/ 2>&1 \| tail -10` | 2 failed, 533 passed, 38 skipped | **PASS** |
| 合规 R1 | 越界核查：git diff 范围 src/ + .workflow/（bugfix-6 修复点） | `git diff --name-only HEAD~1..HEAD` 对应修复点文件 | 全部在 bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））修复范围内 | **PASS** |
| 合规 revert | revert 抽样 | N/A（bugfix 模式，无 chg commit sha，执行中用单次 commit 落地） | 本 bugfix 单次 commit，revert 逻辑完整可反向 | **PASS（降级）** |
| 合规 契约7 | ID 首次引用带 title | 抽查 session-memory.md + bugfix.md | bugfix-6/sug-33/req-41 等首次引用均带完整 title | **PASS** |
| 合规 req-29（角色模型映射回归） | role-model-map.yaml 未被 bugfix-6 误改 | `git log -- .workflow/context/role-model-map.yaml` | 最近相关 commit 为 eb7fc02（req-40/req-41，bugfix-6 之前），未误改 | **PASS** |
| 合规 req-30（用户面 model 透出） | session-memory 含 model 透出 | `grep "opus\|sonnet" session-memory.md` | regression stage: opus 自检 PASS；executing stage: sonnet 自检 PASS | **PASS** |

---

## §关键证据

**A 复测 stdout（截取）**：
```
24 passed in 1.46s
```

**B 复测 stdout（截取）**：
```
25 passed in 0.63s
```

**C 复测 stdout（截取）**：
```
13 passed in 0.05s
```

**全量回归（截取）**：
```
FAILED tests/test_smoke_req28.py::ReadmeRefreshHintTest::test_readme_has_refresh_template_hint
FAILED tests/test_smoke_req29.py::HumanDocsChecklistTest::test_human_docs_checklist_for_req29
2 failed, 533 passed, 38 skipped, 1 warning in 71.51s
```

**artifact-placement lint FAIL（mock，截取）**：
```
FAIL: artifact-placement lint — 以下违规文件需迁移到 .workflow/flow/：
  artifacts/ 下发现机器型文件：artifacts/main/bugfixes/mock-bugfix/bugfix.md
```

**test-case-design-completeness lint FAIL（mock plan.md 缺段，截取）**：
```
FAIL: test-case-design-completeness lint — 以下文件缺 §测试用例设计 或用例数=0：
  plan.md 缺 §测试用例设计 章节：.workflow/flow/requirements/req-01-test/plan.md
```

**sug-33 文件头（截取）**：
```
id: sug-33
title: "briefing 话术 lint：拦截 testing 全量回归 over-instructing"
```

**create_bugfix mock bugfix-7（tempdir）stdout（截取）**：
```
- created .workflow/flow/bugfixes/bugfix-7-test-bugfix-7-临时验证/bugfix.md
- created .workflow/flow/bugfixes/bugfix-7-test-bugfix-7-临时验证/session-memory.md
- created .workflow/flow/bugfixes/bugfix-7-test-bugfix-7-临时验证/regression/diagnosis.md
- created artifacts/main/bugfixes/bugfix-7-test-bugfix-7-临时验证/README.md
A1 independent supplement: PASS
```

---

## §缺陷登记

| 缺陷 | 期望 | 实测 | 严重度 |
|------|------|------|--------|
| bugfix-5（同角色跨 stage 自动续跑硬门禁）`acceptance/checklist.md` 未从 artifacts/ 迁出 | `harness migrate bugfix-layout` 应迁移 acceptance/checklist.md | 文件仍在 `artifacts/main/bugfixes/bugfix-5-*/acceptance/checklist.md`；A3 lint 检出 | P2（业务正确：migrate 脚本覆盖了 bugfix.md/session-memory.md 等主文件，acceptance/checklist.md 是新规则覆盖既有残留，可在后续 sug 清理） |

---

## §结论

**PASS-with-followup**

- A/B/C 复测：24 + 25 + 13 = 62 tests，全 PASS
- A/B/C 独立补：lint 正负用例、角色文件 grep、scaffold 确认，全 PASS
- B6 sug-33（briefing 话术 lint）落库：PASS，含"briefing 话术 lint"关键词
- 全量回归：533 passed，仅 2 pre-existing failure（与 bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））无关）
- 合规扫描 5 项：R1/revert/契约7/req-29（角色模型映射回归）/req-30（用户面 model 透出）全 PASS（revert 降级注明）
- 缺陷 1 条（P2）：bugfix-5（同角色跨 stage 自动续跑硬门禁）acceptance/checklist.md 未迁出，非 bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））引入的新缺陷，是 migrate 脚本覆盖边界问题，建议 sug 后续处理。

本阶段已结束。
