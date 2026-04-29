---
id: bugfix-10
title: req-48 chg-02 实施缺陷：3 个 contract 未真正接入 raise_harness_block
created_at: 2026-04-29
---

# Problem Description

req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）chg-02（fix-checklist 首批 3 个 + lint 输出加指针）实施后，3 个 contract 函数实际没有接入 `raise_harness_block` helper，导致：

- `check_artifact_placement` 违规时仍用旧 `print("FAIL: ...")` + `return 1`，而非输出 HARNESS_BLOCK 协议 + exit 64
- `check_schema_audit` 和 `check_missing_document` 函数根本不存在（未实现）
- `raise_harness_block` 函数本身也未在 `workflow_helpers.py` 中实现

用户 PetMallPlatform2 实测时，`harness validate --contract artifact-placement` 输出旧格式而非 HARNESS_BLOCK 协议。

# Root Cause Analysis

req-48 chg-02 只写了测试（预期 HARNESS_BLOCK 协议），但实际忘记实现：
1. `raise_harness_block` helper 本身（workflow_helpers.py 无此函数）
2. `check_artifact_placement` 中调用 helper（仍用旧 print + return 1）
3. `check_schema_audit` 函数（未创建）
4. `check_missing_document` 函数（未创建）

即 chg-02 只产出了测试骨架，没有实际代码变更——测试在 stash 状态下一直 FAIL。

# Fix Scope

- `src/harness_workflow/workflow_helpers.py`：新增 `raise_harness_block(error_type, fix_checklist_path, retry_context, severity, detected_by, root)` helper
- `src/harness_workflow/validate_contract.py`：改造 `check_artifact_placement`（加 verbose 参数 + 接入 helper），新增 `check_schema_audit` 和 `check_missing_document`
- `src/harness_workflow/cli.py`：argparse choices 加入 `schema-audit` / `missing-document`
- `tests/test_validate_artifact_placement.py`：`assert rc == 1` → `assert rc in (1, 64)`
- `tests/test_artifact_placement_chg01.py`：同上，FAIL 路径 rc 断言宽松化

不涉及：scaffold_v2 mirror（src/ 不在 scaffold 范围）、任何 .workflow/context/ 内容

# Fix Plan

Step 1：在 workflow_helpers.py 末尾实现 `raise_harness_block`（三层载体：stderr HARNESS_BLOCK + exit code 64/65/0 + runtime-block.yaml）
Step 2：改造 check_artifact_placement（加 verbose 参数；违规时调用 raise_harness_block；PASS 路径保留）
Step 3：新增 check_schema_audit（扫 state/requirements/ 下旧格式目录）
Step 4：新增 check_missing_document（扫 planning 阶段 changes/ 为空）
Step 5：更新 cli.py choices
Step 6：更新受影响测试（rc == 1 → rc in (1, 64)）
Step 7：全量 pytest 验证 0 新增失败

# Validation Criteria

- `test_raise_harness_block.py`：TC-01~04, TC-08~12 全 PASS（12 项中 10 PASS，TC-06/TC-07 预存文档缺失）
- `test_fix_checklist_lint_output.py`：全 17 PASS
- `test_block_protocol_e2e.py`：TC-03/04/05/06/07 全 PASS（8 项中 6 PASS，TC-01/TC-08 预存）
- 本仓 dogfood：`harness validate --contract artifact-placement` exit 0 PASS
- tmpdir 违规 dogfood：exit 64 + HARNESS_BLOCK 协议 + runtime-block.yaml 写入
- 全量 pytest：无新增失败
