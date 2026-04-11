# 主动 Context-Maintenance 检查

## 目的

在每次回复前主动检查 session 上下文状态，防止上下文累积过高导致性能下降。

## 触发条件

### 1. 轮次触发
- 条件：`conversation_turns % turn_threshold == 0`
- 默认阈值：10 轮
- 可在 workflow-runtime.yaml 中配置 `context_maintenance.turn_threshold`

### 2. 文件数触发
- 条件：`files_read > file_threshold`
- 默认阈值：15 个文件
- 可在 workflow-runtime.yaml 中配置 `context_maintenance.file_threshold`

### 3. 阶段切换强制触发
- 条件：检测到 `harness next` 命令
- 优先级：最高，无论是否满足其他条件都强制触发

## 检查逻辑

```yaml
# 在每次 before-reply 时执行：
1. 读取当前 session-memory.md
2. 检查 Session State Tracking 区域
3. 判断是否满足任一触发条件：
   - conversation_turns >= turn_threshold
   - files_read >= file_threshold
   - 检测到阶段切换命令
4. 如果满足条件：
   - 根据触发类型提供维护建议
   - 提醒用户执行 /clear 或 /compact
   - 等待用户确认
5. 更新 session-memory.md 中的计数器
```

## 维护建议模板

### 轮次过高建议
```
⚠️ 上下文维护提醒

检测到当前 session 已进行 {conversation_turns} 轮对话，建议执行上下文压缩：

- 使用 /compact 压缩仍相关的历史上下文
- 或使用 /clear 清理不相关的历史上下文

这样可以保持回复性能并避免潜在的上下文截断。
```

### 文件数过高建议
```
⚠️ 上下文维护提醒

检测到当前 session 已读取 {files_read} 个文件，建议执行上下文清理：

- 使用 /clear 清理不再需要的文件内容
- 保留当前工作相关的关键文件

这样可以减少 token 消耗并提升响应速度。
```

### 阶段切换建议
```
⚠️ 阶段切换前维护提醒

即将切换到下一个工作流阶段，建议清理上一阶段的上下文：

- 使用 /clear 清理上一阶段的临时文件和讨论
- 保留当前版本和工件的引用

这样可以确保新阶段从干净的上下文开始。
```

## 实施要求

### Agent 执行步骤

1. **读取状态**：
   ```
   读取当前变更或版本的 session-memory.md
   查找 Session State Tracking 区域
   如果不存在，使用默认值：conversation_turns=0, files_read=0
   ```

2. **检查触发**：
   ```
   从 workflow-runtime.yaml 读取阈值配置（如果存在）
   默认：turn_threshold=10, file_threshold=15
   检查是否满足任一触发条件
   ```

3. **提供建议**：
   ```
   如果满足条件，根据触发类型显示相应建议
   不要自动执行清理操作，等待用户确认
   ```

4. **更新状态**：
   ```
   递增 conversation_turns 计数器
   如果使用了 Read/Glob/Grep 工具，递增 files_read 计数器
   更新 session-memory.md
   ```

### 状态追踪格式

在 session-memory.md 中添加：

```markdown
## Session State Tracking

### Conversation Turns
- Current: {当前轮次}
- Last Maintenance: {上次维护时的轮次}
- Threshold: {阈值}

### Files Read
- Current: {当前已读文件数}
- Last Maintenance: {上次维护时的文件数}
- Threshold: {阈值}
```

## 配置示例

在 workflow-runtime.yaml 中添加：

```yaml
context_maintenance:
  turn_threshold: 10      # 每 10 轮对话触发一次检查
  file_threshold: 15      # 读取 15 个文件后触发检查
  auto_suggest: true      # 自动显示建议（默认 true）
```

## 注意事项

1. **不自动清理**：此 hook 只提供建议，不自动执行清理操作
2. **避免频繁提醒**：同一个触发条件在一次 session 中最多提醒一次
3. **保持向后兼容**：如果 session-memory.md 没有状态追踪区域，使用默认值
4. **性能考虑**：只在 before-reply 时检查，不增加工具调用的开销

## 相关文件

- `workflow/templates/session-memory.md` - session-memory 模板
- `workflow/context/rules/workflow-runtime.yaml` - 配置文件
- `workflow/context/hooks/README.md` - Hook 索引
