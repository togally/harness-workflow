# Session Memory — chg-03（per-stage 合并到 stage × role × model 单表渲染）

## executing stage ✅

### 实现摘要

- `done_efficiency_aggregate` 新增 `task_type: str = "req"` 参数；bugfix/sug 路径从 sessions 目录读 usage-log。
- 新增 `stage_role_map` dict keyed on `(stage, role, model)`；返回 `stage_role_rows: list[dict]`（9 字段：stage/role/model/input_tokens/output_tokens/cache_read_input_tokens/cache_creation_input_tokens/total_tokens/tool_uses）。
- `pure_stage_ts` 过滤修复：排除 `*_exited_at` 键，只保留真正的 entered_at 时间戳。
- 保留 `role_tokens` / `stage_durations` 向后兼容字段（不动旧用途）。
- `done.md` 模板：删「各阶段耗时分布」+「各阶段 token 分布」两表，新增单表「各阶段切片（stage × role × model × token × tool_uses）」；Step 6.x 说明文字同步更新。
- scaffold_v2 mirror 同步：done.md（diff = 0）。

### 测试结果

- 新增测试文件：`tests/test_req43_chg03.py`（8 条）
- 全部通过：8/8 ✅
- 关键覆盖：完整 rows、stage 缺失、entries 为空、多 role、累积聚合、legacy 兼容、done.md 模板、mirror

### 遇到的问题 / 解法

- `test_done_subagent.py::TestDoneDeliverySummaryFieldOrderFixed` 原断言「各阶段耗时分布」/「各阶段 token 分布」与新单表格式不符，需同步更新测试契约。
  - 修复：将断言更新为 `### 各阶段切片`（三段式替代四段式），逻辑等价，契约与 done.md 一致。

### 候选教训

- `pure_stage_ts` 过滤：`*_exited_at` 键需排除，否则会被误当 entered_at 时间戳处理。
