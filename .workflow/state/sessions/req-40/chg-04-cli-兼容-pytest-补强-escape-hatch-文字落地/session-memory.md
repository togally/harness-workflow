# Session Memory — chg-04（CLI 兼容 pytest 补强 + escape hatch 文字落地）

## 1. Current Goal

- 新建 `tests/test_analyst_role_merge.py`（9 条断言）守住 analyst 角色合并后的静态规约；
- 确认 escape hatch 触发词在 `analyst.md` 与 `technical-director.md §6.2` 均落地；
- 全量 pytest 零回归。

## 2. Current Status

- **DONE**：`tests/test_analyst_role_merge.py` 新建，9 条全部 PASS；
- **DONE**：全量 pytest：399 passed（基线 390 + 新增 9），1 failed（pre-existing：`test_smoke_req28 / ReadmeRefreshHintTest::test_readme_has_refresh_template_hint`，req-28 遗留，不算回归），39 skipped；
- **DONE（跳过 Step 3）**：escape hatch 文字已由 chg-01（analyst.md 角色文件新建）在 `analyst.md` 第 19 行（硬门禁段）+ 第 52 行（Step B1）两处明示 `"我要自拆"`；chg-03（harness-manager 路由 + technical-director 流转改写）在 `technical-director.md §6.2` 第 168 行明示四触发词全集；本 chg Step 3 可选操作**已由 chg-01 覆盖**，无需追加。

## 3. Validated Approaches

- `pytest tests/test_analyst_role_merge.py -v`：9/9 passed（0.06s）；
- `pytest tests/ -q --tb=no`：399 passed，1 failed（pre-existing），39 skipped（71.92s）；
- 基线对比：390 → 399（+ 9），零减少；
- escape hatch grep 命中：
  - `analyst.md` 行 19、52 含 `"我要自拆"`；
  - `technical-director.md` 行 168 含四触发词 `我要自拆 / 我自己拆 / 让我自己拆 / 我拆 chg`；
  - `test_technical_director_auto_advance_clause` 断言命中（AC-12）。

## 4. Failed Paths

无。

## 5. Candidate Lessons

### 2026-04-23 测试条数与 plan.md 8 条对比
- plan.md Step 2 列出 8 个函数名；实际产出 9 条，因 `test_role_model_map_mirror_sync` 是 plan.md 函数列表中独立一条（plan.md 代码块包含该函数），count 正确。

## 6. Next Steps

- chg-04 executing 已完成；按 plan.md 依赖关系，后续 chg-05（dogfood 活证）可启动。

## 7. Open Questions

无。

---
**escape hatch Step 3 状态**：已由 chg-01（analyst.md 角色文件新建）覆盖，本 chg 跳过，此处留痕。
