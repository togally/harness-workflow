# Session Memory — chg-05（done 交付总结扩效率与成本段）

## 1. Current Goal

在 `done.md` 交付总结最小字段模板后追加 §效率与成本段（四子字段），SOP Step 6 加聚合逻辑陈述，同步 scaffold_v2 mirror，新增 pytest 三用例。

## 2. Current Status

**已完成（2026-04-24）**：

- `done.md` 最小字段模板追加 `## 效率与成本` 段，含四子字段（总耗时 / 总 token / 各阶段耗时分布 / 各阶段 token 分布），字段顺序固定，"禁止编造"注释落盘。
- `done.md` SOP Step 6 追加 Step 6.x 聚合子步骤：读 `.workflow/flow/requirements/{req-id}-{slug}/usage-log.yaml` + req yaml `stage_timestamps` → 聚合 → 写入交付总结；缺数据降级 `⚠️ 无数据`。
- scaffold_v2 mirror 同步，`diff -q` 输出零行。
- `src/harness_workflow/workflow_helpers.py` 新增 `done_efficiency_aggregate(root, req_id, slug) -> dict` helper，聚合 usage-log + stage_timestamps → 返回四子字段数据。
- `tests/test_done_subagent.py` 新增 13 个 pytest 用例，全部 PASS：
  - `TestDoneDeliverySummaryEfficiencySection`（4 用例）：有数据路径
  - `TestDoneDeliverySummaryEmptyUsageLog`（3 用例）：空/缺 usage-log → ⚠️ 无数据
  - `TestDoneDeliverySummaryFieldOrderFixed`（6 用例）：字段顺序 + mirror diff 归零

## 3. Validated Approaches

- `done_efficiency_aggregate` 在 tempdir fixture 中直接写真实格式 YAML，避免依赖 `record_subagent_usage` 实际写入路径（当前写 state/sessions/，flow/ 路径为 chg-06（harness-manager Step 4 派发硬门禁）后期接入），做到与 chg-06（harness-manager Step 4 派发硬门禁）无时序耦合。
- `_NO_DATA = "⚠️ 无数据"` 全局常量，空列表、空文件、缺失文件三种情况均正确降级。
- 四子字段顺序通过 `awk` 行号验证 + pytest `test_field_order_fixed` 双重保护。

## 4. Failed Paths

无。

## 5. Candidate Lessons

```markdown
### 2026-04-24 done 聚合 helper 与采集链路解耦
- Symptom: done.md 规定读 flow/requirements/usage-log.yaml，但 record_subagent_usage 当前写 state/sessions/
- Cause: chg-06 尚未接入真实派发链路；chg-05 不等 chg-06
- Fix: pytest fixture 手动写真实格式 YAML 到 flow/ 路径，done_efficiency_aggregate 直接读 flow/；与 chg-06 无耦合
```

## 6. Next Steps

- chg-05 DONE，等 chg-06（harness-manager Step 4 硬门禁）完成后，chg-07（dogfood 活证）可启动
- dogfood 时 done subagent 调用 `done_efficiency_aggregate` 从真实 usage-log 聚合写入交付总结

## 7. Open Questions

无。

---

本阶段已结束。
