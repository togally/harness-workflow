# harness next [--execute]

## 前置条件
- 有 current_requirement
- 当前 stage 的退出条件已满足（见角色文件）

## 执行步骤

### 检查退出条件
1. 读当前角色文件的"退出条件"清单
2. 逐条核查是否满足
3. 有未满足项 → 列出未满足条件，停止推进

### 推进 stage
```
requirement_review → planning
planning → executing（需要 --execute 确认）
executing → testing
testing → acceptance
acceptance → done
```

### 状态更新
1. 更新 `state/requirements/{req-id}.yaml` 的 `stage` 字段
2. 在 `state/sessions/{req-id}/session-memory.md` 写入阶段完成记录
3. 触发 after-task hook（经验沉淀检查）
4. 加载新 stage 的角色文件

### planning → executing 的特殊处理
- 需要用户明确确认（`harness next --execute`）
- 确认前展示：即将执行的变更列表、执行顺序、高风险操作提示

## 错误处理
- 退出条件未满足 → 列出具体缺失项，不推进
- 处于 done 状态 → 提示使用 harness archive 归档
