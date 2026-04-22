# Completion — chg-01 完成 requirement 路径迁移到 artifacts/{branch}

## 状态

**已完成（executing 阶段全步骤通过 + 内部单元自测 + 端到端测试床 10/10 通过）**

## 交付清单

### 代码改动
1. `src/harness_workflow/workflow_helpers.py`
   - 新增 `import sys`
   - 新增模块级常量 `_REQUIREMENT_ROOT_NOISE_FILENAMES`
   - 新增 helper `_has_substantive_content` / `resolve_requirement_root` / `resolve_archive_root` / `migrate_requirements`
   - 替换 9 处硬编码 `.workflow/flow/requirements` → `resolve_requirement_root(root)`（或在 `_required_dirs` / `_next_req_id` 中以"追加扫描源"方式保留 legacy）
   - P1-06：`archive_requirement` 的 `archive_base` → `resolve_archive_root(root)`
2. `src/harness_workflow/cli.py`
   - `build_parser` 新增 `migrate_parser`（`migrate requirements [--dry-run]`）
   - `main` 新增 `migrate` 分支
3. `src/harness_workflow/tools/harness_migrate.py`（新增工具脚本）

### DoD 校验

- [x] 新建 `resolve_requirement_root(root)`：三级降级 + stderr 告警 + migrate 引导（源码确认）
- [x] helper 的"非空"判定过滤噪声（`{".DS_Store", ".gitkeep", "Thumbs.db", ".keep"}`，模块级 frozenset，可扩展）
- [x] 9 处硬编码已全部替换（`grep` 校对：剩余的 `.workflow/flow/requirements` 字样仅出现在 helper 内部 legacy 回退、`_required_dirs` 保留、`_next_req_id` 追加扫描、docstring、migrate 扫描源）
- [x] 新增 `harness migrate requirements`：dry-run / 正式运行 / 幂等 / 冲突不覆盖 四种行为经 32 个单元断言 + 4 个端到端场景确认
- [x] 测试床 `harness validate` rc=0（T2 空仓新路径场景 + T9 迁移后场景 + T10 迁移前 legacy 场景）
- [x] 测试床 `harness archive` 产物落到 `artifacts/main/archive/`（T4d 确认）
- [x] 测试床 `harness rename`（T3：id 引用形式，rc=0）
- [x] legacy 模拟仓：dry-run + 正式迁移 + 二次幂等 均符合预期
- [x] 冲突仓：目标已存在时报错不覆盖（T8 rc=1、src/dst 均未动）
- [x] **P1-06 archive_base 对齐 `artifacts/{branch}/archive`**：已纳入并验证（T4d 产物落到 `artifacts/main/archive/chg01-test/test-b/`）。**未延期。**
- [x] `_required_dirs` 在 init 时同时创建 legacy 与新路径（验证见 T1 前置：init 后 `artifacts/main/requirements/` 与 `.workflow/flow/requirements/` 都存在）
- [x] 未破坏 req-27 `create_requirement` / `create_change`（T1 create + T1 后续 change workspace 均成功生成）
- [ ] 沉淀经验 —— session-memory.md §5 已列候选 3 条；**留给 testing/acceptance 验证后再入库**（避免未验证经验污染）

### P1-06 状态

**已对齐**。`archive_requirement` 的 `archive_base = resolve_archive_root(root)`，helper 降级告警与文案与 `resolve_requirement_root` 同步。T4d 端到端验证产物落到新路径。**无延期项。**

### 延期项

无。本 change 的全部范围已实现并测试通过。

### 衍生问题（非本 change 范围，已在 session-memory §6 记录）

1. `harness archive` CLI interactive wrapper 强制 prompt，忽略显式参数。
2. `rename requirement` 未更新 `state/requirements/*.yaml` 文件名 + runtime active_requirements。
3. `resolve_artifact_id` 在 english language 下 slugify 造成 `req-01` 被重命名后目录名丢失 `req-NN-` 前缀。
4. `harness init` 后 runtime.yaml 被 scaffold 预置 `current_requirement: req-25` + `stage: done`（P0-02 范围）。
5. `OPTIONAL_EMPTY_DIRS` 仍含 `.workflow/flow/archive`，init 会生成 scaffold 残留（P0-02 范围）。

这些不阻断本 chg-01 的 DoD 达成；部分在测试床演示时需要手工清理（已在 session-memory §6 标注）。

## 测试证据

- 单元自测：`/tmp/harness-chg01-selftest/test_helpers.py` 32/32 PASS
- 测试床：
  - `/tmp/harness-regression-chg01-fresh-1776570607`（主场景 T1-T4）
  - `/tmp/harness-regression-chg01-legacy-1776570678`（T5-T7, T9）
  - `/tmp/harness-regression-chg01-conflict-1776570703`（T8）
  - `/tmp/harness-regression-chg01-legacy-presence-1776570737`（T10）
- 日志：各 bed 下 `regression-logs/chg-01/*.log`

## 下一步

- 交给 testing 阶段做独立验证。
- acceptance 阶段核对 DoD 每条。
- done 阶段做六层回顾后再决定经验沉淀入库。
