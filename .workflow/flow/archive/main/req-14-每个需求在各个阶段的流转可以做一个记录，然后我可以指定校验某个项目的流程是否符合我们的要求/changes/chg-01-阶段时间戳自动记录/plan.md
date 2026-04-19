# Plan: chg-01

## Steps

1. 读取 `core.py` 中 `workflow_next` 函数
2. 找到更新 requirement state YAML 的代码段（在 `next_stage == "done"` 附近）
3. 将 `stage_timestamps` 的记录逻辑从仅 `done` 阶段扩展到所有阶段切换
4. 在保存 state 前确保 `stage_timestamps` 存在并写入 `stage_timestamps[next_stage] = datetime.now(timezone.utc).isoformat()`
5. 语法检查与本地验证

## Artifacts

- 更新后的 `src/harness_workflow/core.py`
