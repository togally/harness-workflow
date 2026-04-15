# Testing Report: req-21 "suggest 批量转需求支持打包与自动清理"

**Date:** 2026-04-15  
**Tester:** Developer / Self-test  
**Scope:** `--apply-all` 打包与清理功能

---

## Test Plan Summary

1. Verify `--apply-all` packs multiple pending suggests into a single requirement.
2. Verify `--pack-title` overrides the default packed requirement title.
3. Verify original suggest files are deleted after successful conversion.
4. Verify empty suggest pool produces a clear non-error message.
5. Verify README documents the new `--apply-all` and `--pack-title` usage.

---

## Test Results

| ID | Test Case | Steps | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| TC-01 | Pack multiple suggests into one req | Create 3 suggests, run `harness suggest --apply-all` | Only 1 requirement created containing all suggests | `req-01-批量建议合集（3条）` created, packed sug-01~03 | **PASS** |
| TC-02 | Custom pack title | Create 2 suggests, run `harness suggest --apply-all --pack-title "自定义打包标题测试"` | Requirement title matches custom title | `req-02-自定义打包标题测试` created | **PASS** |
| TC-03 | Delete original suggest files | After TC-01, inspect `.workflow/flow/suggestions/` | Suggest files removed | Directory empty (0 files) | **PASS** |
| TC-04 | Empty suggest pool | Run `harness suggest --apply-all` with no pending suggests | Clear message, exit code 0 | "No pending suggestions found." | **PASS** |
| TC-05 | README documentation | Search README.md for `apply-all` and `pack-title` | Both options documented | Found in table and example block | **PASS** |

---

## Acceptance Criteria Verdict

| # | Criterion | Verdict |
|---|---|---|
| 1 | `--apply-all` 支持将所有 pending suggest 打包为**一个**需求 | **PASS** |
| 2 | 打包后的需求标题可由用户指定（`--pack-title`），若未指定则使用默认标题 | **PASS** |
| 3 | 转化成功后，所有被处理的 suggest 文件从 `.workflow/flow/suggestions/` 中**删除** | **PASS** |
| 4 | 命令输出清晰的转换结果报告（成功删除的 suggest 数量和生成的 req ID） | **PASS** |
| 5 | 当 suggest 池为空或无 pending suggest 时，命令给出明确提示且不报错 | **PASS** |
| 6 | CLI 帮助和 README 文档已更新 | **PASS** |

---

## Overall Conclusion

All test cases passed. The `--apply-all` feature now correctly:
- Bundles multiple pending suggestions into a single requirement.
- Supports custom titles via `--pack-title`.
- Deletes original suggestion files after conversion instead of merely marking them applied.
- Handles empty pools gracefully.
- Is documented in README.

**Status: COMPLETE**
