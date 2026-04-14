# 执行计划

## 依赖关系
- **前置依赖**：无
- **后置依赖**：chg-04（交互式归档选择在此基础上叠加）

## 执行步骤

### 步骤 1：了解现有 archive_requirement 实现
1. 阅读 `core.py` 第 2988 行起的 `archive_requirement(root, requirement_name, folder="")` 函数
2. 确认 `folder` 为空时的现有行为：`target_parent = archive_base`（直接放 archive 根下）
3. 确认 `folder` 非空时的现有行为：`target_parent = archive_base / folder`

### 步骤 2：新增 _get_git_branch 辅助函数
1. 在 `core.py` 中新增辅助函数（建议放在 `archive_requirement` 之前）：
   ```python
   def _get_git_branch(root: Path) -> str:
       """读取当前 git 分支名，失败时返回空字符串。"""
       import subprocess
       try:
           result = subprocess.run(
               ["git", "branch", "--show-current"],
               cwd=str(root),
               capture_output=True,
               text=True,
               timeout=5,
           )
           branch = result.stdout.strip()
           return branch.replace("/", "-") if branch else ""
       except Exception:
           return ""
   ```

### 步骤 3：修改 archive_requirement 使用 git branch 作为默认 folder
1. 定位 `archive_requirement()` 函数（第 2988 行）
2. 在函数体开始处（解析 `req_dir` 之后），增加 folder 默认值逻辑：
   ```python
   # 若未传 folder，读取 git branch 作为默认
   if not folder:
       folder = _get_git_branch(root)
   ```
3. 其余逻辑保持不变（`folder` 为空时 `target_parent = archive_base`，非空时 `target_parent = archive_base / folder`）

### 步骤 4：更新打印信息
1. 归档成功后的打印信息中确保显示实际使用的路径（`target`），已有 `print(f"Archive path: {target}")` 无需额外修改

## 预期产物
1. `core.py` 新增 `_get_git_branch(root: Path) -> str` 辅助函数
2. `archive_requirement()` 在 `folder` 为空时自动读取 git branch 名

## 验证方法
1. 在 git 仓库（`main` 分支）执行 `harness archive req-xx`，确认归档路径包含 `archive/main/`
2. 切换到 `feature/login` 分支执行，确认归档路径包含 `archive/feature-login/`
3. 在非 git 目录执行，确认归档路径为 `archive/req-xx-{title}/`（无子目录）
4. 显式传入 `--folder release` 时，确认归档路径为 `archive/release/req-xx-{title}/`

## 注意事项
1. `subprocess.run` 必须设置 `cwd=str(root)` 以确保在正确的仓库目录执行
2. `timeout=5` 防止 git 命令挂起（如网络 mount 场景）
3. `capture_output=True` 避免输出污染 harness 的 stdout
4. branch 名为空字符串（如 detached HEAD 状态）时与非 git 仓库同样降级
5. `/` → `-` 的替换应在 `result.stdout.strip()` 之后执行，避免处理空字符串
