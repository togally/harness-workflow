# Session Memory — chg-04（接入主流程 + stderr 日志 + 端到端 CLI 验证：_merge_project_level_files 接入 install_repo / update_repo + 日志输出 + subprocess 真实 CLI 触发 stderr 断言）

## 1. Current Goal

req-52 / chg-04：把项目级合并行为接入主流程；加 stderr 结构化日志；用真实 subprocess CLI 触发做端到端 e2e 验证。

## 2. Context Chain

- Level 0: 主 agent → analysis stage
- Level 1: Subagent-L1 (analyst / opus) → req-52 Phase 1+2+3

## 3. Completed Tasks

- [x] `_merge_project_level_files` docstring 改造方案落 plan.md §1.1（变更点 A）
- [x] `_log_project_level_load(root, scope, hits, fallback_used)` helper 完整代码落 plan.md §1.1（变更点 B）
- [x] `install_repo` 入口段集成代码块（line ~3791 区域插入）落 plan.md §1.1（变更点 C）
- [x] `tests/test_req52_e2e_log.py` 3 用例完整代码落 plan.md §1.2（subprocess 真实 CLI 触发 + stderr 断言，覆盖零文件 / 主路径命中 / legacy fallback 三场景）
- [x] 7 条 lint 命令 + 7 条测试用例写入 plan.md §3 / §4

## 4. Results

- change.md / plan.md / session-memory.md 三件套写入 chg-04 目录
- chg-04 是 req-52 收口 chg；本 chg 落地后 P3 真实闭环（接入主流程 + stderr 日志 + e2e CLI 真实触发验证）

## 5. Default-pick 决策清单

- 日志格式（OQ-C = A） = `[harness] project-level loaded: {N} files from {path}（fallback={legacy_path or "n/a"}）`：理由——与现有 `[install_repo]` / `[update_repo]` stderr 风格一致，grep / pytest substring assert 简单。
- e2e 触发（OQ-D = A） = `harness install --check` + `harness update --check` 双触发：理由——install + update 是 `_merge_project_level_files` 接入主流程的两个主入口；`--check` dry-run 不污染 fixture。
- 通过 `update_repo` 空壳委托（`force_skill=True`）继承日志：减少代码重复，与 req-33 / chg-01 合并 `install_repo` / `update_repo` 主实现的设计延续。

## 6. Next Steps

- 用户拍板 OQ-A ~ OQ-E 后，主 agent harness next 推进到 executing；
- chg-01 → chg-02 → chg-03 → chg-04 顺序执行；chg-04 是收口 chg；
- chg-04 落地后跑全套 lint + e2e + 5 份 req-51 tests 回归确认全绿，进 testing → acceptance → done。

## 7. 待处理捕获问题

- `tests/test_install_repo_sync_contract.py` 是否含 stderr 行数硬断言：执行实施层需检查；如有需同步更新（不在本 chg 防御性扩展面，留给 executing 阶段确认）。
- `_bootstrap_minimal_repo` 用 `shutil.copytree(scaffold_v2, target)` 拷整个 mirror 作为最小骨架；如 scaffold_v2 体积过大导致 e2e 测试耗时 > 30s，可降级为仅拷必要子树（contract / runtime / templates 子集），实施层按耗时调整。

---

## Executing Stage — chg-04 实施结果（Subagent-L1 / executing / Sonnet）

### 实施步骤完成情况

- ✅ Step 1：`_merge_project_level_files` docstring 改造（移除"不接入主流程"，加 chg-04 接入说明）
- ✅ Step 2：`_log_project_level_load(root, scope, hits, fallback_used)` helper 新增到 workflow_helpers.py（line 8364）
- ✅ Step 3：`install_repo()` 入口段集成代码块（line ~3778-3808，三个 scope 各跑一次 _merge + _log）
- ✅ Step 4：`tests/test_req52_e2e_log.py` 新建，3 用例全 PASS

### lint stdout（完整）

**L1：e2e 单测全 PASS**

```
pytest tests/test_req52_e2e_log.py -v
3 passed in 3.51s

test_zero_files_e2e PASSED
test_main_path_hit_e2e PASSED
test_legacy_fallback_e2e PASSED
```

**L2：_log_project_level_load helper 注册确认**

```
grep -n "^def _log_project_level_load" src/harness_workflow/workflow_helpers.py
8364:def _log_project_level_load(

python3 -c "from harness_workflow.workflow_helpers import _log_project_level_load; print('OK')"
OK
```

**L3：docstring "不接入主流程" 已移除**

```
grep "本 helper 不接入 install_repo" src/harness_workflow/workflow_helpers.py
(silent — 0 命中 ✅)
```

**L4：install_repo 集成段存在**

```
grep -n "_proj_scope" src/harness_workflow/workflow_helpers.py
3778: (命中，三 scope 集成块)
3797: (merge 调用)
3801: (merge 调用)
```

**L5：harness validate --contract all**

```
PYTHONPATH=src python3 -m harness_workflow.cli validate --contract all
EXIT:0
```

**L6：req-51 回归（29 项）**

```
pytest tests/test_req51_project_level_loading.py tests/test_req51_project_level_protection.py -v
29 passed ✅
```

**L7：全 suite 回归**

```
pytest tests/ --tb=no -q
52 failed, 744 passed, 40 skipped（baseline 56 failed, 721 passed）
→ 新增 23 passed；失败数净减 4；51 baseline 不增 ✅
req-52 新增 TC（~22）全在 passed 中 ✅
```

✅ chg-04 完成
