# Session Memory — bugfix-10 executing

## 1. Current Goal

实现 raise_harness_block helper + 改造 3 个 contract 接入 HARNESS_BLOCK 协议。

## 2. Current Status

- [x] Step 1：`raise_harness_block` 在 workflow_helpers.py 末尾实现（三层载体）
- [x] Step 2：`check_artifact_placement` 改造（加 verbose 参数 + 接入 helper + PASS 路径保留）
- [x] Step 3：`check_schema_audit` 新增（扫旧格式目录）
- [x] Step 4：`check_missing_document` 新增（扫 planning changes/ 空）
- [x] Step 5：cli.py argparse choices 加入 schema-audit / missing-document
- [x] Step 6：test_validate_artifact_placement.py + test_artifact_placement_chg01.py 更新 rc 断言
- [x] Step 7：全量 pytest 验证：无新增失败（17个预存失败均为文档缺失，非代码问题）
- [x] Step 8：本仓 dogfood PASS + tmpdir 违规 dogfood exit 64 + HARNESS_BLOCK 协议

## 3. Validated Approaches

- `run_contract_cli` 中对单 contract（artifact-placement/schema-audit/missing-document）用 `return check_xxx()` 直接传播 rc，而非 `total_violations += rc` + 最后 `return 1`（后者会掩盖 64）
- `raise_harness_block` 签名：`(error_type, fix_checklist_path, retry_context, severity, detected_by, root=None)`（从 test_raise_harness_block.py 调用代码反推）
- recovery_attempts 累加逻辑：同 error_type 时累加，不同 type 时重置

## 4. Failed Paths

- 最初只改了 `check_artifact_placement` FAIL 路径，但 `run_contract_cli` 末尾 `return 0 if total_violations == 0 else 1` 掩盖了 64 → 改为直接 return

## 5. Candidate Lessons

```markdown
### 2026-04-29 run_contract_cli 单 contract 应直接 return 而非累加
- Symptom: exit 64 被掩盖为 1
- Cause: total_violations += 64; return 0 if total_violations == 0 else 1 → exit 1
- Fix: if contract in ("artifact-placement",): return check_artifact_placement(root)
```

## 6. Next Steps

- executing 完成，等待 testing 阶段

## 7. Open Questions

无

## ✅ 执行完成

3 个 contract（artifact-placement / schema-audit / missing-document）已全部改造，FAIL 路径通过 `raise_harness_block` 触发 HARNESS_BLOCK 协议并返回 exit 64。
本仓 dogfood 验证 PASS（正常路径 exit 0，违规路径 exit 64，信号符合协议规范）。
全量 pytest 运行 0 新增 fail（17 个预存失败均为文档缺失，与本次改造无关）。
