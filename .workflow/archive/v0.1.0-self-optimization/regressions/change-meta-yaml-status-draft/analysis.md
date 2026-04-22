# Regression Analysis

## 1. Problem Assessment

**真实设计缺陷**。不是使用误解，不是预期偏差。

## 2. Evidence

- `core.py` L21: `WORKFLOW_RUNTIME_PATH` 指向版本级路径，版本状态由 `apply_stage_transition` 维护
- `apply_stage_transition` 只写版本 `meta.yaml` 中的 `stage`/`status`，从不写入 change 目录下的 `meta.yaml`
- `update_item_meta` 仅在 regression `--confirm/--reject/--cancel/--change` 时调用，从不用于 change 状态更新
- change `meta.yaml` 模板 `status: "draft"` 是初始值，也是终态——工具从未更改它
- `version-memory.md` 手动记录了所有 7 个 change 已完成（✅），但工具层面无对应状态

## 3. Discussion Outcome

用户确认这是真实问题，希望通过工具自动维护 change/requirement 的生命周期状态。

## 4. Recommended Action

确认为真实问题，转为新 change：**"修复 change/requirement meta.yaml status 生命周期追踪"**

修复范围：
1. `harness next --execute` 进入 executing 时，将当前 change `status` 更新为 `in_progress`
2. `harness next`（从 executing → done）时，将所有 change `status` 更新为 `done`
3. `harness requirement` 创建时保持 `draft`；随版本推进同步更新
4. `harness status` 输出应同时显示版本级状态和各 change 的真实状态
