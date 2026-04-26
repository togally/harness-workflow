# Session Memory — chg-04（bugfix 引入 bugfix-交付总结.md（done 模板精简版））

## executing stage ✅

### 实现摘要

- `done_efficiency_aggregate` 新增 `task_type="bugfix"` 路径：从 `.workflow/state/sessions/{bugfix_id}/usage-log.yaml` 读 entries（与 chg-01 task_type 配套）。
- `validate_human_docs.py`：`BUGFIX_LEVEL_DOCS` 新增 `("acceptance_done", "bugfix-交付总结.md")`；新增 `_collect_bugfix_items(bugfix_dir)` 函数。
- `done.md` 加 `## bugfix 交付总结模板（精简版）` 段：需求是什么 / 修复了什么 / 修复验证 / 结果是什么 / 后续建议 / 效率与成本（含单表）；删 chg 段，合并 testing+acceptance 为「修复验证」段。
- `repository-layout.md` §2 白名单新增 `bugfix-交付总结.md` 行；§3.2 落位补注。
- scaffold_v2 mirror 同步：done.md + repository-layout.md（diff = 0）。

### 测试结果

- 新增测试文件：`tests/test_req43_chg04.py`（9 条）
- 全部通过：9/9 ✅
- 关键覆盖：bugfix 路径读 sessions、req 向后兼容、BUGFIX_LEVEL_DOCS 含 bugfix-交付总结.md、validate 检出缺失、done.md 模板段、无 chg 段验证、stage_role_rows 包含 regression/executing/acceptance、mirror×2

### 遇到的问题 / 解法

- 无阻塞问题。bugfix done 路径绑在 acceptance 后置 hook，不新增 done stage（D-2 default-pick 落地）。
