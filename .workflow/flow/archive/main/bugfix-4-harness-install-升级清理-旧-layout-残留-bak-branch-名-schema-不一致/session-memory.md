# Session Memory — bugfix-4（harness install 升级清理：旧 layout 残留 / .bak / branch 名 / schema 不一致）

> 角色：诊断师（regression / opus）
> 加载链：runtime.yaml → base-role.md → stage-role.md → regression.md → role-model-map.yaml → repository-layout.md → workflow_helpers.py（install_repo 链）→ PetMallPlatform 现场扫描 → bugfix.md 工作区。

## 1. Current Goal

诊断 bugfix-4（harness install 升级清理：旧 layout 残留 / .bak / branch 名 / schema 不一致）三层根因，给出修复路径与路由建议；不修代码 / 不动 git。

## 2. Current Status

- 完成现场扫描（PetMallPlatform `.workflow/` + `artifacts/` + git 痕迹）；
- 完成 install_repo 链 + cleanup_legacy_workflow_artifacts + _migrate_state_files + _sync_scaffold_v2_mirror_to_live 的源码阅读；
- 完成 `repository-layout.md` §1-§4 + LEGACY_CLEANUP_TARGETS 白名单的契约面对照；
- 已写 `regression/diagnosis.md`（三层根因 + 三方向修复 + 路由建议）+ `bugfix.md`（覆写 Problem / Root Cause / Fix Scope / Fix Plan / Validation Criteria）。

## 3. Validated Approaches

- 现场样本扫描：`ls /Users/jiazhiwei/claudeProject/PetMallPlatform/.workflow/{flow,state}/ + /artifacts/` 一次性确认四类残留。
- 源码定位：`grep -n "install_repo\|cleanup\|legacy\|\.bak\|migrate" workflow_helpers.py` 一次性锁定关键 helper 链 + 行号。
- 契约对照：`repository-layout.md` §4 历史存量豁免规则——req-02 ~ req-40 旧结构禁迁移，确认 chg-3 schema 探测扩 folder 形态时**只识别不迁移**（合契约）。

## 4. Failed Paths

- 无（首次诊断即定位三层根因，无需推翻假设）。

## 5. Candidate Lessons

```markdown
### 2026-04-25 install_repo cleanup 闭环缺口的诊断模式

- Symptom: 存量项目多次 install 后 .workflow/ 出现持久残留（旧 layout / .bak / 多 schema）。
- Cause: install 链是单向"加" + 单向"mirror→live push"；缺一个"对照 mirror 反向 prune live 中过期文件"通道；schema 迁移产出 .bak 后无后续清理任务。
- Fix: cleanup phase 扩展 + 新 helper（cleanup_state_bak_files）+ schema 探测扩 folder 分支；契约 §4 历史豁免规则约束清理面（识别不迁移）。
- 适用场景：所有"工具型仓库做版本演进 + 存量项目升级"的产品，凡是 mirror→live 单向同步都需对偶的 prune 通道。
```

## 6. Next Steps

- executing 阶段已完成（见 §10）；测试通过。主 agent 可推进到 testing。

## 7. Open Questions

- 无。

## 8. default-pick 决策清单

- 无。本次 executing 4 个修复点均无歧义判断点，按任务说明直接推进。

## 9. 待处理捕获问题（职责外）

- branch 命名规约（`{branch}` 抽象 + 多形态混用）应另起 sug / req 修 `repository-layout.md`，加 §branch 命名规约段；本次 bugfix 不动。

## 11. Testing 阶段执行日志

> 角色：测试工程师（testing / sonnet）
> 执行时间：2026-04-23
> expected_model：sonnet；本次 subagent 无法自省，依 role-model-map.yaml 声明落位 sonnet

### 4 修复点独立验证

- [x] **修复 1（LEGACY_CLEANUP_TARGETS 扩 layout 残留）**：`grep "artifacts-layout.md" workflow_helpers.py` 命中 2 行（L109 注释 + L112 Path 条目）✅
- [x] **修复 2（cleanup_state_bak_files helper）**：定义 1 处（L3462）+ install_repo 调用 1 处（L3718），共 2 行命中，符合"定义 + 调用"预期 ✅
- [x] **修复 3（schema folder 形态 audit）**：`grep "audit\|⚠️\|folder 形态" workflow_helpers.py` 命中多行，含 L3773-L3788 folder-scan 分支及 `⚠️ 检测到旧 schema folder 形态` audit 警告 ✅
- [x] **修复 4（pytest 覆盖）**：`tests/test_install_cleanup.py` 5 个测试用例 5/5 全绿 ✅

### 全量 pytest 回归检查

- 总计：453 passed + 2 failed（pre-existing）+ 52 skipped
- 2 个已知 pre-existing 失败：`test_smoke_req28.py::ReadmeRefreshHintTest::test_readme_has_refresh_template_hint` + `test_smoke_req29.py::HumanDocsChecklistTest::test_human_docs_checklist_for_req29`
- 零新增回归 ✅（passed 453 ≥ 452 + pre-existing 2 = 与预期 baseline 一致）

### default-pick 决策清单

- 无。4 修复点验证均无歧义判断，全部直接推进。

## 10. Executing 阶段执行日志

> 角色：开发者（executing / sonnet）
> 执行时间：2026-04-23
> expected_model：sonnet；自省降级留痕：无（本次为 subagent 无法自省，依 role-model-map.yaml 声明落位 sonnet）

### 修复点完成情况

- [x] chg-1（install_repo cleanup 扩 layout 残留）：`LEGACY_CLEANUP_TARGETS` 追加 `.workflow/flow/artifacts-layout.md`（bugfix-4（harness install 升级清理：旧 layout 残留 / .bak / branch 名 / schema 不一致）chg-1）。
- [x] chg-2（state .bak 残留清理 helper）：新建 `cleanup_state_bak_files(root, check)` helper + 在 `install_repo` `_migrate_state_files` 调用之后调用（bugfix-4 chg-2）。
- [x] chg-3（schema 探测扩 folder 形态 + audit 报告）：`_migrate_state_files` 新增 folder-scan 分支，扫 `req-XX/` folder 形态，输出 `⚠️ 检测到旧 schema folder 形态` audit 警告，不删不迁（bugfix-4 chg-3）。
- [x] chg-4（pytest 覆盖）：新建 `tests/test_install_cleanup.py`，5 个测试用例全绿（bugfix-4 chg-4）。

### 验证自检（Grep 检查点）

- `grep "artifacts-layout.md" workflow_helpers.py` → 命中 2 行（LEGACY_CLEANUP_TARGETS）✅
- `grep "cleanup_state_bak_files" workflow_helpers.py` → 命中 2 行（定义 L3462 + 调用 L3718）✅
- `grep "⚠️" workflow_helpers.py` → 命中（schema audit 警告 L3784 + L3788）✅

### Pytest 结果

- 新增测试：`tests/test_install_cleanup.py` 5 passed ✅
- 全量：452 passed + 2 pre-existing fail（`ReadmeRefreshHintTest` + `test_human_docs_checklist_for_req29`）+ 38 skipped ✅（零回归）
