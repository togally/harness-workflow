# Session Memory

## Session State Tracking

> 此区域由 before-reply 阶段的 context-maintenance hook 自动维护
> 用于追踪 session 状态，防止上下文累积过高

### Conversation Turns
- Current: 3
- Last Maintenance: 0
- Threshold: 10

### Files Read
- Current: 8
- Last Maintenance: 0
- Threshold: 15

---

## 1. Current Goal

为 before-reply 阶段添加主动的 context-maintenance 触发机制，解决 session 上下文累积过高的问题。

## 2. Current Status

- ✅ 回归问题已确认：context-maintenance 缺乏主动触发机制
- ✅ 已创建变更工作空间
- ✅ 已填充 change.md、design.md、plan.md、acceptance.md
- ✅ 已创建主动检查 hook 文件
- ✅ 已更新 session-memory.md 模板
- ✅ 已更新 hook README 文档
- ✅ 已更新当前变更的 session-memory.md
- ✅ 已更新 workflow-runtime.yaml 配置
- ✅ 已验证文件完整性
- ✅ 已执行验收测试
- ✅ 变更已标记为 completed

## 3. Validated Approaches

- 使用 `harness regression --confirm` 确认问题真实性
- 使用 `harness regression --change` 将回归转换为正式变更
- 根据 regression.md 中的问题描述和解决方案设计变更

## 4. Failed Paths

- Attempt: 依赖用户手动执行 `/clear` 和 `/compact`
- Failure reason: 用户可能忘记执行，导致上下文持续累积
- Reminder: 不要依赖用户的主动性，必须提供自动触发机制

## 5. Candidate Lessons

```markdown
### [2026-04-11] Context-maintenance 需要主动触发
- Symptom: Session 上下文持续累积，导致 token 浪费、回复变慢
- Cause: 现有 hook 触发条件全部是被动/主观的，缺乏自动检查机制
- Fix: 在 before-reply 阶段添加基于轮次、文件数、阶段切换的主动触发机制
```

## 6. Next Steps

1. ✅ 验证文件完整性 - 已完成
2. ✅ 执行验收测试 - 已完成
3. ✅ 更新变更状态为 completed - 已完成
4. ⏳ 考虑将经验捕获到 workflow/context/experience/ - 待后续处理

## 7. Open Questions

- 具体的触发阈值（轮次数、文件数）是否需要可配置？
- 触发后是否需要自动清理，还是仅提醒用户？
- 如何追踪 session 的轮次和已读文件数？
