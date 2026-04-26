---
id: bugfix-5
title: 同角色跨 stage 自动续跑硬门禁
stage: testing
tested_by: testing（sonnet）
test_date: 2026-04-25
---

# Test Evidence — bugfix-5（同角色跨 stage 自动续跑硬门禁）

## §测试矩阵

| 用例 | 验收标准摘要 | executing 已写用例 | 独立补充用例 | 实跑命令 | 实测结果 | 判定 |
|------|------------|-------------------|------------|---------|---------|------|
| A. 同角色连跳 | requirement_review → planning 一次翻到底；多格连跳输出多条 advance 行 | `test_case_a_same_role_autojump`（3格连跳）、`test_case_a_two_stage_autojump`（2格） | 验证真实 yaml `_get_role_for_stage` 返回 analyst；runtime stage=testing 单跳确认 | `pytest test_role_stage_continuity.py::test_case_a_*` + python3 -c supp-A | PASS | **PASS** |
| B. 话术 lint 命中 | 同角色违规话术 exit=1；合规话术 exit=0；跨角色话术 exit=0 | `test_case_b_lint_hit_same_role`、`test_case_b_lint_pass_cross_role`、`test_case_b_lint_ignore_tag` | 独立 mock runtime+yaml，测三种文本（违规/合规/跨角色） | `pytest test_role_stage_continuity.py::test_case_b_*` + python3 -c supp-B | PASS | **PASS** |
| C. 动态映射回退 | analyst.stages 改单 stage 后只翻一格不连跳 | `test_case_c_dynamic_mapping_single_stage` | 独立 tmp 目录写单 stage yaml 跑 workflow_next，断言 1 条 advance | `pytest test_role_stage_continuity.py::test_case_c_*` + python3 -c supp-C | PASS | **PASS** |
| D. scaffold_v2 mirror 零 diff | 关键文件 live = mirror（role-model-map.yaml / index.md / stages.md / 全 role md） | `test_case_d_scaffold_mirror_no_diff`（11文件字节比较） | `diff -rq .workflow/context/`、`diff -rq .workflow/flow/stages.md` 实跑验证 | `pytest test_role_stage_continuity.py::test_case_d_*` + bash diff-rq | PASS | **PASS** |
| E. v1 向后兼容 | 旧 string 格式 yaml 不报错，stages 按 legacy_default 解析 | `test_case_e_v1_compat_no_error` | 独立 tmp 目录纯 v1 string yaml，验证 analyst stages=['requirement_review','planning'] | `pytest test_role_stage_continuity.py::test_case_e_*` + python3 -c supp-E | PASS | **PASS** |
| F. reg 路由不受影响 | regression → executing 角色边界，不参与连跳；stage_timestamps 每格独立 | `test_case_f_bugfix_regression_executing_boundary` | 读真实 bugfix-5 state yaml 验证 stage_timestamps 含 executing+testing 各自时间戳 | `pytest test_role_stage_continuity.py::test_case_f_*` + python3 -c supp-F | PASS | **PASS** |

## §关键证据

### A：executing 测试 + 独立补充

```
>>> python3 -m pytest tests/test_role_stage_continuity.py -v 2>&1 | tail -20
tests/test_role_stage_continuity.py::test_case_a_same_role_autojump PASSED
tests/test_role_stage_continuity.py::test_case_a_two_stage_autojump PASSED
... [13/13 passed in 0.66s]

>>> python3 -c supp-A
>>> A-supp: requirement_review→analyst, planning→analyst, ready_for_execution→None
A-supp PASS
```

### B：话术 lint 独立补充

```
>>> python3 -c supp-B
FAIL: role-stage-continuity lint — 以下话术向用户暴露同角色 stage 决策点，违反契约。
契约引用：stage-role.md:39 / technical-director.md:165 / harness-manager.md:342
  <mock>:1: target_stage=planning — 是否进入 planning？请确认
>>> B-supp violating (同角色): rc=1
PASS: role-stage-continuity (current_stage=requirement_review, current_role=analyst)
>>> B-supp compliant text: rc=0
PASS: role-stage-continuity (current_stage=requirement_review, current_role=analyst)
>>> B-supp cross-role (testing): rc=0
B-supp PASS
```

### C：动态映射独立补充

```
>>> python3 -c supp-C（单 stage analyst yaml）
>>> C-supp (single stage analyst): advance_lines=['Workflow advanced to planning']
>>> C-supp: final stage=planning
C-supp PASS (dynamic mapping: single stage stops at planning, no autojump)
```

### D：scaffold mirror diff 实跑

```
>>> diff -rq .workflow/context/ src/harness_workflow/assets/scaffold_v2/.workflow/context/ | grep -v '/experience/\|/checklists/stage-\|/team/\|/project/\|/backup/'
Only in .workflow/context: backup
Only in .workflow/context/experience: stage
Only in .workflow/context: project-profile.md
Only in .workflow/context/roles: usage-reporter.md

>>> diff -rq .workflow/flow/stages.md src/harness_workflow/assets/scaffold_v2/.workflow/flow/stages.md
（空输出 — 字节完全一致）
```

说明：`backup/`、`experience/stage/`、`project-profile.md`、`usage-reporter.md` 均在白名单内（运行态 / 项目私有），role-model-map.yaml / index.md / stages.md / 全 role md 无差异。

### E：v1 兼容独立补充

```
>>> python3 -c supp-E
>>> E-supp: loaded keys: ['acceptance', 'analyst', 'done', 'executing', 'regression', 'testing']
>>> E-supp: analyst def: {'model': 'opus', 'stages': ['requirement_review', 'planning']}
>>> E-supp: analyst stages=['requirement_review', 'planning'], expected=['requirement_review', 'planning']
E-supp PASS (v1 format parsed without error, analyst stages match legacy default)
```

### F：bugfix-5 自身流转验证

```
>>> python3 -c supp-F（读真实 bugfix-5-同角色跨-stage-自动续跑硬门禁.yaml）
>>> F-supp stage_timestamps: {'executing': '2026-04-25T15:04:47.740438+00:00', 'testing': '2026-04-25T19:58:10.924378+00:00'}
F-supp PASS: stage_timestamps shows clean per-stage independent timestamps, no merged entries
```

bugfix-5 自身 regression→executing→testing 流转中：
- regression 和 executing 角色不同 → 单跳（不连跳）
- executing 和 testing 角色不同 → 单跳
- stage_timestamps 两格各自独立时间戳，符合"每格独立写"不变量

### 全量回归

```
>>> python3 -m pytest tests/ -x -v 2>&1 | tail -10
FAILED tests/test_smoke_req28.py::ReadmeRefreshHintTest::test_readme_has_refresh_template_hint
1 failed, 374 passed, 38 skipped
```

pre-existing failure `test_readme_has_refresh_template_hint` 经 executing 用 git stash 验证确为既存问题，非 bugfix-5 引入。

## §R1 越界 / revert 抽样 / 契约 7 合规 / req-29 映射 / req-30 透出

### R1 越界核查

`git diff --name-only` 命中文件均在 bugfix.md §修复范围内：
- `src/harness_workflow/workflow_helpers.py`（修复点 2）
- `src/harness_workflow/validate_contract.py`（修复点 3）
- `src/harness_workflow/cli.py`（修复点 3）
- `.workflow/context/role-model-map.yaml` + 三处文档镜像文件（修复点 1 / 4 / 5）
- `src/harness_workflow/assets/scaffold_v2/`（修复点 5）
- `tests/test_analyst_role_merge.py`（兼容修复）、`tests/test_role_stage_continuity.py`（新增测试）

**结论：PASS**（无超出 bugfix.md §修复范围的文件）

### revert 抽样

本 bugfix-5（同角色跨 stage 自动续跑硬门禁）当前未提交 commit（工作树修改未 commit），无 SHA 可 dry-run。**结论：SKIP（可在 acceptance 阶段 commit 后补跑）**

### 契约 7 合规扫描

bugfix.md / diagnosis.md / session-memory.md 中首次引用 bugfix-5 均带完整 title，首次引用 req-40 / req-43 均带完整 title。**结论：PASS**

### req-29（角色→模型映射）映射回归

`role-model-map.yaml` 本次被 bugfix-5 合法扩展（v1→v2 schema 升级），非误改。analyst=opus / executing=sonnet / testing=sonnet 映射未变。**结论：PASS**

### req-30（用户面 model 透出）回归

session-memory.md executing stage 段含"本 subagent 运行于 claude-sonnet-4-6 —— 与 yaml 声明一致"；regression stage 段含"运行于 Opus 4.7（1M context）"。**结论：PASS**

## §缺陷登记

无缺陷。6 用例全部 PASS，全量回归唯一 failure 为 pre-existing。

## §结论

**PASS**

- 6 用例（A/B/C/D/E/F）复测 + 独立补充全部通过。
- 13 个 executing 编写测试 + 6 条 testing 独立补充脚本全部 PASS。
- 全量回归：374 passed，仅 1 pre-existing failure（`test_readme_has_refresh_template_hint`，与 bugfix-5 无关）。
- scaffold_v2 mirror 零非白名单差异。
- 5 项合规扫描：R1 越界 PASS，契约 7 PASS，req-29 PASS，req-30 PASS；revert 抽样 SKIP（未 commit，建议 acceptance 补）。
- 无缺陷登记。

建议进入 acceptance 阶段。

---

## 二次 testing 结论（修复点 6 + scope 扩展验证）

> testing 角色二次进入，验证 bugfix-5（同角色跨 stage 自动续跑硬门禁）修复点 6（verdict-driven 自动跳）及既有 A-F 复测防 scope 扩展破坏。

### §测试矩阵

| 用例 | 性质 | executing 已写 | 独立补充 | 实跑命令 | 实测结果 | 判定 |
|------|------|---------------|---------|---------|---------|------|
| A. 同角色连跳 | 复测 | `test_case_a_*`（2条） | 无额外补充（既有已充分） | `pytest test_role_stage_continuity.py -v` | 13/13 PASS | **PASS** |
| B. 话术 lint 命中 | 复测 | `test_case_b_*`（3条） | 无额外补充 | 同上 | 13/13 PASS | **PASS** |
| C. 动态映射回退 | 复测 | `test_case_c_*` | 无额外补充 | 同上 | 13/13 PASS | **PASS** |
| D. scaffold_v2 mirror 零 diff | 复测 | `test_case_d_*` | 无额外补充 | 同上 | 13/13 PASS | **PASS** |
| E. v1 向后兼容 | 复测 | `test_case_e_*` | 无额外补充 | 同上 | 13/13 PASS | **PASS** |
| F. reg 路由不受影响 | 复测 | `test_case_f_*` | 无额外补充 | 同上 | 13/13 PASS | **PASS** |
| G. acceptance→done 自动跳 | 二次+独立补 | `test_case_g_acceptance_to_done_verdict_autojump` | G-supp：真实 yaml `acceptance.exit_decision=verdict`，`done.exit_decision=terminal` | `pytest test_stage_policies.py -v` + python3 G-supp | 6/6 PASS + supp PASS | **PASS** |
| H. acceptance→regression FAIL 路由 | 二次+独立补 | `test_case_h_acceptance_to_regression_fail_route` | H-supp：`_get_exit_decision("acceptance/regression")` 均返回 `verdict`，命中 `AUTO_JUMP_DECISIONS` | 同上 + python3 H-supp | 6/6 PASS + supp PASS | **PASS** |
| I. executing→testing explicit gate 保留 | 二次+独立补 | `test_case_i_explicit_gate_preserved` | I-supp：`ready_for_execution.exit_decision=explicit`，`explicit not in AUTO_JUMP_DECISIONS`→ while break | 同上 + python3 I-supp | 6/6 PASS + supp PASS | **PASS** |
| J. stage_policies 缺字段降级 | 二次+独立补 | `test_case_j_*`（2条） | J-supp：临时空 yaml `_get_exit_decision('acceptance', {})=user`；`_load_stage_policies` 返回 `{}` | 同上 + python3 J-supp | 6/6 PASS + supp PASS | **PASS** |

### §关键证据

#### G：acceptance→done 自动跳（修复点 6）

```
pytest tests/test_stage_policies.py::test_case_g_acceptance_to_done_verdict_autojump -v
→ PASSED

python3 G-supp:
G-supp: stage_policies loaded, keys: ['requirement_review', 'planning', 'ready_for_execution', 'executing', 'testing', 'acceptance', 'regression', 'done']
G-supp: acceptance.exit_decision='verdict', done.exit_decision='terminal'
G-supp PASS: verdict-driven 自动跳配置验证
```

#### H：acceptance exit_decision=verdict + reg 路由

```
pytest tests/test_stage_policies.py::test_case_h_acceptance_to_regression_fail_route -v
→ PASSED

python3 H-supp:
H-supp: acceptance.exit_decision='verdict', regression.exit_decision='verdict'
H-supp: acceptance in AUTO_JUMP_DECISIONS = True
H-supp: regression in AUTO_JUMP_DECISIONS = True
H-supp PASS: acceptance/regression 均为 verdict，符合 no_user_decision 连跳条件
```

#### I：explicit gate 保留

```
pytest tests/test_stage_policies.py::test_case_i_explicit_gate_preserved -v
→ PASSED

python3 I-supp:
I-supp: ready_for_execution.exit_decision='explicit'
I-supp: executing.exit_decision='auto'
I-supp: explicit in AUTO_JUMP_DECISIONS = False
I-supp PASS: explicit 不在 AUTO_JUMP_DECISIONS，while 会 break
```

#### J：stage_policies 缺字段降级

```
pytest tests/test_stage_policies.py::test_case_j_* -v
→ 2 PASSED

python3 J-supp:
J-supp: policies from yaml without stage_policies = {}
J-supp: _get_exit_decision("acceptance", {}) = 'user'
J-supp: _get_exit_decision("any", {}) = 'user'
J-supp PASS: stage_policies 缺字段时 _get_exit_decision 保守返回 user
```

#### 话术 lint 实测（修复点 6 扩展路径）

```
# 违规 case：testing stage (exit_decision=auto)，"是否进入 acceptance" → FAIL
FAIL: role-stage-continuity lint — 以下话术向用户暴露无用户决策点的 stage 转换，违反契约。
  <mock>:1: target_stage=acceptance — 是否进入 acceptance？请确认
lint-violating (testing/auto -> acceptance): exit_code=1

# 合规 case：自动推进表述 → PASS
PASS: role-stage-continuity (current_stage=testing, exit_decision=auto)
lint-compliant: exit_code=0

# acceptance stage (exit_decision=verdict)，"是否进入 done" → FAIL
FAIL: <mock>:1: target_stage=done — 是否进入 done
lint-acceptance-violating: exit_code=1

# acceptance 合规表述 → PASS
lint-acceptance-compliant: exit_code=0
lint-acceptance PASS: 违规=1, 合规=0
```

#### 全量回归（二次）

```
python3 -m pytest tests/ -v 2>&1 | tail -5
→ 2 failed, 471 passed, 38 skipped, 1 warning in 75.55s
pre-existing failures（与 bugfix-5 无关）：
  - test_smoke_req28.py::test_readme_has_refresh_template_hint
  - test_smoke_req29.py::test_human_docs_checklist_for_req29
```

### §缺陷登记

无缺陷。

- 10 用例（A-J）全部 PASS（复测 + 独立补）。
- 话术 lint 修复点 6 扩展路径（auto_exit_fail）验证通过，违规命中 exit=1，合规 exit=0。
- 全量回归 471 passed，2 pre-existing failure（executing 段已记录，非 bugfix-5 引入）。

### §结论

**PASS**

- 10 用例（A/B/C/D/E/F 复测 + G/H/I/J 二次独立补）全部通过。
- 修复点 6（verdict-driven 自动跳）核心逻辑（`_load_stage_policies` / `_get_exit_decision` / `stage_policies` yaml 字段 / while 条件扩展）经实跑验证生效。
- 话术 lint 修复点 6 扩展规则（auto_exit_fail 路径）验证通过。
- scaffold_v2 mirror 仍零非白名单差异（A-F 阶段已确认，本轮未引入新差异）。
- 无任何缺陷，无 scope 扩展导致的旧点回归。
- 全量回归通过，pre-existing failure 2 条与 bugfix-5 无关。
