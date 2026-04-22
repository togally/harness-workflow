# Session Memory

## 1. Current Goal

- 修复 `resolve_archive_root` 判据：primary 优先，legacy 仅显式 opt-in。覆盖 req-29 AC-03。

## 2. Current Status

- planning 阶段已产出：change.md / plan.md / 变更简报.md。
- executing 已完成（2026-04-19）：
  - ✅ Step 1 调用点扫描：仅 `archive_requirement` 一处调用，无依赖老降级行为的测试。
  - ✅ Step 2 改判据：`resolve_archive_root` 默认返回 primary；opt-in 同时支持 `prefer_legacy: bool = False` 参数和 `HARNESS_ARCHIVE_LEGACY=1` 环境变量（briefing 明确要求两种都支持）。默认分支把老 warning 改为 notice 级迁移提示；opt-in 分支保留原 warning 并把文案从 `harness migrate requirements` 修为 `harness migrate archive`。
  - ✅ Step 3 补 import os；新增 3 条测试（`test_resolve_archive_root_returns_primary_by_default`、`test_resolve_archive_root_returns_legacy_when_opted_in`（含参数/环境变量/空 legacy 三个子 case）、`test_archive_new_requirement_lands_in_primary`）。
  - ✅ Step 4 跑测：`tests.test_archive_path` 5/5；`discover -s tests` 140/140（36 skipped）无回归。
  - ✅ 对人文档 `实施说明.md` 已产出。

## 3. Validated Approaches

- 在 `src/harness_workflow/workflow_helpers.py` 约 4280 行定位到 `resolve_archive_root`，确认当前判据链：primary 非空 → primary；legacy 非空 → legacy 告警；否则 primary。
- 本 change 是 chg-02（migrate --archive）的前置，必须先合入。

## 4. Failed Paths

- Attempt: 无
- Failure reason: n/a
- Reminder: 不要把 `resolve_requirement_root` / `resolve_bugfix_root` 一并改（scope creep）。

## 5. Candidate Lessons

```markdown
### 2026-04-19 归档路径降级判据设计原则
- Symptom: legacy 非空即自动降级 → 新归档路径被老数据"绑架"。
- Cause: 判据链按"哪个目录有内容"而非"哪个是规范目标"选择。
- Fix: 规范路径（primary）应始终优先，legacy 仅在显式 opt-in 时使用，打一次迁移提示引导用户收敛。
```

## 6. Next Steps

- executing 角色接手时先 grep 所有调用方 + 现有测试断言，再修函数。
- 测试先行：补 2 条用例，跑红再改实现。

## 7. Open Questions

- ~~opt-in 机制选参数还是环境变量？~~ **已敲定（2026-04-19 executing）**：按 briefing 要求两种都支持——`prefer_legacy: bool = False` 参数（调用方显式、测试友好） + `HARNESS_ARCHIVE_LEGACY=1` 环境变量（运维兜底、无需改调用方）；二者任一命中即 opt-in。参数优先在函数签名中声明，环境变量作为 OR 条件。

## 8. 交接 chg-02 要点

- **legacy 下待迁移的目录清单**（migrate 命令要搬的对象）：
  - `.workflow/flow/archive/requirements/` 下所有历史归档（req-26 / req-28 等落过这里的 requirement 目录）。
  - `.workflow/flow/archive/bugfixes/` 下所有历史 bugfix 归档（bugfix-3/4/5/6 因老判据落 legacy）。
  - 历史遗留的"双层 branch"目录（如 `artifacts/main/archive/main/req-xx`）不在本 chg 范围，维持 `test_archive_path_preserves_legacy` 的 Excluded 语义。
- **目标路径**：统一搬到 `artifacts/{branch}/archive/{requirements|bugfixes}/<dir>`；冲突处理策略（跳过 / 报错 / 覆盖）待 chg-02 明确。
- **触发点**：用户在默认路径下执行 `harness archive/status` 时会看到新的 notice 级迁移提示 `run harness migrate archive to consolidate`——chg-02 需确保此命令可用。
