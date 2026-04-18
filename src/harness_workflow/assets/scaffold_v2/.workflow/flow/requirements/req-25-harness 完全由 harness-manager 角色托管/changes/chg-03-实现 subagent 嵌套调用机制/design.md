# Subagent 嵌套调用机制设计

## 1. 概述

本文档定义 Harness Workflow 中的 subagent 嵌套调用协议，实现上层可以无限调用下层的 subagent 嵌套启动能力。

## 2. 核心概念

### 2.1 Subagent 身份体系

| 身份 | 说明 |
|------|------|
| **主 agent** | 通过 `harness enter` 或 harness slash 命令进入，拥有完整工作流控制权 |
| **Subagent** | 被主 agent 或其他 subagent 派发来执行特定任务，只执行分配的任务 |

### 2.2 调用层级

```
主 agent (Level 0)
  └── Subagent A (Level 1)
        └── Subagent B (Level 2)
              └── Subagent C (Level 3)
                    └── ... (无限层级)
```

## 3. Subagent 启动协议

### 3.1 派发请求格式

当上层调用下层时，必须提供以下 briefing：

```yaml
subagent_briefing:
  role: "{stage-role}"           # 如: executing, testing, acceptance
  task_context:
    requirement_id: "{req-id}"
    change_id: "{chg-id}"
    task_description: "具体任务描述"
  context_chain:
    - level: 0
      agent: "主 agent"
      current_stage: "{stage}"
    - level: 1
      agent: "Subagent A"
      task: "..."
  session_memory_path: "{path}"
  handover_mode: "automatic"    # automatic | manual
```

### 3.2 上下文传递机制

#### 3.2.1 调用链追踪 (Context Chain)

每个 subagent 必须维护一个 `context_chain` 列表，记录完整的调用链路：

```python
context_chain = [
    {"level": 0, "agent": "主 agent", "stage": "executing"},
    {"level": 1, "agent": "Subagent-1", "task": "执行 plan.md 步骤 1-3"},
    {"level": 2, "agent": "Subagent-2", "task": "实现特定功能模块"},
]
```

#### 3.2.2 会话内存 (Session Memory)

subagent 将结果写入 `session-memory.md`，格式：

```markdown
# Session Memory

## 1. Current Goal
- 任务目标描述

## 2. Context Chain
- Level 0: 主 agent → executing
- Level 1: Subagent-1 → 执行 plan.md 步骤 1-3
- Level 2: Subagent-2 → 实现特定功能模块

## 3. Completed Tasks
- [x] 任务项 1
- [x] 任务项 2

## 4. Results
- 产出描述

## 5. Next Steps
- 下一步建议
```

#### 3.2.3 交接文档 (Handoff)

当 subagent 需要将任务传递给下一个 subagent 时，使用 `handoff.md`：

```markdown
# Handoff Document

## From
- Agent: Subagent-2
- Level: 2
- Role: executing

## To
- Expected: Subagent-3 或返回上层

## Task Status
- Completed: 任务项 A, B
- In Progress: 任务项 C
- Pending: 任务项 D

## Context
- 传递给下层的关键信息

## Open Issues
- 待处理问题
```

## 4. 嵌套启动能力

### 4.1 派发接口

任何 agent（主 agent 或 subagent）都可以通过以下方式派发下层 subagent：

```
使用 Agent 工具，注入以下 prompt：

你是 Subagent-L{N}（{role}角色）
任务：{task_description}

## 角色文件
读取 .workflow/context/roles/{role}.md

## 上下文链
{context_chain}

## 会话内存路径
{session_memory_path}

## 执行规则
1. 只执行分配的任务
2. 将结果写入 session-memory.md
3. 不要执行 stage 推进命令
4. 完成后退出
```

### 4.2 深度限制

**无深度限制** - 上层可以无限调用下层，但建议：
- Level 1-3: 正常业务任务
- Level 4+: 仅在复杂拆分任务时使用
- Level 10+: 需在 session-memory 中记录原因

### 4.3 上下文隔离

每个 subagent 有独立的上下文空间：
- 读取：所有上层上下文
- 写入：自己的 session-memory.md
- 不修改：上层的 session-memory.md

## 5. 实现要求

### 5.1 角色文件更新

更新 `harness-manager.md` 添加：

```markdown
### Step 3.6: 派发 Subagent

当需要派发 subagent 时：

1. **构建 context_chain**：
   - 从当前 runtime 获取当前 stage 和 agent 身份
   - 如果是嵌套调用，继承上层的 context_chain 并追加当前层

2. **构建 briefing**：
   - role: 目标角色（如 executing, testing）
   - task: 具体任务描述
   - context_chain: 调用链
   - session_memory_path: 结果写入路径

3. **派发 subagent**：
   - 使用 Agent 工具
   - 注入标准 prompt
   - 等待返回

4. **处理返回**：
   - 读取 subagent 的 session-memory.md
   - 更新当前 session-memory.md
   - 决定下一步
```

### 5.2 Base Role 更新

在 `base-role.md` 中添加：

```markdown
## Subagent 嵌套调用规则

任何 agent（主 agent 或 subagent）都可以派发下层 subagent：

1. **构建调用链**：继承上层 context_chain，追加当前层信息
2. **指定角色**：明确被调用的角色类型
3. **传递上下文**：通过 briefing 传递必要信息
4. **等待返回**：subagent 完成后处理结果

subagent 可以继续派发更下层的 subagent，形成嵌套调用链。
```

## 6. 验收标准

- [x] harness-manager 能启动 stage 角色 subagent
- [x] subagent 能启动其他 subagent（任意层级）
- [x] 上下文能正确传递
- [x] 能正常完成五层以上嵌套调用
- [x] 上层调用下层无限制
