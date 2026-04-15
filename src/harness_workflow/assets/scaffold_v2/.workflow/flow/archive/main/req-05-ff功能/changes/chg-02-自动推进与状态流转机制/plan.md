# Plan: chg-02

## Steps

1. 读取当前 `runtime.yaml` 和 `.workflow/state/` 目录结构
2. 设计 ff 模式状态字段：
   - 在 `runtime.yaml` 中增加 `ff_mode: boolean`
   - 增加 `ff_stage_history: []` 可选字段，记录 ff 模式下经过的 stage（用于调试和审计）
3. 定义 ff 模式的启动方式：
   - 用户在 `requirement_review` 或 `planning` 阶段执行 `harness ff` → `runtime.yaml` 标记 `ff_mode: true`
   - 一旦启动，后续 stage 推进由主 agent 自动完成
4. 定义主 agent 在 ff 模式下的自动推进逻辑：
   - 当前 stage 的 subagent 任务完成且验收条件满足后，主 agent 自动更新 `runtime.yaml` 到下一 stage
   - 不需要等待用户输入 `harness next`
   - 但需要在每次推进前保存关键状态到 session-memory
5. 定义 session-memory 在 ff 模式下的保存规范：
   - 每个 stage 结束时必须更新 `session-memory.md`
   - 包含：stage 结果摘要、关键决策、遇到的问题、下一步任务
6. 定义 ff 模式的暂停/退出机制：
   - 遇到需要用户输入的情况时，将 `ff_mode` 设为 `paused`，等用户回复后再恢复
   - 用户可以随时说 "停止 ff" 来退出 ff 模式（转为正常模式）
7. 更新 `runtime.yaml` 示例或相关文档
8. 检查与现有 `state/` 结构的兼容性

## Artifacts

- 更新后的 `.workflow/state/runtime.yaml`（结构和示例）
- `.workflow/flow/stages.md` 中 ff 推进规则的补充（与 chg-01 协调）

## Dependencies

- 依赖 chg-01 的语义设计（完成判定规则）
