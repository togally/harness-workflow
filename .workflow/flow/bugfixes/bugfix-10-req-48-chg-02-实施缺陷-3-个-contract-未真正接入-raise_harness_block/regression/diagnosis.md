# Regression Diagnosis

## Issue
req-48 chg-02 实施缺陷：3 个 contract 未真正接入 raise_harness_block

## Root Cause Analysis

chg-02 仅产出了测试文件骨架，但以下 4 个代码实体从未实际实现：

1. `raise_harness_block` helper（workflow_helpers.py 无此函数）— ImportError
2. `check_artifact_placement` 中 raise_harness_block 调用（仍用旧 print + return 1）
3. `check_schema_audit` 函数（不存在，测试 ImportError）
4. `check_missing_document` 函数（不存在，测试 ImportError）

直接证据：`from harness_workflow.workflow_helpers import raise_harness_block` → ImportError

## Routing Direction

- [x] Real issue → proceed to fix（直接在 executing 阶段实现缺失代码）

## 测试用例设计

| TC | 前提 | 操作 | 期望 |
|----|------|------|------|
| TC-01 | workflow_helpers.py 有 raise_harness_block | `raise_harness_block("artifact-placement", ...)` severity=FAIL | rc=64, stderr 含 HARNESS_BLOCK:, runtime-block.yaml 写入 |
| TC-02 | 同上 | severity=ABORT | rc=65 |
| TC-03 | 同上 | severity=WARN | rc=0 |
| TC-04 | 同上 | 连续调用 2 次 | recovery_attempts=2 |
| TC-05 | tmp_path 有 artifacts/ 违规 | check_artifact_placement(tmp_path) | rc=64, stdout 含 FAIL:, stderr 含 HARNESS_BLOCK: |
| TC-06 | tmp_path 有旧格式目录 req-99/ | check_schema_audit(tmp_path) | rc=64, HARNESS_BLOCK: schema-audit |
| TC-07 | planning stage + changes/ 为空 | check_missing_document(tmp_path) | rc=64, HARNESS_BLOCK: missing-document |
| TC-08 | 无违规 | check_artifact_placement(clean_tmp) | rc=0, stdout 含 PASS |
| TC-E2E | subprocess via CLI --contract artifact-placement | 构造违规 + 运行 | exit 64 + HARNESS_BLOCK: + runtime-block.yaml |

## Required Inputs

无需人工输入，ff 模式直接 executing。
