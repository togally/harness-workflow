# Session Memory

## 1. Current Goal

- chg-03（validate_human_docs 重写删四类 brief）：在 `validate_human_docs.py` 新增 `BRIEF_DEPRECATED_FROM_REQ_ID = 41`，重写扫描逻辑三分支，扩展 pytest。

## 2. Current Status

- 全部 6 Steps 已完成 ✅
- 22/22 test_validate_human_docs.py PASS
- 全量 pytest：3 个预存在失败（chg-02（CLI 路径迁移）workflow_helpers.py 并行变更导致，与 chg-03 无关）

## 3. Completed Tasks

- [x] Step 1：读取 validate_human_docs.py 全文 + 现有常量结构分析
- [x] Step 2：新增常量 `BRIEF_DEPRECATED_FROM_REQ_ID = 41`（方案 A：本地定义，不走 workflow_helpers import）
- [x] Step 3：新增 `REQ_LEVEL_DOCS_SIMPLIFIED`（只含 requirement.md + 交付总结.md）；更新注释，`HUMAN_DOC_CONTRACT` 新增 raw_artifact 键；`CHANGE_LEVEL_DOCS` / `BUGFIX_LEVEL_DOCS` 维持现状（只有精简路径不调用它们）
- [x] Step 4：新增 `_collect_req_items_simplified()` 函数；`_collect_req_items()` 扫描入口加四分支（req-41（本需求）+ 精简 / req-39（对人文档家族契约化）-40（阶段合并）现行 / req-38（api-document-upload 工具闭环）mixed / ≤37 legacy）
- [x] Step 5：扩展 pytest 22 条（新增 7 条 + 修复 5 条既有用例因 req-99（虚拟测试占位）→ req-40（阶段合并）命名调整）；修复 test_smoke_req28.py::ValidateHumanDocsSmokeTest::test_validate_human_docs_reports_missing_and_present（req-77（测试 fixture 占位 ID）→ req-40（阶段合并与用户介入窄化））
- [x] Step 6：自检验证全部通过

## 4. Results

- `src/harness_workflow/validate_human_docs.py`：新增 BRIEF_DEPRECATED_FROM_REQ_ID = 41 + REQ_LEVEL_DOCS_SIMPLIFIED + _collect_req_items_simplified + 四分支 _collect_req_items
- `tests/test_validate_human_docs.py`：新增 7 条 + 修复 5 条；共 22 条全绿
- `tests/test_smoke_req28.py`：1 条用例更新（req-77 → req-40）

## 5. Default-Pick 决策清单

- D-A：方案 A（本地定义 BRIEF_DEPRECATED_FROM_REQ_ID = 41）vs 方案 B（workflow_helpers 中心化 import）→ 选 A，原因：语义独立，避免循环依赖风险，与 plan.md 推荐一致
- D-B：既有使用 req-99 的测试用例（req-99 >= 41 触发精简分支）→ 改用 req-40（现行扫描），保持对原来"四类 brief 扁平路径"行为的回归覆盖；未删除任何测试，改写后语义等价

## 6. Next Steps

- 主 agent 推进到 testing 阶段独立复核

## 7. Open Questions

- 无

---

本阶段已结束。
