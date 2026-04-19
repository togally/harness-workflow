# Plan: chg-01

## Steps

1. 读取 `core.py` 中 `validate_requirement` 函数
2. 在 artifact 检查之后、返回之前插入编译检查逻辑
3. 遍历 `root.rglob("*.py")`，跳过 `__pycache__` 和 `.venv` 等目录
4. 对每个文件调用 `py_compile.compile(file, doraise=True)`
5. 捕获 `PyCompileError`，记录文件路径和错误信息
6. 汇总打印，若存在错误则返回非 0 退出码
7. 语法检查

## Artifacts

- 更新后的 `src/harness_workflow/core.py`
