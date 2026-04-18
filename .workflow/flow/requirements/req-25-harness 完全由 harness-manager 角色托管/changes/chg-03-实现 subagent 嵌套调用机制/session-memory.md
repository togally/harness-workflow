# Session Memory

## 1. Current Goal

实现 subagent 嵌套调用机制：定义启动协议、实现无限层级嵌套能力、建立上下文传递机制。

## 2. Current Status

### Completed

- [x] 创建 `design.md` 定义嵌套调用机制
- [x] 更新 `harness-manager.md` 添加 Step 3.6 派发 Subagent
- [x] 更新 `base-role.md` 添加 Subagent 嵌套调用规则
- [x] 定义 context_chain 结构
- [x] 定义 session-memory.md 格式
- [x] 定义派发 prompt 模板

### Pending

- [ ] 验证 harness-manager 能启动 stage 角色 subagent
- [ ] 验证 subagent 能启动其他 subagent（任意层级）
- [ ] 验证上下文能正确传递
- [ ] 验证能正常完成五层以上嵌套调用
- [ ] 验证上层调用下层无限制

## 3. Validated Approaches

### Subagent 嵌套调用协议

1. **context_chain**：追踪完整调用链路，Level 0 为主 agent，Level 1+ 为 subagent
2. **Session Memory**：每个 subagent 维护独立的 session-memory.md
3. **上下文隔离**：subagent 只写入自己的 session-memory.md，不修改上层文档
4. **无限深度**：上层可以无限调用下层，无代码深度限制

### 实现文件

1. `design.md`：详细描述嵌套调用机制
2. `harness-manager.md` Step 3.6：派发 Subagent 协议
3. `base-role.md`：Subagent 嵌套调用规则

## 4. Failed Paths

- 无

## 5. Candidate Lessons

```markdown
### 2026-04-18 Subagent 嵌套调用设计

- Symptom: 需要实现上层无限调用下层的能力
- Cause: 传统 subagent 模式只有一层派发
- Fix: 通过 context_chain 追踪调用链，通过 session-memory.md 隔离上下文，实现无限层级嵌套
```

## 6. Next Steps

1. 实际测试 subagent 嵌套调用功能
2. 验证 5 层以上嵌套调用是否正常工作
3. 验证上下文是否正确传递

## 7. Open Questions

- 无
