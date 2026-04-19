# Change: 重建 tools 模板

## 变更目标

在 `src/harness_workflow/assets/scaffold_v2/.workflow/tools/` 中重建完整的 tools 模板目录，确保 `harness init` / `harness install` / `harness update` 在为新项目同步工作流结构时，能正确创建 tools 目录及其核心文件。

## 范围

### 包含
- 在 `src/harness_workflow/assets/scaffold_v2/.workflow/tools/` 下创建以下文件和目录：
  - `index.md`
  - `stage-tools.md`
  - `selection-guide.md`
  - `maintenance.md`
  - `catalog/` 目录及其中所有工具定义文件（如 `_template.md`、`agent.md`、`bash.md` 等）
- 文件内容从 `.workflow/context/backup/legacy-cleanup/.workflow/tools/` 复制并整理

### 不包含
- 不修改 scaffold_v2 的其他目录结构
- 不修改当前仓库根目录下的 `.workflow/tools/`（由 chg-03 负责）
- 不修改任何代码逻辑

## 验收标准

- [ ] `src/harness_workflow/assets/scaffold_v2/.workflow/tools/` 目录存在
- [ ] 至少包含：`index.md`、`stage-tools.md`、`selection-guide.md`、`maintenance.md`
- [ ] `catalog/` 子目录存在，且至少包含 `_template.md`
- [ ] 所有文件内容与 backup 中的源文件一致（直接复制即可）
