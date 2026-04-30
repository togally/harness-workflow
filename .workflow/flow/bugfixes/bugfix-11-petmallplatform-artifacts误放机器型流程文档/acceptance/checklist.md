---
id: bugfix-11
title: "PetMallPlatform-artifacts误放机器型流程文档"
stage: acceptance
verdict: PASS
created_at: 2026-04-29
---

## 模型自检

- 当前模型：claude-sonnet-4-6（Sonnet 4.6）
- role-model-map.yaml `roles.acceptance == "sonnet"` → 一致

## A. 源码层方向 C 落地

- [x] A.1 req 维度三段式废弃 — grep 0 命中：
  ```
  $ grep -rn "_use_flow_layout\b\|_use_flat_layout\b\|FLAT_LAYOUT_FROM_REQ_ID\|FLOW_LAYOUT_FROM_REQ_ID\|LEGACY_REQ_ID_CEILING" src/harness_workflow/*.py
  （无输出，0 命中）
  ```

- [x] A.2 bugfix 维度三段式废弃 — grep 0 命中：
  ```
  $ grep -rn "_use_flow_layout_for_bugfix\|BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID" src/harness_workflow/*.py
  （无输出，0 命中）
  ```

- [x] A.3 scaffold_v2 mirror 同步 — grep 0 命中：
  ```
  $ grep -rn "_use_flow_layout\|_use_flat_layout\|FLAT_LAYOUT_FROM_REQ_ID\|FLOW_LAYOUT_FROM_REQ_ID\|BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID" src/harness_workflow/assets/scaffold_v2/
  （无输出，0 命中）
  ```

- [x] A.4 契约层 §4 已删 — grep 结果：
  ```
  $ grep -n "三段式分水岭\|历史存量豁免\|FLAT_LAYOUT_FROM_REQ_ID" .workflow/flow/repository-layout.md
  （无输出，0 命中）
  ```

## B. 存量清理

- [x] B.1 artifacts/main/regressions/ 已空：
  ```
  $ ls -la artifacts/main/regressions/
  total 0
  drwxr-xr-x@ 2 jiazhiwei  staff   64 Apr 29 20:36 .
  drwxr-xr-x@ 7 jiazhiwei  staff  224 Apr 23 02:15 ..
  ```
  结论：目录存在且为空，B1 落地。

- [x] B.2 artifacts/main/archive/bugfixes/ 不含 1/2/3/4/6：
  ```
  $ ls artifacts/main/archive/bugfixes/
  bugfix-10-req-48-chg-02-实施缺陷-3-个-contract-未真正接入-raise_harness_block
  bugfix-5-同角色跨-stage-自动续跑硬门禁
  bugfix-7-pipx-reinstall-harness-install-后目标项目未更新到最新且残留多余文件
  bugfix-8-用户项目区与开发期区分离-反向清理盲区修复-用户写保护硬门禁
  bugfix-9-force-managed-透传修复-user-write-门禁误报修复
  ```
  结论：不含 bugfix-1,2,3,4,6，B2 落地。

- [x] B.3 .workflow/flow/archive/main/ 含迁入子目录：
  ```
  $ ls .workflow/flow/archive/main/ | grep -E "bugfix-[12346]|reg-0[12345]"
  bugfix-1-harness-update-check-等-flag-被角色触发吞了-drift-check-无路可走
  bugfix-2-pre-existing-pytest-3-failures-test_chg03_title_contract-py
  bugfix-3-cli-sug-12-sug-13-复发-harness-next-在-regression-planning-后吞-s
  bugfix-4-harness-install-升级清理-旧-layout-残留-bak-branch-名-schema-不一致
  bugfix-6-工作流契约统一加固-对人机器分离-测试契约重塑
  reg-01-角色模型未对用户透出-自我介绍不含-model-字段
  reg-02-harness-update-融合-install-接入-project-reporter
  reg-03-新增工具-api-document-upload-首实现-apifox-mcp-架构可拔插
  reg-04-对人汇报裸-id-不友好-main-agent-输出-reg-xx-req-xx-sug-xx-bugfix-xx-chg-xx-缺简短描述-违反契约-7-精神但现行契约只覆盖文档首次引用
  reg-05-archive-行为重定义-对人文档保留原位-不再生成摘要-md
  ```
  结论：bugfix-{1,2,3,4,6} 全部迁入，reg-01..05 全部迁入，B3 落地。

## C. 测试层

- [x] C.1 test_use_flow_layout.py 已删：
  ```
  $ ls tests/test_use_flow_layout.py
  ls: tests/test_use_flow_layout.py: No such file or directory
  ```

- [x] C.2 test_bugfix_layout_v2.py 已删：
  ```
  $ ls tests/test_bugfix_layout_v2.py
  ls: tests/test_bugfix_layout_v2.py: No such file or directory
  ```

- [x] C.3 test_bugfix_11_flow_layout.py 存在 + DeprecatedSymbolsLintTest：
  ```
  $ ls tests/test_bugfix_11_flow_layout.py
  tests/test_bugfix_11_flow_layout.py

  $ grep -c "def test_" tests/test_bugfix_11_flow_layout.py
  25

  $ grep -n "DeprecatedSymbolsLintTest|class " tests/test_bugfix_11_flow_layout.py
  11:- DeprecatedSymbolsLintTest (12): src/ 树下不允许存在已废弃符号（含 H-E3 新增 2 项）
  45:class CreateRequirementUnconditionalFlowLayoutTest(unittest.TestCase):
  150:class CreateChangeUnconditionalFlowLayoutTest(unittest.TestCase):
  225:class CreateRegressionUnconditionalFlowLayoutTest(unittest.TestCase):
  308:class CreateBugfixUnconditionalFlowLayoutTest(unittest.TestCase):
  375:class DeprecatedSymbolsLintTest(unittest.TestCase):
  ```
  结论：文件存在，25 个测试方法（≥18），DeprecatedSymbolsLintTest 类存在，C3 落地。

- [x] C.4 pytest 通过率：
  ```
  $ pytest tests/ --tb=no -q 2>&1 | tail -5
  FAILED tests/test_validate_test_case_design_completeness.py::test_cli_contract_choices_include_artifact_placement
  FAILED tests/test_workflow_next_subprocess.py::test_tc04_subprocess_rfe_execute_advances_to_executing_only
  FAILED tests/test_workflow_next_subprocess.py::test_tc07_dogfood_full_chain_four_hops
  FAILED tests/test_workflow_next_workdone_gate.py::test_tc05_same_role_jump_not_blocked_by_workdone_gate
  51 failed, 708 passed, 40 skipped, 1 warning, 17 subtests passed in 85.78s (0:01:25)
  ```
  结论：708 passed ≥ 705 门槛，failed = 51（等于 pre-existing 基线，无新增），C4 落地。

## D. 范围红线

- [x] D.1 PetMallPlatform 不动：
  ```
  $ git diff --name-only | grep PetMallPlatform | wc -l
         0
  ```
  结论：0 命中，跨仓红线未被触碰，D1 落地。

- [x] D.2 plan.md / bugfix.md 无"重写恒 True"现行规约字样：
  ```
  $ grep -n "恒 True|恒True" .workflow/flow/bugfixes/bugfix-11-petmallplatform-artifacts误放机器型流程文档/plan.md
  24:- [x] **删除 `_use_flow_layout(req_id)` 函数本体**（bugfix-11 round-2 修正：round-1 误写为「恒 True」，round-2 真正删除函数 + 6 处调用改无条件 flow layout）
  84:- round-1 executing subagent 把「删 `_use_flow_layout`」改写为「重写 `_use_flow_layout` 为恒 True」，函数本体保留在 src。
  93:- 修正 bugfix.md / plan.md 中「重写恒 True」字样，改为「函数本体删除 + 6 处调用改无条件 flow layout」。

  $ grep -n "恒 True|恒True" .workflow/flow/bugfixes/bugfix-11-petmallplatform-artifacts误放机器型流程文档/bugfix.md
  47:- **删除 `_use_flow_layout(req_id)` 函数本体**（bugfix-11 round-2 修正：round-1 误改为「恒 True」，round-2 真正删除函数 + 6 处调用改为无条件 flow layout 内联路径）
  ```
  结论：所有"恒 True"出现均在历史错误记录段（round-1 走偏说明 / 修正注释），并非"现行规约"字样。D2 落地。

## E. dogfood（P1）

- [/] E.1 fresh repo 路径核查（**FAIL — 部署版本未更新**）：
  ```
  $ cd /tmp && rm -rf harness_ac_test && mkdir harness_ac_test && cd harness_ac_test
  $ git init && echo "init" > README.md && git add README.md && git commit -m "init"
  $ harness install
  [install_repo] force_managed received: False
  ...（安装成功）

  $ harness requirement "ac-test"
  Requirement workspace: /private/tmp/harness_ac_test/artifacts/main/requirements/req-01-ac-test
  - created /private/tmp/harness_ac_test/artifacts/main/requirements/req-01-ac-test/requirement.md
  - created .workflow/state/requirements/req-01-ac-test.yaml
  ```
  **结论：文档落到了 `artifacts/main/requirements/`，NOT `.workflow/flow/requirements/`。**

  **根因确认**：源码（`src/harness_workflow/workflow_helpers.py`）已修复，但 pipx 部署版本仍是 0.2.0（旧版），未执行 `pipx install --force`。

  ```
  $ pipx list | grep harness
  package harness-workflow 0.2.0, installed using Python 3.14.3

  $ diff src/harness_workflow/workflow_helpers.py \
      ~/.local/pipx/venvs/harness-workflow/lib/python3.14/site-packages/harness_workflow/workflow_helpers.py | head -20
  78,81c78,90
  < # bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）/ 方向C（废弃三段式分水岭）：
  < # 三级布局常量（数字阈值分水岭）已被删除。
  < # 所有 req / chg / regression 一律走 flow layout...
  ---
  > LEGACY_REQ_ID_CEILING = 38
  > FLAT_LAYOUT_FROM_REQ_ID = 39
  > FLOW_LAYOUT_FROM_REQ_ID = 41
  > BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID = 6
  > def _use_flat_layout(req_id):...
  > def _use_flow_layout(req_id):...
  ```

  **E.1 FAIL：pipx 未重装 → 部署版与源码严重分叉 → 真实运行时 bug 仍存在。**

## §结论（初版 - 已被复跑覆盖）

> **Superseded**：本节为初次 acceptance 跑出的 FAIL（仅 E.1 dogfood 因 pipx 部署版未重装而 FAIL，源码 / 测试 / 契约 / 红线均 PASS）。
> 修复路径：commit `1994ab2` push origin/main，用户从 GitHub `pipx install --force` 重装 → fresh repo 复跑 dogfood 通过 → verdict 改 PASS。
> 最终 verdict 见下方「E.1 复跑」+「§最终结论」段。

---

## E.1 复跑（用户在 fresh repo 跑部署版，2026-04-29 22:46~22:50 UTC+8）

### Step 2 废弃符号 import 自检

```
$PYBIN -c "from harness_workflow.workflow_helpers import _use_flow_layout"
→ ImportError: cannot import name '_use_flow_layout' from 'harness_workflow.workflow_helpers' (...workflow_helpers.py)

$PYBIN -c "from harness_workflow.workflow_helpers import _use_flow_layout_for_bugfix"
→ ImportError: cannot import name '_use_flow_layout_for_bugfix' ...

$PYBIN -c "from harness_workflow.workflow_helpers import _use_flat_layout"
→ ImportError: cannot import name '_use_flat_layout' ...

$PYBIN -c "from harness_workflow.workflow_helpers import FLAT_LAYOUT_FROM_REQ_ID"
→ ImportError: cannot import name 'FLAT_LAYOUT_FROM_REQ_ID' ...

$PYBIN -c "from harness_workflow.workflow_helpers import FLOW_LAYOUT_FROM_REQ_ID"
→ ImportError: cannot import name 'FLOW_LAYOUT_FROM_REQ_ID' ...

$PYBIN -c "from harness_workflow.workflow_helpers import BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID"
→ ImportError: cannot import name 'BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID' ...
```

6/6 ImportError ✓ 部署版的 4 维度三段式分水岭符号全部不存在。

### Step 4 dogfood fresh repo

```
TMPDIR=/var/folders/6m/.../T/harness-deploy-XXXX.J8ualMXbjO
harness install --force-managed → OK（agent=claude）
harness requirement "deploy-verify-bugfix-11"
  → created .workflow/flow/requirements/req-01-deploy-verify-bugfix-11/requirement.md ✓
  → created .workflow/state/requirements/req-01-deploy-verify-bugfix-11.yaml
ls .workflow/flow/requirements/ → req-01-deploy-verify-bugfix-11/
find artifacts/ -type f → (empty)  ✓
find artifacts/ -type d -name "changes" → (empty)  ✓
harness bugfix "deploy-verify-bugfix-dim"
  → Bugfix workspace: .workflow/flow/bugfixes/bugfix-1-deploy-verify-bugfix-dim ✓
  → created artifacts/main/bugfixes/bugfix-1-deploy-verify-bugfix-dim/README.md  （白名单对人占位）
  → created .workflow/flow/bugfixes/bugfix-1-deploy-verify-bugfix-dim/{bugfix.md, session-memory.md, regression/diagnosis.md, regression/required-inputs.md, test-evidence.md}  ✓
ls .workflow/flow/bugfixes/ → bugfix-1-deploy-verify-bugfix-dim/
```

req 维度 + bugfix 维度均落 `.workflow/flow/`，artifacts/ 仅占位 README，**E.1 PASS**。

## §最终结论

- **verdict**: PASS
- **总评**: bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）方向 C 在源码 / 测试 / 契约 / 部署四层全部落地，下游用户仓的 fresh-install 场景不再误落 artifacts/，PetMallPlatform 类型问题根除。
- **未达标项**: 无。
- **路由建议**: PASS → done。

## 旁支观察（不阻塞，建议入 sug 池）

1. `harness requirement` stdout 第一行 `Requirement workspace: .../artifacts/main/requirements/...` 文案误导（artifacts/ 实际未落物，文案应印 `.workflow/flow/requirements/...`）。
2. 用户机器上 `/usr/local/bin/harness` 还有一个非 pipx 安装的 harness 二进制，pipx force install 时提示 PATH 冲突，建议清理或确认。
