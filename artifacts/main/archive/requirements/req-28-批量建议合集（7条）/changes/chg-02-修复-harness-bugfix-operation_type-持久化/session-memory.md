# Session Memory

## 1. Current Goal

- 修复 `harness bugfix` / `harness next` 闭环：让 `operation_type` / `operation_target` 在 runtime.yaml 中持久化，覆盖 AC-12；同时通过懒回填兼容历史 bugfix-3/4/5/6 runtime 缺字段的情况。

## 2. Current Status

- [x] Step 1：审计 runtime.yaml 读写路径，确认 `save_requirement_runtime` 是唯一权威入口，无旁路直写。
- [x] Step 2：扩展 `save_requirement_runtime.ordered_keys`，加入 `operation_type` / `operation_target` / `stage_entered_at`，避免 save 按白名单裁剪。
- [x] Step 2 补充：在 `load_requirement_runtime` 加懒回填（`current_requirement` 前缀 → operation_type），显式值保留。
- [x] Step 3：确认 `create_bugfix`（workflow_helpers.py:3375-3376）已写 operation_type / operation_target；本 change 的 ordered_keys 修复让其真正落盘。
- [x] Step 4：`workflow_next` / `workflow_fast_forward` 既有逻辑（4636 / 4684 行）已调用 `_sync_stage_to_state_yaml`，operation_type 持久化后 bugfix 路径自动走通。
- [x] Step 5：采用懒回填策略代替独立 `scripts/backfill_bugfix_runtime.py`，更简单且对历史数据零侵入。
- [x] Step 6：新增 `tests/test_bugfix_runtime.py`，4/4 全过。
- [x] 对人文档 `实施说明.md` 已产出。

## 3. Validated Approaches

- `python3 -m unittest tests.test_bugfix_runtime -v` → 4/4 pass。
- `python3 -m unittest discover tests` → 93 tests, OK (skipped=36)。既有 `test_next_writeback.py` 的 bugfix 同步测试也继续绿。
- `save_simple_yaml` 在传入 `ordered_keys` 时只遍历列表中的 key，不在列表里的字段直接被丢弃——这是本次核心 bug 的机制。

## 4. Failed Paths

- Attempt: 曾考虑在 `save_requirement_runtime` 里不传 `ordered_keys`，让所有字段透传。
- Failure reason: 会破坏现有 yaml 字段顺序的确定性，影响 diff 可读性与向后兼容。
- Reminder: 保留 `ordered_keys` 列表，按需扩展白名单更稳。

## 5. Candidate Lessons

```markdown
### 2026-04-19 runtime.yaml 白名单裁剪是 bugfix 闭环断链根因
- Symptom: `harness bugfix` 创建后 runtime.yaml 缺 `operation_type`，`harness next` 报 `Unknown stage: regression`。
- Cause: `save_simple_yaml` 在传 `ordered_keys` 时只按列表遍历，未列入的字段被无声丢弃；`create_bugfix` 写的字段首次 save 即丢。
- Fix: 把 `operation_type`/`operation_target`/`stage_entered_at` 加入白名单；`load` 层增加懒回填防御历史数据。
```

## 6. Next Steps

- 交接给 chg-03（bugfix sweep）：现在新 bugfix 的 yaml stage 可以被 `workflow_next` 正确同步回写；历史 bugfix-6 的 runtime.yaml 即使已丢失 operation_type，下次 `load_requirement_runtime` 会自动从 `current_requirement="bugfix-6"` 推断回来。chg-03 只需处理 bugfix-3/4/5 的 force-done 归档即可，无需自己补 operation_type edge case。

## 7. Open Questions

- 未来若新增 `operation_type`（如 `experiment`），需同步扩展懒回填的 id 前缀映射。
