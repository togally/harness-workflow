# Plan: 重建 tools 模板

## 执行步骤

1. 确认源目录 `.workflow/context/backup/legacy-cleanup/.workflow/tools/` 中的文件列表（已知包含 index.md、stage-tools.md、selection-guide.md、maintenance.md、catalog/ 及多个工具定义文件）。
2. 在 `src/harness_workflow/assets/scaffold_v2/.workflow/` 下创建 `tools/` 目录。
3. 将 backup 中的 `index.md`、`stage-tools.md`、`selection-guide.md`、`maintenance.md` 复制到目标目录。
4. 在目标目录下创建 `catalog/` 子目录，并将 backup 中 `catalog/` 下的所有 `.md` 文件复制过去。
5. 核对文件数量和名称，确保无遗漏。

## 预期产物

- 新建目录 `src/harness_workflow/assets/scaffold_v2/.workflow/tools/`
- 新建目录 `src/harness_workflow/assets/scaffold_v2/.workflow/tools/catalog/`
- 复制到位的多个 `.md` 文件

## 依赖关系

- **前置依赖**：chg-01 必须已完成，确保后续 `harness update` 不会把刚重建的模板再次误清理。
- **后置依赖**：chg-03 依赖于本变更，因为当前仓库的 tools 恢复内容应与模板保持一致。
