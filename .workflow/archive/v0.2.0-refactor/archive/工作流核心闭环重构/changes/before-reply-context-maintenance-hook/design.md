# Change Design

## 1. Problem

当前 harness 工作流中，context-maintenance 的触发机制完全依赖被动和主观判断：
- Agent 需要主观判断"上下文可能失真"时才触发
- 没有自动的轮次计数或文件数检查
- 用户需要手动执行 `/clear` 或 `/compact`

这导致长期 session 中上下文持续累积，造成：
- Token 浪费和成本增加
- 回复速度变慢
- 潜在的上下文截断风险
- 用户体验下降

## 2. Approach

### 2.1 整体架构

在 `workflow/context/hooks/before-reply/` 目录下新增主动触发 hook 文件：
- `10-context-maintenance-check.md` - 主动检查 hook

### 2.2 触发机制设计

#### 2.2.1 轮次触发

**实现方式**：
- 在 session-memory.md 中维护 `conversation_turns` 计数器
- 每次 before-reply 时递增计数器
- 当 `conversation_turns % 10 == 0` 时触发检查

**配置参数**：
- 默认阈值：10 轮
- 可在 workflow-runtime.yaml 中配置 `context_maintenance.turn_threshold`

#### 2.2.2 文件数触发

**实现方式**：
- 在 session-memory.md 中维护 `files_read` 计数器
- 每次 Read/Glob/Grep 工具调用时递增计数器
- 当 `files_read > 15` 时触发检查

**配置参数**：
- 默认阈值：15 个文件
- 可在 workflow-runtime.yaml 中配置 `context_maintenance.file_threshold`

#### 2.2.3 阶段切换强制触发

**实现方式**：
- 在 `before-reply/15-stage-transition-check.md` hook 中添加强制检查
- 检测到 `harness next` 命令时，无论是否满足其他条件都强制触发

### 2.3 Session 状态追踪

在 session-memory.md 中新增状态追踪区域：

```markdown
## Session State Tracking

### Conversation Turns
- Current: 0
- Last Maintenance: 0
- Threshold: 10

### Files Read
- Current: 0
- Last Maintenance: 0
- Threshold: 15
```

### 2.4 触发后的行为

当触发条件满足时，hook 应该：

1. **检查是否需要维护**：比较当前状态与上次维护时的状态
2. **提供维护建议**：
   - 如果轮次过高：建议 `/compact` 压缩上下文
   - 如果文件数过高：建议 `/clear` 清理不相关的历史上下文
   - 如果阶段切换：建议清理上一阶段的临时文件和上下文
3. **等待用户确认**：不自动执行清理操作，由用户决定

### 2.5 Hook 集成

在 `workflow/context/hooks/README.md` 中更新 before-reply 阶段的 hook 加载顺序：

```
before-reply/:
  10-context-maintenance-check.md    # 新增：主动上下文维护检查
  20-conversation-lock-check.md      # 现有：对话锁检查
  30-workflow-drift-check.md         # 现有：工作流漂移检查
  40-stage-boundary-check.md         # 现有：阶段边界检查
```

## 3. Risks

### 3.1 实现风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Session 状态追踪可能不准确 | 检查失效 | 在关键操作点（如工具调用）确保状态更新 |
| 频繁的检查可能影响性能 | 回复变慢 | 限制检查频率，仅在 before-reply 时检查 |
| 阈值设置可能不适合所有场景 | 用户体验差 | 提供可配置的阈值参数 |
| 用户可能忽略维护建议 | 问题仍然存在 | 在关键节点（如阶段切换）强制提醒 |

### 3.2 权衡

- **自动清理 vs 主动提醒**：选择主动提醒而非自动清理，避免意外删除重要上下文
- **单一阈值 vs 多条件**：使用多条件触发，覆盖不同场景
- **硬编码 vs 可配置**：提供默认值同时支持配置，平衡易用性和灵活性

### 3.3 兼容性

- 不影响现有 hook 的功能
- 不修改 workflow-runtime.yaml 的核心结构
- 保持向后兼容，没有 session 状态追踪时仍能正常工作
