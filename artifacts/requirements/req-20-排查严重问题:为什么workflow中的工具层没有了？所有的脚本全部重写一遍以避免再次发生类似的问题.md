# 排查严重问题:为什么workflow中的工具层没有了？所有的脚本全部重写一遍以避免再次发生类似的问题

> req-id: req-20 | 完成时间: 2026-04-15 | 分支: main

## 需求目标

解决 `.workflow/tools/` 工具层意外缺失的问题，并重写相关脚本以防止再次发生：

1. **根因修复**：`src/harness_workflow/core.py` 中的 `LEGACY_CLEANUP_TARGETS` 错误地将 `.workflow/tools/` 列为旧系统残留，导致 `harness update` 执行清理时把该目录归档到 backup 中，且由于 scaffold_v2 模板中缺少 `.workflow/tools/`，更新后无法恢复。
2. **模板恢复**：在 `src/harness_workflow/assets/scaffold_v2/.workflow/tools/` 中重建完整的 tools 模板，确保 `harness init`/`harness install` 能为新项目正确创建 tools 目录。
3. **当前仓库恢复**：将当前仓库中被误归档到 `.workflow/context/backup/legacy-cleanup/.workflow/tools/` 的内容恢复为 `.workflow/tools/`。
4. **防护增强**：审查并重写/修复 cleanup 和 scaffold 同步逻辑，确保有效工作流目录不会被误清理，并新增测试覆盖。

## 交付范围

### Included
- 修改 `src/harness_workflow/core.py`：
  - 从 `LEGACY_CLEANUP_TARGETS` 中移除 `.workflow/tools/` 及其子目录
  - 确保 `_required_dirs()` 继续包含 `.workflow/tools/` 和 `.workflow/tools/catalog/`
- 重建 `src/harness_workflow/assets/scaffold_v2/.workflow/tools/` 模板目录，包含核心文件：
  - `index.md`
  - `stage-tools.md`
  - `selection-guide.md`
  - `maintenance.md`
  - `catalog/` 目录及工具定义文件
- 恢复当前仓库的 `.workflow/tools/`（从 backup 复制或重新生成）
- 更新/新增测试，验证：
  - `harness update` 不会将 `.workflow/tools/` 移入 backup
  - `harness init` 会在新仓库中创建 `.workflow/tools/`
  - tools 目录中的关键文件在同步后存在且内容正确

### Excluded
- 不修改项目根目录 `tools/lint_harness_repo.py` 的功能逻辑（该脚本属于项目级工具，不在 `.workflow/tools/` 体系内）
- 不重构 scaffold_v2 的其他目录结构或上下文文件内容
- 不修改工作流核心状态机（requirement/change/stage 流转逻辑）
- 不引入新的工具目录层级（保持现有 `catalog/` 结构）

## 验收标准

- [ ] `src/harness_workflow/core.py` 的 `LEGACY_CLEANUP_TARGETS` 列表中不再包含 `Path(".workflow") / "tools"` 及任何 tools 子路径
- [ ] `src/harness_workflow/assets/scaffold_v2/.workflow/tools/` 目录存在，且至少包含：`index.md`、`stage-tools.md`、`selection-guide.md`、`maintenance.md`、`catalog/`（含 `_template.md` 等工具定义文件）
- [ ] 在当前仓库运行 `harness update` 后，`.workflow/tools/` 保持原位，不会被移动到 `.workflow/context/backup/legacy-cleanup/`
- [ ] 当前仓库根目录下 `.workflow/tools/` 已恢复，关键文件（如 `index.md`、`stage-tools.md`）存在且内容完整
- [ ] `pytest` 测试全部通过，且至少新增一个测试用例验证 tools 目录在 init/update 生命周期中不会被误清理

## 变更列表

- **chg-01** chg-01-修复误清理逻辑：修复 `src/harness_workflow/core.py` 中 `LEGACY_CLEANUP_TARGETS` 错误地将 `.workflow/tools/` 列为旧系统残留目录的问题，确保 `harness update` 执行清理时不会将 tools 目录归档到 backup 中。同时确认 `_required_dirs()` 已正确包含 `.workflow/tools/` 和 `.workflow/tools/catalog/`。
- **chg-02** chg-02-重建tools模板：在 `src/harness_workflow/assets/scaffold_v2/.workflow/tools/` 中重建完整的 tools 模板目录，确保 `harness init` / `harness install` / `harness update` 在为新项目同步工作流结构时，能正确创建 tools 目录及其核心文件。
- **chg-03** chg-03-恢复当前仓库tools目录：将当前仓库中被误归档到 `.workflow/context/backup/legacy-cleanup/.workflow/tools/` 的内容恢复为项目根目录下的 `.workflow/tools/`，使本仓库的工作流工具层重新可用。
- **chg-04** chg-04-补充测试覆盖：在现有测试基础上新增/更新测试用例，验证 `.workflow/tools/` 目录在 `harness init` 和 `harness update` 生命周期中不会被误清理，且 scaffold 同步能正确创建 tools 目录及其核心文件。
