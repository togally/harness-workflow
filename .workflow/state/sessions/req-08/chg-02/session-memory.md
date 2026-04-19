# Session Memory: chg-02

## Change
harness update 增加 state 文件格式自动迁移

## Status
✅ 已完成

## Steps
- [x] 在 `core.py` 中新增 `_migrate_state_files(root)` 函数
- [x] 实现 `runtime.yaml` 的 `ff_mode` / `ff_stage_history` 自动补齐（含 `.bak` 备份）
- [x] 实现 `requirements/*.yaml` 的旧字段自动迁移：`req_id`→`id`、`created`→`created_at`、`completed`→`completed_at`，补充 `started_at` / `stage_timestamps`
- [x] 在 `update_repo` 末尾调用迁移函数
- [x] 修复 `core.py` 中多处 `state.get("req_id")` 为 `_get_req_id(state)`，兼容新旧字段
- [x] 临时目录测试验证通过

## Internal Test
- [x] `harness update` 能把旧格式 `runtime.yaml` 升级为新格式 ✅
- [x] `harness update` 能把旧格式 `requirements/*.yaml` 升级为新格式 ✅
- [x] 升级前生成 `.bak` 备份 ✅
