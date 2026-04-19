# chg-03 Session Memory — 归档默认 folder

## 执行状态
- [x] 步骤 1：分析 archive_requirement 现有实现
- [x] 步骤 2：新增 _get_git_branch 辅助函数
- [x] 步骤 3：修改 archive_requirement 使用 git branch 作为默认 folder

## 关键决策
- `_get_git_branch()` 使用 `subprocess.run` + `cwd=root`，timeout=5，capture_output=True
- branch 中 `/` 替换为 `-`（feature/auth → feature-auth）
- detached HEAD 或非 git 仓库均返回空字符串，降级为 archive 根目录

## 修改位置
- `src/harness_workflow/core.py`：`_get_git_branch()` 在 `archive_requirement()` 之前（原 3028 行区域）
- `archive_requirement()` 函数头部加入 `if not folder: folder = _get_git_branch(root)`
