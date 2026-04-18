# Testing Report: req-12 "suggest批量转成需求"

**Date:** 2026-04-15  
**Tester:** Independent Testing Engineer  
**Scope:** `--apply-all` feature for `harness suggest`

---

## Test Plan Summary

1. Verify `--apply-all` is recognized by the CLI parser and documented in help.
2. Verify end-to-end batch conversion: create multiple pending suggestions, run `--apply-all`, confirm requirements are created.
3. Verify suggestion file statuses change from `pending` to `applied` after conversion.
4. Verify command output contains a clear result report with success counts and sug-id → req-id mapping.
5. Verify non-pending (already applied) suggestions are skipped without error.
6. Verify README.md documents the new `--apply-all` option.

---

## Test Results

| ID | Test Case | Steps | Expected Result | Actual Result | Status |
|----|-----------|-------|-----------------|---------------|--------|
| TC-01 | `--apply-all` is a valid CLI argument | Run `harness suggest --help` | `--apply-all` appears in options list with description | `--apply-all` listed as: "Apply all pending suggestions and create requirements." | **PASS** |
| TC-02 | Batch conversion creates requirements | Init temp project, add 3 suggests, run `--apply-all` | 3 requirements created under `.workflow/flow/requirements/` | `req-01-Add dark mode toggle`, `req-02-Refactor auth middleware`, `req-03-Improve error messages` created | **PASS** |
| TC-03 | Suggest status changes to `applied` | Inspect `status:` in all `sug-*.md` files after conversion | All converted suggests show `status: applied` | `sug-01`, `sug-02`, `sug-03` all show `status: applied` | **PASS** |
| TC-04 | Command outputs clear result report | Run `--apply-all` and capture stdout | Output shows success count and mapping from sug-id to req-id | Output: "Applied 3 suggestion(s):" with `- sug-01 → req-01`, etc. | **PASS** |
| TC-05 | Non-pending suggests are skipped | Add a pre-existing `status: applied` suggest (`sug-04`), run `--apply-all` | Skipped count reported, no error, no duplicate req created | Output: "Skipped 1 already-applied suggestion(s)." No `req-04` created. | **PASS** |
| TC-06 | README documents `--apply-all` | Search `README.md` for `apply-all` | README contains command reference and example usage | Found in Core Commands table and Capture Ideas example block. | **PASS** |

---

## Acceptance Criteria Verdict

| # | Criterion | Verdict |
|---|-----------|---------|
| 1 | `harness suggest --apply-all` 命令可用 | **PASS** |
| 2 | 命令能将所有 `status: pending` 的 suggest 批量转为正式需求 | **PASS** |
| 3 | 转化成功的 suggest 状态变为 `applied` | **PASS** |
| 4 | 命令输出清晰的转换结果报告（成功/失败数量及对应 ID） | **PASS** |
| 5 | 文档（README 或命令帮助）已更新 | **PASS** |
| 6 | 批量转换功能验证通过（chg-02） | **PASS** |
| 7 | 包已重新安装（chg-02） | **PASS** (stated in current state) |

---

## Overall Conclusion

All test cases passed. The `--apply-all` feature behaves correctly:
- Parses and executes via CLI.
- Converts all pending suggestions to requirements.
- Updates suggestion statuses to `applied`.
- Produces a readable success report including mappings.
- Gracefully skips already-applied suggestions.
- Is documented in both CLI help and `README.md`.

**Status: COMPLETE**
