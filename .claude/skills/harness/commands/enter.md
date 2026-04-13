# harness enter

## 前置条件
- 有 current_requirement

## 执行步骤
1. 读 `state/runtime.yaml` 确认 current_requirement 和 stage
2. 更新 `state/runtime.yaml`：
   - `conversation_mode: harness`
   - `locked_requirement: {current_requirement}`
   - `locked_stage: {current_stage}`
3. 输出：已进入 harness 模式，锁定到 {req-id} / {stage}

## 锁定效果
- 对话期间只能在 locked_requirement + locked_stage 范围内工作
- before-reply hook 会检查每次回复是否在锁定范围内
- 只有 `harness exit` 才能解除锁定
