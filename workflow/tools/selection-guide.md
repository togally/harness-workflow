# 工具选择指南

## 任务类型 → 推荐工具

| 任务类型 | 推荐工具 | 说明 |
|---------|---------|------|
| 读取文件 | Read | 优先于 Bash cat |
| 搜索内容 | Grep / Glob | 优先于 Bash grep/find |
| 编辑文件 | Edit | 精确替换，优先于 Write |
| 创建新文件 | Write | 全量写入 |
| 执行命令 | Bash | 仅系统命令，不可替代时使用 |
| 派发节点任务 | Agent | 主 agent 编排核心工具 |

## subagent 派发规范

主 agent 派发 subagent 时，必须提供以下 briefing：

```
1. 角色文件内容
   来源：workflow/context/roles/{stage}.md

2. 当前任务描述
   来源：state/requirements/{req-id}.yaml → current_change
         flow/requirements/{req-id}/changes/{chg-id}/change.md
         flow/requirements/{req-id}/changes/{chg-id}/plan.md

3. 历史上下文
   来源：state/sessions/{req-id}/chg-{id}/session-memory.md
         （有 handoff.md 时优先读 handoff.md）

4. 相关经验
   来源：state/experience/index.md → 匹配当前 stage 的分类
```

## 工具结果回流规范

subagent 完成后，主 agent 必须：

```
1. 读取 subagent 输出
2. 更新 state/sessions/{req-id}/[chg-id/]session-memory.md
   → 将 ▶ 更新为 ✅
3. 更新 state/requirements/{req-id}.yaml
   → 更新 completed_tasks / pending_tasks / current_change
4. 更新 state/runtime.yaml（如有全局状态变更）
5. 决定下一步：继续当前 stage / harness next / harness regression
```
