# Plan: chg-01

## Steps

1. 读取 `core.py` 中的 `archive_requirement` 函数
2. 在函数末尾（归档成功后）新增 Git 检测逻辑：
   - 调用 `subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root, capture_output=True, text=True)`
   - 若返回 "true"，则通过 `input()` 询问用户 `Auto-commit archive changes? [y/N]: `
3. 用户输入 `y` 或 `yes` 后：
   - 执行 `git add -A`
   - 执行 `git commit -m "archive: {req_name}"`
   - 询问 `Push to remote? [y/N]: `，确认后执行 `git push`
4. 处理 `EOFError`（非交互环境）等边界情况
5. 本地语法检查

## Artifacts

- 更新后的 `src/harness_workflow/core.py`
