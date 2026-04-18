# Session Memory

## 变更：chg-04-补充测试覆盖

- [x] 步骤1：阅读 `tests/test_cli.py` 中的 `test_install_*` 和 `test_update_*` 测试
- [x] 步骤2：新增 `test_install_scaffolds_tools_directory`：运行 `harness install` 后断言 `.workflow/tools/index.md`、`.workflow/tools/catalog/agent.md`、`.workflow/tools/stage-tools.md` 存在
- [x] 步骤3：新增 `test_update_does_not_archive_tools_directory`：运行 `harness update` 后断言 `.workflow/tools/` 仍存在且 `index.md` 未被归档
- [x] 步骤4：运行 `pytest tests/test_cli.py -v`，17 passed, 36 skipped，全部通过

## 关键决策
- 测试直接使用 `PYTHONPATH=src python3 -m pytest` 运行，无需额外重装包
- `test_update_does_not_archive_tools_directory` 在 install 后先断言 tools 存在，再 update，再断言仍存在，覆盖误清理修复效果

## 遇到的问题
- 无

## 测试通过情况
- 全部通过（17 passed, 36 skipped）
