---
id: bugfix-12
title: "runtime-block.yaml-误判用户野文件-白名单漏配"
created_at: 2026-04-30
operation_type: bugfix
stage: regression
---

## Current Goal
- 独立诊断 + 同型病扫描，判定真伪 + 路由 + fix plan + 完成判据 lint 命令字面清单。

## Current Status
- regression round-1 已完成。诊断结论 = real（非误判 / 非部分真）；路由 = confirm → executing；同型病扫描覆盖 10 类 .workflow/state/ 文件，仅此 1 例漏配；fix plan + 4 条 lint 字面命令已写入 `regression/diagnosis.md`；无 OQ，无阻塞。

## Validated Approaches
- 实证 1：`grep -n "runtime-block" src/harness_workflow/workflow_helpers.py` 命中 4 行，唯一写盘点 = `block_path = root / ".workflow" / "state" / "runtime-block.yaml"` (line 8238)。
- 实证 2：`PYTHONPATH=src python3 -c "from harness_workflow.workflow_helpers import _SCAFFOLD_V2_MIRROR_WHITELIST; print([w for w in _SCAFFOLD_V2_MIRROR_WHITELIST if w in 'state/runtime-block.yaml'])"` → `[]`（21 条白名单零命中）。
- 实证 3：`PYTHONPATH=src python3 -c "from harness_workflow.workflow_helpers import _scaffold_v2_file_contents; ..."` → mirror 仅 4 个 state/ 文件（runtime / action-log / platforms / experience-index），不含 runtime-block.yaml → 第一级豁免 miss。
- 实证 4：`_save_managed_state` 仅记录 mirror 推过的文件 hash，runtime-block.yaml 不走 mirror → managed-files.json 不登记 → 第二级豁免 miss。
- 实证 5：本仓 pyproject.toml `name = "harness-workflow"` → `_is_dev_repo` Layer 1 命中 → 本地 `check_user_write_protected_zones` 直接 return 0，故本仓不复现，问题只出现在用户仓。
- 实证 6：baseline pytest = 51 failed / 729 passed / 40 skipped（regression stage 实测 2026-04-29 16:59 后）。
- 实证 7：`find src/harness_workflow/assets/scaffold_v2 -name workflow_helpers.py` 零命中 → 修白名单不需要 scaffold mirror 同步。

## Failed Paths
- （无 — 主 agent 4 条结论复核全部成立，无任何反证。）

## Candidate Lessons
- 2026-04-30 新增 harness 自家写的运行时态文件时（如 raise_harness_block 写 runtime-block.yaml），必须同步在 `_SCAFFOLD_V2_MIRROR_WHITELIST` 登记一条 — Symptom: user-write-protected-zones 误判为用户野文件 / Cause: 三级豁免（mirror / managed / WHITELIST）全 miss / Fix: WHITELIST 加 substring 兜底（最小修法）。
- 2026-04-30 同型病排查方法论：列出仓库 `.workflow/state/...` 全部 harness 自写文件 → 对照 mirror 实测 + WHITELIST 子串扫描，确保每条至少命中一级豁免，无遗漏。

## Diagnosis Round-1
- 复核结论：主 agent 4 条结论（writer / 三级豁免链 / WHITELIST 漏配 / dev_repo 短路）经 grep + Python 双重实证全部成立。
- 真伪：real（真实问题，非误判 / 非部分真）。
- 同型病扫描：10 类 `.workflow/state/...` 文件对照表，仅 `state/runtime-block.yaml` 1 条漏配；其它 9 类（runtime.yaml / action-log / platforms / experience-index / sessions / requirements / bugfixes / feedback / task-context）均已被三级豁免至少一级覆盖。
- 路由：confirm → executing（实现层修复，纯白名单加 1 条字符串 + 4 条反例测试）。
- 阻塞：无。诊断 + 修法 + lint 字面命令均已落定，无 OQ，可直推 executing。
- default-pick 决策清单：无（regression stage 内未遇争议点，主 agent briefing 已圈定红线 + 修法 + 测试范围）。

## Next Steps / Open Questions
- 主 agent 路由 → executing：subagent 执行 fix plan 4 步（白名单加条目 + 新建 4 条 TC + 4 条 lint 字面自检 + scaffold mirror 反向核查）。
- 无 Unresolved questions。

## Round 1 Executing

**执行时间：2026-04-29**

**改动文件：**
1. `src/harness_workflow/workflow_helpers.py`：`_SCAFFOLD_V2_MIRROR_WHITELIST` 元组在 `"state/runtime.yaml"` 行下一行插入 `"state/runtime-block.yaml"` 白名单条目（行 179）。
2. `tests/test_bugfix_12_runtime_block_whitelist.py`：新建，包含 4 条 TC（TC-01 / TC-02 / TC-03 / TC-04）。

**Lint-1 stdout（期望 1 行命中，行号 ∈ [172, 201]）：**
```
179:    "state/runtime-block.yaml",  # bugfix-12（runtime-block.yaml-误判用户野文件-白名单漏配）：raise_harness_block 写运行时阻塞状态，需豁免
8212:    3. .workflow/state/runtime-block.yaml：结构化状态文件
```
行 179 命中白名单元组范围，行 8212 为注释字符串（不影响判定）。✅

**Lint-2 stdout（期望 4 passed）：**
```
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0 -- /usr/local/opt/python@3.14/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/jiazhiwei/claudeProject/workspace/harness-workflow
configfile: pyproject.toml
collecting ... collected 4 items

tests/test_bugfix_12_runtime_block_whitelist.py::test_tc01_runtime_block_yaml_not_flagged_in_user_repo PASSED [ 25%]
tests/test_bugfix_12_runtime_block_whitelist.py::test_tc02_runtime_block_yaml_whitelisted_while_wild_file_flagged PASSED [ 50%]
tests/test_bugfix_12_runtime_block_whitelist.py::test_tc03_runtime_block_yaml_in_whitelist PASSED [ 75%]
tests/test_bugfix_12_runtime_block_whitelist.py::test_tc04_dev_repo_still_short_circuits PASSED [100%]

============================== 4 passed in 0.18s ===============================
```
✅ 4 passed

**Lint-3 stdout（期望 ≤ 51 failed / ≥ 733 passed）：**
```
FAILED tests/test_validate_test_case_design_completeness.py::test_cli_contract_choices_include_artifact_placement
FAILED tests/test_workflow_next_subprocess.py::test_tc04_subprocess_rfe_execute_advances_to_executing_only
FAILED tests/test_workflow_next_subprocess.py::test_tc07_dogfood_full_chain_four_hops
FAILED tests/test_workflow_next_workdone_gate.py::test_tc05_same_role_jump_not_blocked_by_workdone_gate
51 failed, 733 passed, 40 skipped, 1 warning, 17 subtests passed in 99.33s (0:01:39)
```
✅ 51 failed（= baseline，不增）/ 733 passed（≥ 729 + 4 baseline = 733）

**Lint-4 stdout（期望 rc=0 + PASS）：**
```
check rc=0 (期望 0)
PASS
```
✅ PASS

**结论：4 条 lint 全部通过，无任何 plan 条款无法满足。** ✅

## Done Stage Six-Layer Review（2026-04-29 done / opus）

> bugfix-12 修复面极小（白名单 +1 行 / TC +4），六层精简扫描，每层 1~2 行结论。

- **Context 层**：bugfix-12 同型病已扫 10 类 `.workflow/state/...` 自写文件（regression diagnosis.md §同型病扫描表），仅 `state/runtime-block.yaml` 1 条漏配；mirror / managed / experience 文件无同型病；executing.md 经验十五已沉淀同型病扫描方法论 + dev_repo 反例 TC 兜底。
- **Tools 层**：grep / pytest / Python dogfood 三类工具全程顺畅；scaffold mirror 反向核查（`find scaffold_v2 -name workflow_helpers.py` 零命中）确认 src/ 不入 mirror；无新工具痛点。
- **Flow 层**：regression → executing → testing → acceptance → done 五段顺畅，无跳阶；testing 与 acceptance 时间戳同源（19:30:31，acceptance subagent 同时承载 test-evidence.md 写入），bugfix 流程 testing 精简（已被 req-31 / chg-04 废止"测试结论.md"）符合契约。
- **State 层**：runtime.yaml 当前 stage=done / current_requirement=bugfix-12 一致；usage-log.yaml entries=3（regression / executing / acceptance）= 派发次数 3，State 层校验 PASS；bugfix-12.yaml `stage_timestamps` 完整记录到 done。
- **Evaluation 层**：acceptance verdict=PASS / 0 未达标项；4 lint stdout 字面命令全过；testing 与 acceptance 独立性达标（acceptance 用 dogfood Python 脚本独立 paste rc=0 stdout，未盲信 executing 报告）。
- **Constraints 层**：硬门禁九（subagent 产出独立核查）本周期触发 3 次 — regression 主 agent 4 条结论独立 grep 复核（实证 1~7）+ executing 报"白名单已加" 主 agent 实跑 grep 命中行 179 + acceptance 实跑 dogfood Python 看 rc=0；executing 首次未虚报（独立 paste stdout 全部对得上 lint 期望），bugfix-11 教训发挥作用；范围红线无越界（git diff 不含 PetMallPlatform / req-51）。

**六层结论：全过。verdict 不重审，沿用 acceptance PASS。**
