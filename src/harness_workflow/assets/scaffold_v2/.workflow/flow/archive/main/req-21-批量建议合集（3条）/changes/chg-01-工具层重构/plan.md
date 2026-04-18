# Plan: chg-01

## Steps

1. 创建 `base-role.md` 并修改 `.workflow/context/index.md` 加载顺序
2. 在 `core.py` 中实现 `search_tools`、`rate_tool`、`log_action`
3. 在 `cli.py` 中注册 `tool-search` 和 `tool-rate` 子命令
4. 创建 `keywords.yaml`、`ratings.yaml`、`missing-log.yaml`
5. 编写并运行 `tests/test_cli.py` 集成测试
6. 注册变更文档

## Artifacts

- `.workflow/context/roles/base-role.md`
- `.workflow/context/index.md`
- `src/harness_workflow/core.py`
- `src/harness_workflow/cli.py`
- `.workflow/tools/index/keywords.yaml`
- `.workflow/tools/index/missing-log.yaml`
- `.workflow/tools/ratings.yaml`
- `tests/test_cli.py`

## Dependencies

无外部依赖
