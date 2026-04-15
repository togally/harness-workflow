# Testing Report

## Scope

验证 req-20 实现的经验索引与阶段沉淀机制：
1. `harness update` 能自动生成/刷新 `.workflow/context/experience/index.md`
2. `tests/test_cli.py` 全部通过，无回归
3. `testing.md` 已填充 req-19 的测试修复经验
4. regression 关闭时提示同步到 testing/acceptance experience

## Test Results

- `python3 -m pytest tests/test_cli.py -v`：15 passed, 36 skipped（无失败）
- `python3 -m py_compile src/harness_workflow/core.py`：Syntax OK
- `harness update`：成功生成 `Refreshed experience index: .workflow/context/experience/index.md`
- 经验索引内容正确：按 risk/stage/tool 分组列出所有经验文件

## Regression Check

- req-19 的测试修复未受影响
- archive、ff、next、regression 等核心命令行为正常

## Conclusion

测试通过，可以进入验收阶段。
