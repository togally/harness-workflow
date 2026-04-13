# harness exit

## 前置条件
- conversation_mode 是 `harness`

## 执行步骤
1. 更新 `state/runtime.yaml`：
   - `conversation_mode: open`
   - `locked_requirement: ""`
   - `locked_stage: ""`
2. 输出：已退出 harness 模式，对话解锁

## 注意
- 退出不改变 current_requirement 和 stage
- 不触发任何状态推进
