# Plan: 补充测试覆盖

## 执行步骤

1. 阅读 `tests/test_cli.py` 中现有的 `test_install_*` 和 `test_update_*` 测试，了解测试基类和辅助方法（如 `run_cli`、`self.repo` 临时目录）。
2. 新增测试 `test_install_scaffolds_tools_directory`：
   - 在临时仓库运行 `harness install`
   - 断言 `.workflow/tools/index.md`、`.workflow/tools/stage-tools.md` 等文件存在
3. 新增测试 `test_update_does_not_archive_tools_directory`：
   - 在临时仓库运行 `harness install`
   - 确认 `.workflow/tools/` 存在
   - 运行 `harness update`
   - 断言 `.workflow/tools/` 仍然存在，且 `.workflow/context/backup/legacy-cleanup/.workflow/tools/` 未被创建（或 update 输出中未包含 tools 相关清理动作）
4. 运行 `pytest tests/test_cli.py -v`，确认所有测试通过。
5. （执行时需确认）若测试基类中有 teardown 逻辑或特殊的 mock，需适配新测试以保持一致。

## 预期产物

- 修改后的 `tests/test_cli.py`
- `pytest` 全绿输出

## 依赖关系

- **前置依赖**：
  - chg-01 必须完成（update 不再误清理）
  - chg-02 必须完成（install/init 能正确创建 tools）
- **无后置依赖**：本变更为 req-20 的最后一个变更。
