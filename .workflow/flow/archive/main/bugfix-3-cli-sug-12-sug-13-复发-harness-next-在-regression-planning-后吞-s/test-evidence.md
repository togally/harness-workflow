# Test Evidence — bugfix-3

## 1. 自动化测试（pytest）

### 1.1 新增防回归套件 `tests/test_state_sync_invariants.py`

8 / 8 全绿（修复前 6 红 2 绿，修复后全绿）：

```
tests/test_state_sync_invariants.py::RegressionRouteConsumptionTest::test_next_consumes_regression_route_text_marker PASSED
tests/test_state_sync_invariants.py::RegressionRouteConsumptionTest::test_next_consumes_regression_route_yaml_frontmatter PASSED
tests/test_state_sync_invariants.py::RegressionRouteConsumptionTest::test_next_falls_back_to_sequence_when_no_route PASSED
tests/test_state_sync_invariants.py::OperationTypeSyncTest::test_enter_workflow_resets_operation_type_to_bugfix PASSED
tests/test_state_sync_invariants.py::OperationTypeSyncTest::test_load_runtime_fixes_stale_operation_type PASSED
tests/test_state_sync_invariants.py::OperationTypeSyncTest::test_next_after_enter_syncs_bugfix_yaml_not_requirement PASSED
tests/test_state_sync_invariants.py::ArchiveDefaultTargetTest::test_cli_archive_passes_current_requirement_as_preselect PASSED
tests/test_state_sync_invariants.py::ArchiveDefaultTargetTest::test_prompt_uses_current_requirement_as_preselect PASSED
============================== 8 passed in 0.51s ===============================
```

| 缺陷 | 单测覆盖 | 红 → 绿 |
| --- | --- | --- |
| 1（sug-12 复发：next 吞 stage） | RegressionRouteConsumptionTest 3 条 | 2 红 → 全绿 |
| 2（sug-13 复发：runtime ↔ state yaml 不同步） | OperationTypeSyncTest 3 条 | 3 红 → 全绿 |
| 3（archive 选错目标） | ArchiveDefaultTargetTest 2 条 | 1 红 → 全绿 |

### 1.2 全量回归 `PYTHONPATH=src python3 -m pytest -q`

```
316 passed, 53 skipped in 69.51s (0:01:09)
```

- 修复前基线：308 passed + 53 skipped + 0 failed
- 修复后：316 passed (+8 新增) + 53 skipped + **0 failed**
- 零回归。

## 2. 手工模拟验证

### 模拟 1：reg + decision = planning → next 切到 planning（缺陷 1）

mock 一个 `req-mock` + 在 `regressions/reg-99-test/decision.md` 写 `route_to: planning`，runtime.stage 起始 = acceptance、current_regression = reg-99：

```
BEFORE:
  runtime.stage = acceptance / current_regression = reg-99
  req.stage = acceptance

--- harness next ---
Workflow advanced to planning

AFTER:
  runtime.stage = planning / current_regression = (empty)
  req.stage = planning
```

PASS：
- runtime.stage 从 acceptance 跳到 planning（按 reg.decision 路由覆盖默认 sequence + 1 = done）
- current_regression 被消费清空
- req state yaml 同步写到 planning

### 模拟 2：4 次 next 全程 runtime.stage == bugfix.stage（缺陷 2）

模拟今天用户活证：runtime 残留 operation_type=requirement / operation_target=req-old，enter bugfix-99 → 4 次 next：

```
=== STEP 1: enter bugfix-99 ===
  runtime.operation_type = bugfix       (从残留 requirement 自愈)
  runtime.operation_target = bugfix-99

=== STEP 2: 4 次 harness next ===
  iter 1: runtime.stage=executing    | bugfix.stage=executing    | == EQUAL ==
  iter 2: runtime.stage=testing      | bugfix.stage=testing      | == EQUAL ==
  iter 3: runtime.stage=acceptance   | bugfix.stage=acceptance   | == EQUAL ==
  iter 4: runtime.stage=done         | bugfix.stage=done         | == EQUAL ==
```

PASS：4 次推进全程 EQUAL，bugfix yaml 不再永远停留在 regression。

### 模拟 3：archive 默认目标 = current_requirement（缺陷 3）

mock done 列表含 bugfix-2 + bugfix-3，runtime.current_requirement = bugfix-2，monkey-patch 捕获 prompt 入参：

```
candidates = ['bugfix-2', 'bugfix-3']
preselect  = bugfix-2
expected   = bugfix-2 (current_requirement)
PASS
```

PASS：preselect = bugfix-2（current_requirement），不再盲取列表首个 bugfix-3。

## 3. 修复点位汇总

| 缺陷 | 文件 | 关键改动 |
| --- | --- | --- |
| 1 | `src/harness_workflow/workflow_helpers.py` | 新增 `_parse_decision_route` / `_resolve_regression_route` helper；`workflow_next` 在 sequence 校验前先消费 reg 路由（允许 done → planning 等回退） |
| 1 | `assets/skill/assets/templates/regression-decision.md{.tmpl,.en.tmpl}` | 头部加 yaml frontmatter `route_to: ""` 占位 + 注释说明 |
| 2 | `src/harness_workflow/workflow_helpers.py::enter_workflow` | 切换 id 时显式重设 `operation_type` / `operation_target` |
| 2 | `src/harness_workflow/workflow_helpers.py::load_requirement_runtime` | 残留值与 current_requirement 前缀不一致时强制自愈 |
| 3 | `src/harness_workflow/cli.py` archive 分支 | 从 runtime 读 `current_requirement` 作为 preselect；不在 done 列表时 stderr 提示并 fallback |
| 防回归 | `tests/test_state_sync_invariants.py` | 新建，8 条用例覆盖三组缺陷 |

## 4. 验收建议

- 阻塞 acceptance / done：**不阻塞**。修复方案不引入新外部依赖、不改角色文件、不改工作流模型；测试零回归；3 个缺陷各自手工模拟均通过。
- 后续监控点：建议 done 阶段六层回顾时关注 `decision.md` 是否被诊断师按新 frontmatter 习惯填写；若长期为空，考虑在 `harness regression --confirm` 流程中加一个 prompt 引导填 route_to。
