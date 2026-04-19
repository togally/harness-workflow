# Plan: chg-02

## Steps

1. 在 `core.py` 中新增 `validate_requirement(root: Path) -> int` 函数
2. 函数逻辑：
   - 读取 runtime 获取 `current_requirement`
   - 定位到 `.workflow/flow/requirements/{req_dir}/changes/`
   - 遍历每个 change 子目录
   - 检查是否存在 `testing-report.md` 和 `acceptance-report.md`
   - 汇总并打印缺失项
3. 在 `cli.py` 中新增 `validate` 子命令并绑定到 `validate_requirement`
4. 本地运行 `harness validate` 验证输出

## Artifacts

- 更新后的 `src/harness_workflow/core.py`
- 更新后的 `src/harness_workflow/cli.py`
