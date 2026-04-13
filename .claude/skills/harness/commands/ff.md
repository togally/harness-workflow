# harness ff

## 前置条件
- 当前 stage 是 `requirement_review` 或 `planning`

## 作用
跳过讨论门禁，快进到执行确认门。

## 执行步骤
1. 将 stage 推进到 `planning`（如当前在 requirement_review）
2. 再推进到执行确认门（`ready_for_execution` 等待确认）
3. 展示变更列表和执行顺序，等待用户运行 `harness next --execute` 确认

## 注意
- ff 跳过讨论，不跳过最终执行确认
- 适用于用户已充分了解需求，不需要逐步讨论的场景
