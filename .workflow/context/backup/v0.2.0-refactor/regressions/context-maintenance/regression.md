# Regression Intake

## 1. Issue Title

上下文累积过高：context-maintenance 缺乏主动触发机制

## 2. Reported Concern

在实际使用中，session 的上下文会越来越高，单靠 `/clear` 和 `/compact` 无法根本解决问题。

## 3. Current Behavior

- **复现路径**：开启一个 harness session → session-start 读取 8+ 个文件 → 执行期间持续读取代码/模板 → 经过 10+ 轮对话后上下文显著增大
- **实际表现**：
  - `context-maintenance` hook 的触发条件全部是被动/主观的（"after entering a new node"、"when accumulated context may distort"）
  - `before-reply` 的 3 个 hook 只检查对话锁、workflow drift、阶段边界，无任何上下文大小检查
  - Agent 没有周期性/阈值型自动检查机制，只能等用户发现"卡了"才清理
- **影响**：context 积压导致 token 浪费、回复变慢、潜在截断风险

## 4. Expected Outcome

`before-reply` 应有主动的上下文检查 hook，按以下条件触发 context-maintenance：
1. **轮次触发**：每 8-10 轮对话执行一次检查
2. **文件数触发**：本 session 已读文件数 > 15 时触发
3. **阶段切换强制**：`harness next` 之前强制触发

## 5. Next Step

确认为真实设计缺口，转为新 change：**"before-reply 新增主动 context-maintenance 触发 hook"**
