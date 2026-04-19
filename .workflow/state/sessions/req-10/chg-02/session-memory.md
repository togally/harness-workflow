# Session Memory: chg-02

## Change
CLI 命令实现

## Status
✅ 已完成

## Steps
- [x] 在 `cli.py` 中新增 `suggest` 子命令解析（`--list`, `--apply`, `--delete`, content positional）
- [x] 在 `core.py` 中实现 `create_suggestion`、`list_suggestions`、`apply_suggestion`、`delete_suggestion`
- [x] 在 `COMMAND_DEFINITIONS` 中注册 `harness-suggest`
- [x] 修复 `apply_suggestion` 更新 status 时保留 body 的问题
- [x] 顺便修复 `create_requirement` 中 state yaml 使用旧字段的问题，改为新规范字段
- [x] 修复 `core.py` 中多处 `state.get("req_id")` 为 `_get_req_id(state)`，兼容新旧双字段

## Internal Test
- [x] `harness suggest "xxx"` 能创建文件 ✅
- [x] `harness suggest --list` 能正确显示 ✅
- [x] `harness suggest --apply sug-01` 能创建需求并标记 applied ✅
- [x] `harness suggest --delete sug-01` 能删除文件 ✅
