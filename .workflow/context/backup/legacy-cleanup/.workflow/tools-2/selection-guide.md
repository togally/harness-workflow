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
| **上下文维护** | **Claude Code 上下文管理** | 根据阈值和任务状态选择 `/compact`、`/clear` 或新开 agent |

## 上下文维护工具选择指南

### 选择因素

#### 1. 上下文负载水平（引用 chg-01 阈值）
- **低负载** (<70% 最大上下文)：通常不需要维护
- **预警负载** (70-80%)：建议 `/compact`
- **高负载** (85-90%)：必须执行维护
- **紧急负载** (>95%)：必须新开 agent

#### 2. 当前任务阶段
- **planning/executing**：优先 `/compact`，保留关键决策
- **testing**：根据测试需求选择 `/compact` 或 `/clear`
- **acceptance**：通常 `/compact`，避免 `/clear`
- **regression**：复杂问题优先新开 agent

#### 3. 任务进度和重要性
- **任务刚开始**：可考虑 `/clear` 重新开始
- **任务进行中**：优先 `/compact`，保留任务状态
- **任务接近完成**：强烈倾向 `/compact`，完成收尾
- **关键任务**：谨慎维护，确保重要信息已保存

#### 4. 可用时间和资源
- **时间充足**：可执行完整维护流程
- **时间紧迫**：选择快速有效的维护动作
- **资源有限**：避免复杂交接，优先简单维护

### 决策流程图

```
开始上下文维护决策
  ↓
检查上下文负载（引用 chg-01 指标）
  ├── <70% → 继续工作，无需维护
  ├── 70-80% → 进入预警决策
  ├── 85-90% → 进入强制维护决策
  └── >95% → 必须新开 agent（紧急）
  ↓
预警决策（70-80%）
  ├── 任务进行中 → 建议 `/compact`
  ├── 任务刚开始 → 可考虑 `/clear`
  └── 其他情况 → 建议 `/compact`
  ↓
强制维护决策（85-90%）
  ├── 任务刚开始 → 必须 `/clear`
  ├── 任务进行中 → 必须 `/compact`
  ├── 任务接近完成 → 必须 `/compact`
  └── 任务已完成 → 必须 `/clear`
  ↓
紧急决策（>95%）
  └── 任何状态 → 必须新开 agent + handoff
  ↓
执行选定的维护动作
  ↓
验证维护效果，记录经验
```

### 选择矩阵

| 上下文负载 | 任务状态 | 推荐动作 | 优先级 | 注意事项 |
|------------|----------|----------|--------|----------|
| **70-80%** | 进行中 | `/compact` | 建议 | 压缩历史，保留关键信息 |
| **70-80%** | 刚开始 | `/clear` | 可选 | 清空重新开始 |
| **85-90%** | 刚开始 | `/clear` | 必须 | 清空，重新开始 |
| **85-90%** | 进行中 | `/compact` | 必须 | 压缩，保留关键信息 |
| **85-90%** | 接近完成 | `/compact` | 必须 | 压缩，完成收尾 |
| **>95%** | 任何状态 | 新开 agent | 紧急 | 交接，新会话继续 |

### 特殊情况处理

#### 1. 关键决策未记录
- **场景**：需要维护但关键决策未保存到文件
- **处理**：
  1. 先记录关键决策到 `session-memory.md` 或相关文件
  2. 再执行维护动作（优先 `/compact` 或新开 agent）
  3. 避免使用 `/clear`，除非已确保所有重要信息已保存

#### 2. 多指标同时触发
- **场景**：Token 估算达到预警阈值，同时消息条数达到强制维护阈值
- **处理**：按**最严重的阈值**处理
  - 任一指标达到紧急阈值 → 按紧急阈值处理
  - 任一指标达到强制维护阈值 → 按强制维护阈值处理
  - 所有指标都在预警范围内 → 按预警阈值处理

#### 3. 阶段转换时
- **场景**：从 `executing` 阶段转换到 `testing` 阶段
- **处理**：
  - 如果上下文负载较高（>60%），建议执行 `/compact`
  - 如果历史上下文与新阶段无关，建议执行 `/clear`
  - 确保新阶段开始时有干净的上下文

### 与决策树集成（引用 chg-02）

本选择指南基于 chg-02 维护动作决策树，提供简化的决策支持：

1. **输入相同**：chg-01 的监控指标和阈值
2. **逻辑一致**：相同的决策逻辑和规则
3. **输出对应**：对应的维护动作选择
4. **经验共享**：相同的经验记录要求

**快速参考（引用 chg-02 决策表）：**
| 情况 | 动作 | 优先级 | 说明 |
|------|------|--------|------|
| Token 70-80% | `/compact` | 建议 | 压缩历史，继续工作 |
| Token 85-90% + 任务刚开始 | `/clear` | 必须 | 清空，重新开始 |
| Token 85-90% + 任务进行中 | `/compact` | 必须 | 压缩，保留关键信息 |
| Token >95% | 新开 agent | 紧急 | 交接，新会话继续 |

## subagent 派发规范

主 agent 派发 subagent 时，必须提供以下 briefing：

```
1. 角色文件内容
   来源：.workflow/context/roles/{stage}.md

2. 当前任务描述
   来源：.workflow/state/requirements/{req-id}.yaml → current_change
         .workflow/flow/requirements/{req-id}/changes/{chg-id}/change.md
         .workflow/flow/requirements/{req-id}/changes/{chg-id}/plan.md

3. 历史上下文
   来源：.workflow/state/sessions/{req-id}/chg-{id}/session-memory.md
         （有 handoff.md 时优先读 handoff.md）

4. 相关经验
   来源：.workflow/state/experience/index.md（加载规则）→ 读取 .workflow/context/experience/ 下匹配当前 stage 的分类文件
```

## 工具结果回流规范

subagent 完成后，主 agent 必须：

```
1. 读取 subagent 输出
2. 更新 .workflow/state/sessions/{req-id}/[chg-id/]session-memory.md
   → 将 ▶ 更新为 ✅
3. 更新 .workflow/state/requirements/{req-id}.yaml
   → 更新 completed_tasks / pending_tasks / current_change
4. 更新 .workflow/state/runtime.yaml（如有全局状态变更）
5. 决定下一步：继续当前 stage / harness next / harness regression
```
