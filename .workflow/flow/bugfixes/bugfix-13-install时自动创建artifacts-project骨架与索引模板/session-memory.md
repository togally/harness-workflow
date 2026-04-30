---
id: bugfix-13
title: "install时自动创建artifacts-project骨架与索引模板"
created_at: 2026-04-30
operation_type: bugfix
stage: regression
---

## Current Goal
- 独立诊断 req-52 chg-04（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证 / 接入主流程-stderr日志-端到端CLI验证）落地后遗留的 install 写盘缺口：用户仓 `harness install` 时不会自动创建 `artifacts/project/` 骨架。

## Current Status
- Subagent-L1（regression / opus）执行；模型自检与 role-model-map.yaml `roles[regression].model = opus` 一致。
- 诊断完成，verdict = real-issue，route = executing。
- 4 份产出全部落位：bugfix.md + regression/diagnosis.md + regression/required-inputs.md + session-memory.md（本文件）。

## Validated Approaches
- 主 agent 4 条结论独立复核（diagnosis.md §3 表格）：4/4 全部成立。
- `find src/.../scaffold_v2 -name "*project*"` + `find -type d`：scaffold_v2 树仅 `.workflow/`，无 `artifacts/`。
- `grep "artifacts/project/" workflow_helpers.py`：命中点全部为读路径 / 白名单注释，无写盘代码。
- `_SCAFFOLD_V2_MIRROR_WHITELIST` L172-L208：双兜底 "artifacts/project/" + "/project/" 明文豁免，"artifacts/ 不入 mirror" 契约成立。
- `_load_project_level_index` scope_map（L8420-L8427）：仅枚举 6 scope（constraints / experience-roles / experience-tool / experience-risk / experience-regression / experience-stage），`tools` 不参与索引懒加载——解释了自身仓 `artifacts/project/tools/` 仅 `.gitkeep` 无 index.md 的设计。

## Failed Paths
- 未尝试通过 mirror sync 链路自动建骨架（违反契约，被白名单 + repository-layout.md §2.1 双重锁定）。
- 未考虑硬编码字符串模板（OQ-A 候选 B）—— 内容与代码分离原则，长期维护差。

## default-pick 决策清单
- OQ-A（模板放哪）= A：新增 `src/harness_workflow/assets/templates/project-skeleton/` 独立模板树 — 结构性强 + 与 mirror 物理隔离 + 无变量无须 render
- OQ-B（写盘点）= A：install_repo 入口段（_ensure_workflow_dir_gitignore 之后、项目级合并循环之前） — 覆盖 install + update 双路径
- OQ-C（幂等策略）= A + C：write_if_missing + check 模式 dry-run — 现有 helper 天然幂等 + 不破用户写保护
- OQ-D（README 内容）= 1:1 复刻自身仓 README.md — 自身仓即权威范本，无需重设计

## Candidate Lessons
- 2026-04-30 req 落地半截工程模式 — Symptom：读路径 + 日志已接通，写盘骨架漏 | Cause：install_repo 项目级合并循环只读不写，主路径不存在时仅记 0 命中默默放过 | Fix：执行 install_repo 入口段插 `_bootstrap_project_skeleton(root, check)`，模板树落 `assets/templates/project-skeleton/`（mirror 外），write_if_missing 幂等。
- 2026-04-30 契约硬约束驱动模板落位选择 — Symptom：候选 modules 看似都能放（scaffold_v2 / templates / 硬编码） | Cause：mirror 白名单"artifacts/project/" + "/project/" 双兜底**正是**为了防 mirror 反向覆盖用户写入 | Fix：模板**必须**放 mirror 外（`assets/templates/project-skeleton/`），install_repo 显式 bootstrap 而非"顺手 sync"。

## 待处理捕获问题
- 无（diagnosis.md §4 已穷举 4 个 OQ + default-pick + 理由；required-inputs.md 标"无阻塞"）。

## Next Steps / Open Questions
- 主 agent 收到本汇报后，直接 `harness regression --confirm` 推 executing；
- executing 阶段建议：
  - 先建模板树（7 文件 + 3 .gitkeep = 10 文件，1:1 复刻自身仓 `artifacts/project/`）；
  - 再加 helper + install_repo 接入点；
  - 不动现有 `_SCAFFOLD_V2_MIRROR_WHITELIST` / `_merge_project_level_files` / `_load_project_level_index`；
  - testing 阶段必跑子进程 dogfood（`subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'install'])`）—— 参考 regression 经验十"三维失配"，单元测试直调 helper 不够，必须子进程真跑 CLI 验证部署链路。
- Question：无。

---

## Round 1 Executing

**Subagent**：Subagent-L1（executing / sonnet）

### 完成标记 ✅

1. ✅ 新建模板树 `src/harness_workflow/assets/templates/project-skeleton/`（10 文件：README.md + 6 index.md + 3 .gitkeep，1:1 复刻自身仓 `artifacts/project/`）
2. ✅ 新增 `_bootstrap_project_skeleton(root, check)` helper 到 `workflow_helpers.py`（L3745）
3. ✅ 在 `install_repo()` 内 `_ensure_workflow_dir_gitignore` 之后调用 helper（L3816）
4. ✅ 新建 `tests/test_bugfix_13_project_skeleton_bootstrap.py`（10 TC：TC-01/02/03/04/05/06 + TC-07 模板清单 + TC-08a/08b/08c helper 直调）
5. ✅ `bugfix.md` Validation Criteria [x] 标记
6. ✅ `test-evidence.md` 填入真实数据 + `## 结论` 段

### 6 lint 完整 stdout

**lint A**：`pytest tests/test_bugfix_13_project_skeleton_bootstrap.py -v`
```
10 passed in 8.09s
```

**lint B**：`ls src/harness_workflow/assets/templates/project-skeleton/`
```
constraints  experience  README.md  tools
```

**lint C**：`find project-skeleton/ -type f | wc -l`
```
10
```

**lint D**：`grep -n "_bootstrap_project_skeleton" workflow_helpers.py`
```
3745:def _bootstrap_project_skeleton(root: Path, check: bool = False) -> list[str]:
3816:    _bootstrap_actions = _bootstrap_project_skeleton(root, check=check)
```

**lint E**：dogfood fresh repo
```
[install_repo] project skeleton: created 10 files / skipped 0 files
artifacts/project/: README.md + constraints/ + experience/ + tools/ 存在
find count: 10
```

**lint F**：`pytest tests/ --tb=no -q | tail -5`
```
52 failed, 754 passed, 40 skipped, 1 warning, 17 subtests passed in 139.97s
```

### 无法满足的 plan 条款

无。所有条款均已实现。

### 备注

- `validate --contract all` 退出码 1 为**预存在**历史 contract-7 violations，非本次引入。
- `validate --contract user-write-protected-zones` PASS（exit=0）。
- 52 failed 全为预存在失败（不含 bugfix-13 测试文件），754 passed ≥ 751 要求。
