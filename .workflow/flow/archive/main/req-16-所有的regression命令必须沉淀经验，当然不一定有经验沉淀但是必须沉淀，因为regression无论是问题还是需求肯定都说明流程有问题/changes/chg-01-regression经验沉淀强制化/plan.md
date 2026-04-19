# Plan: chg-01

## Steps

1. 读取 `core.py` 中 `regression_action` 函数
2. 在 `archive_requirement` 和 `workflow_status` 之间的合适位置新增 `_ensure_regression_experience(root: Path, regression_id: str) -> None`
3. 函数逻辑：
   - 构建路径 `root / ".workflow" / "context" / "experience" / "regression" / f"{regression_id}.md"`
   - 若文件已存在，直接返回
   - 若不存在，创建目录，写入模板（包含标题、日期、现象、根因、改进措施等占位）
   - 打印提示信息
4. 修改 `regression_action`：
   - `cancel` / `reject` 分支：先调用 `_ensure_regression_experience`，再清除 regression
   - `confirm` 分支：先调用 `_ensure_regression_experience`，再清除 regression，打印确认信息
   - `change_title` 分支：先调用 `_ensure_regression_experience`，再清除并创建 change
   - `requirement_title` 分支：先调用 `_ensure_regression_experience`，再清除并创建 requirement
   - `to_testing` 分支：先调用 `_ensure_regression_experience`，再清除并回退 stage
5. 语法检查

## Artifacts

- 更新后的 `src/harness_workflow/core.py`
