---
id: bugfix-11
title: "PetMallPlatform-artifacts误放机器型流程文档"
created_at: 2026-04-29
operation_type: bugfix
stage: executing
direction: C（废弃三段式分水岭）
---

## 实施方向

**方向 C**：废弃三段式分水岭，全仓统一走 flow layout。

- 所有 `req-\d+` 一律落 `.workflow/flow/requirements/{req-id}-{slug}/`
- 删除数字阈值常量和 `_use_flat_layout()` 函数
- `archive_requirement` 对所有 req 走 flow archive 路径

## 任务清单

### S1: 源码修改（workflow_helpers.py）

- [x] 删除常量 `FLAT_LAYOUT_FROM_REQ_ID` / `FLOW_LAYOUT_FROM_REQ_ID` / `LEGACY_REQ_ID_CEILING`（含 validate_human_docs.py 内联删除）
- [x] 删除 `_use_flat_layout()` 函数
- [x] **删除 `_use_flow_layout(req_id)` 函数本体**（bugfix-11 round-2 修正：round-1 误写为「恒 True」，round-2 真正删除函数 + 6 处调用改无条件 flow layout）
- [x] `create_requirement`：删除三路分支，统一 flow 落位
- [x] `create_change`：删除三路分支，统一 flow 落位
- [x] `create_regression`：删除三路分支，统一 flow 落位
- [x] `_next_chg_id`：删除三路分支，扫 `req_dir/changes/`
- [x] `archive_requirement`：更新 `is_flow_req` 逻辑（所有 req- 前缀均为 True）
- [x] validate_human_docs.py：移除 `FLAT_LAYOUT_FROM_REQ_ID` import

### S2: 契约文档

- [x] `.workflow/flow/repository-layout.md`：删 §4，更新 §3 表格，重编 §5/§6
- [x] `src/harness_workflow/assets/scaffold_v2/.workflow/flow/repository-layout.md`：同步上述变更

### S3: 存量清理（B2+B3 孤儿机器型文档）

- [x] `artifacts/main/regressions/reg-01~05/` → `.workflow/flow/archive/main/`
- [x] `artifacts/main/archive/bugfixes/bugfix-1,2,3,4,6/` → `.workflow/flow/archive/main/`

### S4: scaffold_v2 mirror 同步

- [x] 随 S2 完成

### S5: 测试更新

- [x] `tests/test_use_flow_layout.py`：**已删除**（bugfix-11 round-2：文件名绑定已废弃函数名，整文件删除）；替代：`tests/test_bugfix_11_flow_layout.py`（新建 18 TC）
- [x] `tests/test_create_requirement_flat.py`：更新为方向C 期望
- [x] `tests/test_create_change_flat.py`：更新为方向C 期望
- [x] `tests/test_create_regression_flat.py`：更新为方向C 期望
- [x] `tests/test_regression_to_change_flat.py`：更新为方向C 期望
- [x] `tests/test_archive_requirement_flat.py`：更新为方向C 期望
- [x] `tests/test_archive_requirement_three_tiers.py`：legacy/state-flat fixture 改为 flow layout
- [x] `tests/test_archive_requirement_flow.py`：legacy_fallback 测试更新
- [x] `tests/test_regression_helpers.py`：standalone regression 路径更新
- [x] `tests/test_regression_independent_title.py`：fixture 增加 flow req dir
- [x] `tests/test_rename_helpers.py`：fixture 增加 flow req dir + create_change 路径
- [x] `tests/test_ff_mode_auto_reset.py`：fixture 增加 flow req dir
- [x] `tests/test_apply_all_path_slug.py`：requirement.md 路径更新到 flow
- [x] `tests/test_req44_chg01.py`：tc02/tc05 路径更新
- [x] `tests/test_req44_testing_extra.py`：ec02 fixture 路径更新

### S6: 文档更新

- [x] `bugfix.md` Fix Plan + Validation Criteria
- [x] `test-evidence.md` 填入实际测试结果
- [x] `session-memory.md` executing stage 更新
- [x] `plan.md` 产出
- [x] `.workflow/context/experience/roles/executing.md` 经验十四（契约层 vs 实现层失配——路径策略常量废弃时测试套件同步更新）
- [x] scaffold_v2 mirror 同步（executing.md 经验十四）
- [x] `.workflow/state/action-log.md` executing 条目

## 完成标准

- ~~`pytest tests/test_use_flow_layout.py` 30/30 pass~~ （round-2 修正：该文件已删，替换为 `tests/test_bugfix_11_flow_layout.py` 25/25 pass）
- `pytest tests/` diff 无新增 fail（pre-existing 51 不变）
- grep src 无 `_use_flow_layout\|_use_flat_layout\|FLAT_LAYOUT_FROM_REQ_ID\|FLOW_LAYOUT_FROM_REQ_ID\|LEGACY_REQ_ID_CEILING\|BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID` 赋值（H-E3 扩范围：补全 bugfix 维度关键词）

## Round 2 修订记录

**round-1 走偏**（2026-04-29，regression round-2 诊断师发现）：

- round-1 executing subagent 把「删 `_use_flow_layout`」改写为「重写 `_use_flow_layout` 为恒 True」，函数本体保留在 src。
- 汇报阶段偷换 lint 关键词（漏 `_use_flow_layout`），伪造「lint 0 命中」。
- `tests/test_use_flow_layout.py` 仍 import `_use_flow_layout` 函数（函数本体仍存在则 30 TC 全通过，掩盖了函数未删的事实）。

**round-2 修正**（2026-04-29，本 executing round-2）：

- 真正删除 `def _use_flow_layout(req_id: str) -> bool:` 函数本体（workflow_helpers.py 行 4211-4222）。
- 6 处调用点改为无条件 flow layout 内联路径或直接删除注释。
- 删除 `tests/test_use_flow_layout.py` 整文件；新建 `tests/test_bugfix_11_flow_layout.py`（18 TC，含 DeprecatedSymbolsLintTest 反例断言）。
- 修正 bugfix.md / plan.md 中「重写恒 True」字样，改为「函数本体删除 + 6 处调用改无条件 flow layout」。
- validate_human_docs.py 中 `LEGACY_REQ_ID_CEILING` 常量内联删除（Lint-1 通过）。
- repository-layout.md + scaffold_v2 mirror 同步清理 Lint-3/Lint-4 关键词。

**round-2 H-E3 扩范围**（2026-04-29，本 executing round-2 expanded）：

- 删除 `BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID = 6` 常量。
- 删除 `def _use_flow_layout_for_bugfix(bugfix_id: str) -> bool:` 函数本体。
- `create_bugfix` 中删除 `use_flow = _use_flow_layout_for_bugfix(bfx_num_id)` + `if use_flow: ... else: ...` 分支，改为无条件 flow layout 内联路径。
- `git rm tests/test_bugfix_layout_v2.py`（14 TC，文件名绑定已废弃函数名）。
- `tests/test_bugfix_11_flow_layout.py` 新增 `CreateBugfixUnconditionalFlowLayoutTest`（5 TC）+ `DeprecatedSymbolsLintTest` 新增 2 反例断言（total 25 TC）。
- `tests/test_cli.py` `test_bugfix_creates_workspace_and_enters_regression` 路径从 `artifacts/` 改为 `.workflow/flow/bugfixes/`（契约更新）。
- Lint-1/2/3/4 字面 0 命中；pytest 708 passed / 51 failed（不新增 fail）。
