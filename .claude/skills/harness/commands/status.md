# harness status

## 前置条件
- 无（任何时候均可查询）

## 执行步骤
1. 读 `workflow/state/runtime.yaml`
2. 读所有活跃需求的 `state/requirements/{req-id}.yaml`
3. 输出状态摘要

## 输出格式
```
当前需求：{req-id} — {title}
当前阶段：{stage}（{角色}）
当前变更：{current_change}（如有）

进度：
  ✅ requirement_review
  ✅ planning
  ▶ executing（{current_change}）
  ○ testing
  ○ acceptance
  ○ done

活跃需求列表：
  → req-01-xxx（executing）
  ○ req-02-xxx（requirement_review）

对话模式：{open / harness（锁定到 {req-id} / {stage}）}
```

## 注意
- 只读操作，不改变任何状态
- 不进入 conversation_mode: harness
