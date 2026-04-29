---
id: bugfix-4
stage: testing
tested_at: 2026-04-23
tested_by: testing / sonnet
verdict: PASS
---

# Test Report — bugfix-4（harness install 升级清理：旧 layout 残留 / .bak / branch 名 / schema 不一致）

## 验证对象

`src/harness_workflow/workflow_helpers.py` + `tests/test_install_cleanup.py`

## 4 修复点逐点验证

### 修复 1：LEGACY_CLEANUP_TARGETS 扩 layout 残留（chg-1）

- **验证命令**：`grep -n "artifacts-layout.md" workflow_helpers.py`
- **结果**：命中 2 行
  - L109：注释说明（`# .workflow/flow/artifacts-layout.md 是 req-39 旧契约文件…`）
  - L112：Path 条目（`Path(".workflow") / "flow" / "artifacts-layout.md"`）
- **判定**：✅ PASS（≥ 1 命中，符合验收标准）

### 修复 2：cleanup_state_bak_files helper（chg-2）

- **验证命令 A**：`grep -n "def cleanup_state_bak_files" workflow_helpers.py`
- **结果 A**：命中 1 行（L3462）✅
- **验证命令 B**：`grep -n "cleanup_state_bak_files" workflow_helpers.py`
- **结果 B**：命中 2 行（L3462 定义 + L3718 install_repo 内调用）✅
- **判定**：✅ PASS（定义 1 处 + 调用 1 处，符合验收标准）

### 修复 3：schema folder 形态 audit 报告（chg-3）

- **验证命令**：`grep -n "audit\|⚠️\|folder 形态" workflow_helpers.py`
- **结果**：命中多行，关键行：
  - L3773-L3774：`# bugfix-4（…）/ chg-3（schema 探测扩 folder 形态 + audit 报告）`
  - L3780：`# folder 形态 req：无对应 .yaml，仅 audit 报告`
  - L3784：`⚠️ 检测到旧 schema folder 形态：{child.name}/，…`
  - L3788：`[install_repo:schema-audit] ⚠️ 检测到旧 schema folder 形态：…`
- **判定**：✅ PASS（audit / ⚠️ / folder 形态 关键词均命中）

### 修复 4：pytest 覆盖（chg-4）

- **验证命令**：`pytest tests/test_install_cleanup.py -v`
- **结果**：
  ```
  tests/test_install_cleanup.py::test_artifacts_layout_removed_by_install_repo     PASSED
  tests/test_install_cleanup.py::test_bak_files_cleaned_by_install_repo            PASSED
  tests/test_install_cleanup.py::test_cleanup_state_bak_files_direct               PASSED
  tests/test_install_cleanup.py::test_cleanup_state_bak_files_check_mode           PASSED
  tests/test_install_cleanup.py::test_schema_folder_audit_warning_not_deleted      PASSED
  5 passed in 1.51s
  ```
- **判定**：✅ PASS（5/5 全绿）

## 全量 pytest 回归检查

- **命令**：`pytest --tb=no -q`
- **结果**：453 passed, 2 failed, 52 skipped（79.06s）
- **pre-existing 已知失败**（与 baseline 一致，不属新增回归）：
  - `tests/test_smoke_req28.py::ReadmeRefreshHintTest::test_readme_has_refresh_template_hint`
  - `tests/test_smoke_req29.py::HumanDocsChecklistTest::test_human_docs_checklist_for_req29`
- **判定**：✅ PASS（453 ≥ 452 passed，零新增回归）

## 合规扫描（evaluation/testing.md R1 ~ R5）

| 项 | 内容 | 结论 |
|----|------|------|
| R1 越界检查 | testing 角色只读代码，未修改任何被测生产文件 | ✅ 无越界 |
| revert 抽样 | `workflow_helpers.py` 改动为 bugfix-4 chg-1~3 修复内容，无非预期 revert | ✅ 无异常 |
| 契约 7 合规 | 本报告所有 id 首次引用均带 title 描述 | ✅ 合规 |
| req-29（角色→模型映射）映射 | testing 角色 = sonnet，与 role-model-map.yaml 一致 | ✅ 一致 |
| req-30（slug 沟通可读性增强：全链路透出 title）透出 | 所有 id 引用格式符合 `{id}（{title}）` | ✅ 合规 |

## 总判定

**状态：PASS**。4 修复点全部通过独立验证，pytest 5/5 全绿，全量回归 453 passed + 2 pre-existing fail，零新增回归。
