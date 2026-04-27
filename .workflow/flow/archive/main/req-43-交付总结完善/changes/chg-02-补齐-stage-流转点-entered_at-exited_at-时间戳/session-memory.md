# Session Memory — chg-02（补齐 stage 流转点 entered_at + exited_at 时间戳）

## executing stage ✅

### 实现摘要

- `_sync_stage_to_state_yaml` 加 `prev_stage: str | None = None` kw-only 参数。
- 写 new_stage.entered_at 时同时写 `{prev_stage}_exited_at = now_ts`（D-4 同级键，非嵌套字典）。
- `if new_stage not in existing` 保护：不覆盖已存在的 entered_at（幂等）。
- 新增 `_STAGE_ORDER` 常量列表。
- 新增 `_backfill_done_timestamps(state)` helper：归档前扫 stage_timestamps，若 done.entered_at 缺失补当前时间 + 写 prev_stage_exited_at。
- `archive_requirement` 在保存前调 `_backfill_done_timestamps(state)`。
- scaffold_v2 mirror：无（纯 CLI 源码，不进 scaffold，符合 plan 预期）。

### 测试结果

- 新增测试文件：`tests/test_req43_chg02.py`（7 条）
- 全部通过：7/7 ✅
- 关键覆盖：前向流转、跳跃流转、prev_stage=None 向后兼容、不覆盖已有 entered_at、backfill done、backfill exited_at、无 stage_timestamps 安全

### 遇到的问题 / 解法

- 无阻塞问题。schema 升级选 D-4（同级键）保持历史 req yaml 向后兼容。
