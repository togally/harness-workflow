# Change: 恢复当前仓库 tools 目录

## 变更目标

将当前仓库中被误归档到 `.workflow/context/backup/legacy-cleanup/.workflow/tools/` 的内容恢复为项目根目录下的 `.workflow/tools/`，使本仓库的工作流工具层重新可用。

## 范围

### 包含
- 在项目根目录创建 `.workflow/tools/` 目录
- 从 `.workflow/context/backup/legacy-cleanup/.workflow/tools/` 复制全部文件和子目录到 `.workflow/tools/`
- 确保关键文件（`index.md`、`stage-tools.md`、`selection-guide.md`、`maintenance.md`、`catalog/` 及其内容）完整恢复

### 不包含
- 不修改 backup 中的归档内容
- 不修改 core.py 或 scaffold 模板（分别由 chg-01 和 chg-02 负责）
- 不新增测试（由 chg-04 负责）

## 验收标准

- [ ] 项目根目录下存在 `.workflow/tools/`
- [ ] `.workflow/tools/index.md`、`.workflow/tools/stage-tools.md`、`.workflow/tools/selection-guide.md`、`.workflow/tools/maintenance.md` 存在且内容完整
- [ ] `.workflow/tools/catalog/` 目录存在且包含工具定义文件
- [ ] 运行 `harness update` 后，`.workflow/tools/` 保持原位，不会被移动到 backup
