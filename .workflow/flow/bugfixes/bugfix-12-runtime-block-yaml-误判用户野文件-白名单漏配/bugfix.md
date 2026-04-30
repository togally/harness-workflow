---
id: bugfix-12
title: "runtime-block.yaml-误判用户野文件-白名单漏配"
created_at: 2026-04-30
operation_type: bugfix
stage: regression
---

## Problem Description

- Symptom: 非 dev_repo 用户仓（如 PetMallPlatform）触发过 `raise_harness_block`（任意 fix-checklist lint 失败路径都会写 `.workflow/state/runtime-block.yaml`）后，再跑 `harness validate --contract user-write-protected-zones` 或 `harness status --lint`，立即得到 `[user-write-protected-zones] ABORT: 1 violation(s) — 用户野文件命中保护区: - .workflow/state/runtime-block.yaml`，exit 1。
- Impact: 所有非 dev_repo 用户仓 + 历史触发过 HARNESS_BLOCK 的项目（含 PetMallPlatform 在内的下游用户）均阻塞在 user-write-protected-zones 硬门禁上；harness 命令链路（next / status / validate）无法继续；本仓 dev_repo 短路命中故本地不复现，问题面在用户侧。

## Root Cause Analysis

- Root cause: req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）/ chg-01（错误协议契约 + base-role 抛错门禁 + harness-manager 捕获路由）实施时新增 `raise_harness_block` 写 `.workflow/state/runtime-block.yaml`（workflow_helpers.py:8198-8264），但漏改 `_SCAFFOLD_V2_MIRROR_WHITELIST`（workflow_helpers.py:172-201）。该文件三级豁免（mirror / managed / WHITELIST）全 miss：mirror 不含（实证 4 文件白名单零命中）、managed 不登记（不走 mirror 推送路径）、WHITELIST 21 条无任何子串匹配 `state/runtime-block.yaml`。
- Confirmed real issue: yes — 主 agent 4 条结论（写盘者 / 三级豁免链 / WHITELIST 漏配 / dev_repo 短路）经独立 grep + Python 实证全部成立；同型病扫描 9 类对照表确认其它 harness 自写运行时文件均已被覆盖，仅此 1 例漏配。

## Fix Scope

- Affected files / modules:
  - `src/harness_workflow/workflow_helpers.py`：`_SCAFFOLD_V2_MIRROR_WHITELIST` 元组（line 172-201）内 `# 运行时 / 业务态` 段加 1 条 `"state/runtime-block.yaml"`；
  - `tests/test_bugfix_12_runtime_block_whitelist.py`：新建反例测试 4 条 TC（非 dev_repo 不再误报 / 真野文件不被遮蔽 / WHITELIST 条目锁定 / dev_repo 行为不变）。
- Out of scope:
  - PetMallPlatform 任何文件（用户侧 fix 由用户自行升级 harness-workflow 包后自动生效）；
  - req-51（项目级规则-经验-工具支持从制品引入）任何文件；
  - `_is_dev_repo` 三层探测、`check_user_write_protected_zones` 三级豁免主体逻辑、`raise_harness_block` 写盘行为；
  - 新 helper / 新概念 / 新契约（纯白名单加条目修法）。

## Fix Plan

1. 编辑 `src/harness_workflow/workflow_helpers.py` `_SCAFFOLD_V2_MIRROR_WHITELIST` 元组，在 `"state/runtime.yaml"` 行下一行插入：
   ```python
       "state/runtime-block.yaml",      # bugfix-12（runtime-block.yaml-误判用户野文件-白名单漏配）：raise_harness_block 运行时按需创建，跨项目独立，不入 scaffold mirror
   ```
2. 新建 `tests/test_bugfix_12_runtime_block_whitelist.py`，按 `tests/test_user_write_protected_zones.py` 模板写 4 条 TC（详见 `regression/diagnosis.md` §测试用例设计）。
3. 自检 lint 4 条字面命令（详见 diagnosis.md §完成判据 lint 命令清单）：
   - `grep -n "state/runtime-block.yaml" src/harness_workflow/workflow_helpers.py` → 1 行命中，行号 ∈ [172, 201]
   - `pytest tests/test_bugfix_12_runtime_block_whitelist.py -v` → 4 passed
   - `pytest tests/ --tb=no -q | tail -5` → ≤ 51 failed / ≥ 733 passed（baseline = 51 failed / 729 passed / 40 skipped）
   - dogfood Python snippet → `rc= 0` + `PASS`
4. 反向核查 scaffold mirror 不需要同步：`find src/harness_workflow/assets/scaffold_v2 -name workflow_helpers.py` 应零命中。

## Validation Criteria

- [x] `grep -n "state/runtime-block.yaml" src/harness_workflow/workflow_helpers.py` 恰命中 1 行，且行号落在 `_SCAFFOLD_V2_MIRROR_WHITELIST` 元组范围 [172, 201] 内；（实测行 179 ✅）
- [x] `pytest tests/test_bugfix_12_runtime_block_whitelist.py -v` → 4 passed / 0 failed / 0 error；（实测 4 passed in 0.18s ✅）
- [x] `pytest tests/ --tb=no -q | tail -5` → 失败数 ≤ 51（不增加回归），通过数 ≥ 733（含新增 4 条 TC）；（实测 51 failed, 733 passed, 40 skipped ✅）
- [x] dogfood Python 脚本（构造非 dev_repo + 写 runtime-block.yaml + 调 helper）→ `rc = 0` + 输出 `PASS`；（实测 rc=0 PASS ✅）
- [ ] `find src/harness_workflow/assets/scaffold_v2 -name workflow_helpers.py` → 零命中（确认 scaffold mirror 不含 src/，无需同步）；（待 acceptance 终验）
- [ ] PetMallPlatform 用户仓升级 harness-workflow 包后再跑 `harness validate --contract user-write-protected-zones` 不再 ABORT（用户侧验证，可由用户在 acceptance 阶段口头确认或 ff 模式 dogfood 化）。
