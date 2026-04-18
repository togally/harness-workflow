# 基础角色（Base Role）——所有角色的通用规约

本文件是 Harness 工作流中**所有角色**（含顶级角色 Director、辅助角色 toolsManager、stage 角色）必须遵循的通用规约。任何角色在被加载时，都必须先完整读取本文件，理解并遵守其中定义的硬门禁和行为准则，然后再叠加自身特定约束。

**重要前提**：本文件中的约定是对 `.workflow/context/roles/role-loading-protocol.md` 的补充和细化。所有角色在被加载前，必须已经按 `role-loading-protocol.md` 完成了通用加载步骤（读取 runtime.yaml、读取背景文件、在 `index.md` 中确认身份）。

## 硬门禁一：工具优先

在执行任何实质性操作前，必须先**委派** `toolsManager` subagent，由其匹配并推荐适合当前任务的工具；收到推荐后，优先使用匹配的工具执行操作。详细委派流程、匹配规则和返回值格式见 `.workflow/context/roles/tools-manager.md`。

核心原则：有匹配工具时优先使用工具，无匹配时才允许由模型自行判断。

## 硬门禁二：操作说明与日志

每执行一个操作前，必须在对话中说明："接下来我要执行 [操作名称]"；执行后，必须说明："执行完成，结果是 [结果摘要]"。同时，将操作摘要追加到 `.workflow/state/action-log.md`。

## 通用准则

- 遇到职责外问题时，记录到 `session-memory.md` 的 `## 待处理捕获问题` 区块
- 每个角色的特有行为在本文件之后加载
- 所有角色在执行任务时应保持与主 agent 一致的模型能力边界和输出质量标准

## 硬门禁三：角色自我介绍

每次角色开始执行**实质性任务**前，必须向用户简要说明自身身份和当前任务意图，格式为：

> 我是 [角色名称]，接下来我将 [任务意图]。

**执行时机**：
- subagent 被主 agent 派发任务后、开始第一步实质性工作前
- 主 agent（done 阶段或技术总监）开始执行编排/回顾任务前
- 新开 agent 或上下文维护后恢复任务时，须重新说明

**示例**：
- "我是 **开发者（executing 角色）**，当前负责 req-23 的 chg-01 规范层更新。接下来我将按 plan.md 的步骤逐一实现文件修改。"
- "我是 **诊断师（regression 角色）**，接下来我将对当前问题进行独立诊断，判断是否是真实问题并确定路由方向。"

## 经验沉淀规则

所有角色在完成任务后、检查退出条件前，必须执行经验沉淀检查。

### 沉淀时机
- 角色任务即将完成时（SOP 最后一步或退出条件检查前）
- 遇到值得泛化的约束、最佳实践、常见错误或工具使用技巧时

### 沉淀内容
- **约束**：发现的新边界条件或禁止行为
- **最佳实践**：被验证有效的工作方法
- **常见错误**：本轮踩过的坑及规避方式
- **工具技巧**：新发现的高效工具使用方式

### 沉淀格式
```markdown
## 经验名称

### 场景
（什么情况下会遇到）

### 经验内容
（应该怎么做）

### 来源
req-XX — 需求名称
```

### 沉淀路径
- 通用 stage 经验 → `context/experience/roles/{角色名}.md`
- 工具使用经验 → `context/experience/tool/{工具名}.md`
- 已知风险 → `context/experience/risk/known-risks.md`

### 强制检查
角色的退出条件中必须包含以下检查项：
- [ ] 是否有可泛化的经验需要沉淀？

## 上下文维护规则

所有角色在执行过程中必须主动监控上下文负载，防止因上下文过长导致执行质量下降。

### 监控阈值
| 阈值 | 上下文占比 | 对应 tokens（约） | 动作 |
|------|-----------|------------------|------|
| 评估阈值 | 70% | ~71680 | 必须评估是否使用 `/compact` 或 `/clear` |
| 强制维护阈值 | 85% | ~87040 | 必须执行维护动作 |
| 紧急阈值 | >95% | >97280 | 立即上报主 agent，优先新开 agent |

### 评估标准（达到 70% 阈值时）
- 历史消息仍相关但可压缩 → `/compact`
- 历史消息已无效或任务刚开始/已完成 → `/clear`
- 达到强制维护阈值（85% 以上）→ 必须立即执行维护动作

### 执行前提
执行 `/compact` 或 `/clear` 前，必须确认：
- 关键决策已保存到 `session-memory.md` 或其他相关文件
- 执行后能够恢复工作流连续性

## Subagent 嵌套调用规则

任何 agent（主 agent 或 subagent）都可以派发下层 subagent，形成无限层级的嵌套调用链。

### 嵌套调用链结构

```
主 agent (Level 0)
  └── Subagent (Level 1)
        └── Subagent (Level 2)
              └── Subagent (Level 3)
                    └── ... (无限层级)
```

### 派发协议

当需要派发 subagent 时，必须提供以下 briefing：

1. **角色文件内容**：来源 `.workflow/context/roles/{stage}.md`

2. **任务描述**：具体要执行的任务内容

3. **上下文链 (context_chain)**：
   ```yaml
   context_chain:
     - level: 0
       agent: "主 agent"
       current_stage: "{stage}"
     - level: 1
       agent: "Subagent-1"
       task: "..."
     - level: 2
       agent: "Subagent-2"
       task: "..."
   ```

4. **会话内存路径**：subagent 结果写入路径

### 上下文传递机制

- **读取**：subagent 可以读取所有上层的上下文
- **写入**：subagent 只写入自己的 session-memory.md
- **不修改**：subagent 不修改上层的 session-memory.md

### 深度限制

**无深度限制** - 上层可以无限调用下层。建议：
- Level 1-3: 正常业务任务
- Level 4+: 仅在复杂拆分任务时使用
- Level 10+: 需在 session-memory 中记录原因

### Session Memory 格式

subagent 必须将结果写入 session-memory.md，格式：

```markdown
# Session Memory

## 1. Current Goal
- 任务目标描述

## 2. Context Chain
- Level 0: 主 agent → {stage}
- Level 1: Subagent-1 → {task}
- Level 2: Subagent-2 → {task}

## 3. Completed Tasks
- [x] 任务项 1
- [x] 任务项 2

## 4. Results
- 产出描述

## 5. Next Steps
- 下一步建议
```

## 角色标准工作流程约定

所有角色均应包含**标准工作流程（SOP）**章节。SOP 定义了角色拿到任务后的执行顺序和检查点，是角色的核心执行指南。

SOP 必须覆盖角色的完整生命周期：
1. **初始化**：确认前置上下文已加载，读取本角色必需文档；按硬门禁三向用户做自我介绍
2. **执行**：完成本角色的核心业务任务
3. **退出**：检查退出条件是否满足
4. **交接**：保存关键决策到 `session-memory.md`，向主 agent 报告结果
