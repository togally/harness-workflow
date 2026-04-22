# Session Memory

## 1. Current Goal

- req-28 / chg-01：修复 `harness suggest` 的 filename fallback 与 `create_suggestion` 跨 archive 编号单调递增，落硬门禁"新 sug 必含 YAML frontmatter"。

## 2. Current Status

- ✅ Step 1：定位 `apply_suggestion` / `delete_suggestion` / `archive_suggestion` / `_next_suggestion_id`。
- ✅ Step 2：三函数加 frontmatter+filename 统一 fallback 匹配。
- ✅ Step 3：`_next_suggestion_id` 重写为跨 `suggestions/` 与 `archive/` 扫描 `sug-NN` 最大值 +1。
- ✅ Step 4：`done.md` / `stage-role.md` 追加 sug frontmatter 硬门禁 SOP（未落代码 raise 校验，按 briefing 的双轨文档风格）。
- ✅ Step 5：scaffold_v2 镜像同步，两份 diff = 0。
- ✅ Step 6：`tests/test_suggest_cli.py` 3 条用例全绿；存量 86 测试回归通过（36 skipped）。
- ✅ 对人文档 `实施说明.md` 已产出。

## 3. Validated Approaches

- `python3 -m unittest tests.test_suggest_cli -v` → 3/3 ok。
- `diff` 两对 done.md / stage-role.md 与 scaffold_v2 镜像 → 空。
- `python3 -m unittest tests.test_archive_path tests.test_cli tests.test_next_writeback tests.test_cycle_detection tests.test_rename_helpers tests.test_regression_helpers tests.test_req26_independent tests.test_smoke_req26` → Ran 86 tests OK (skipped=36)。

## 4. Failed Paths

- 无。

## 5. Candidate Lessons

```markdown
### 2026-04-19 sug CLI filename fallback
- Symptom: 无 frontmatter 的 sug 永远 `Suggestion not found`，清空目录后编号与 archive 冲突。
- Cause: 仅按 frontmatter.id 匹配；`_next_suggestion_id` 只扫当前目录。
- Fix: 统一 frontmatter.id / path.stem / `sug-NN-` 前缀三分支匹配；编号计算跨 archive 扫描。
```

## 6. Next Steps

- 交接给 chg-02：slug/filename 匹配工具可复用（三分支模式）；sug frontmatter SOP 已上线，后续 chg 新写 sug 时请遵循 `id/title/status/created_at/priority`。
- 不跑 `harness next`。

## 7. Open Questions

- 无。
