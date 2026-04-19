# 应用项目经验自进化规范

## 1. 概述

应用项目在持续开发过程中会不断积累业务经验和技术约束。这些知识如果仅停留在对话记忆中，会随会话结束而丢失；如果手工维护，则成本高且容易遗漏。

本规范定义经验从采集到淘汰的完整生命周期，使应用项目的知识体系能够自我演化：

**经验流转路径：**

```
session-memory.md → docs/context/experience/entries/ → docs/context/rules/
   （会话级）            （项目级经验库）                    （正式规则）
```

核心原则：**经验被命中的次数越多，其优先级越高**。高频命中的经验自然向规则晋升，长期未命中的经验自然过期退出，无需人工干预即可保持经验库的精准与精简。

## 2. 经验自动采集触发点

以下六种场景应自动触发经验采集。触发时，AI 需判断该知识是否具有跨变更复用价值，仅将通用性教训写入经验库。

### 2.1 被用户纠正时

当用户明确指出 AI 的判断、输出或行为有误，且纠正涉及可复用的知识（而非一次性笔误），应立即创建经验条目。

- **触发时机：** 用户纠正被识别后，在下一次回复前
- **source_type：** `correction`
- **典型示例：** 用户指出某个 API 的调用方式有误、某个框架的行为与 AI 假设不同

### 2.2 发现技术约束或隐藏规则

在执行过程中发现框架限制、API 行为与文档不符、环境隐式依赖等非显而易见的技术事实。

- **触发时机：** 发现时立即记录到 session-memory.md，阶段结束时提升为经验
- **source_type：** `constraint`
- **典型示例：** Spring Boot 多 profile 配置 list 类型被完全覆盖而非追加

### 2.3 路径失败且不应重试

某个技术方案、配置方式、工具用法被证明不可行，且该结论具有一般性（不仅限于当前特殊情况）。

- **触发时机：** 失败确认后立即记录
- **source_type：** `failure`
- **典型示例：** 某个第三方库与当前项目的 JDK 版本不兼容

### 2.4 变更完成后的教训提升

每个变更级任务完成时，AI 必须回顾本次任务中出现的新约束、失败路径、技术发现，判断 session-memory.md 中是否存在尚未提升为经验的教训。

- **触发时机：** `after-task` 钩子执行阶段
- **source_type：** `promotion`
- **判断依据：** session-memory.md 中标记为"待提升"的条目

### 2.5 MCP 成功解决问题

当通过 MCP 工具调用成功解决了一个非平凡问题，且用法值得记录供后续参考。需要记录**哪个 MCP 解决了什么问题**。

- **触发时机：** MCP 调用成功且结果被采纳后
- **source_type：** `mcp`
- **记录内容：** 问题模式、MCP 标识、成功/失败结果、上下文环境

### 2.6 回归确认了真实问题

当 `harness regression` 确认某个问题确实存在（非误报），该问题的模式应被记录为经验，防止同类问题再次出现。

- **触发时机：** 回归流程确认问题为真后
- **source_type：** `regression`
- **记录内容：** 问题模式、触发条件、修复方案

## 3. 经验条目格式

每条经验以独立 Markdown 文件存储在 `docs/context/experience/entries/` 目录下，使用 YAML frontmatter 承载元数据，正文承载教训内容。

文件名格式：`<id>.md`

```yaml
# docs/context/experience/<category>/<slug>.md frontmatter
---
id: exp-20260409-001
keywords: [spring-boot, profile, config-merge]
confidence: low
hit_count: 0
last_hit: ""
created: "2026-04-09"
source_type: constraint
source_change: "某变更名"
mcp_id: ""
---
```

正文部分（frontmatter 之后）：

```markdown
## 问题

Spring Boot 多 profile 配置合并时 list 类型会被完全覆盖而非追加。

## 上下文

在 application.yml 和 application-dev.yml 同时定义 list 类型配置时，
Spring Boot 不会合并两个 list，而是用 profile 文件的值完全替换基础文件的值。

## 结论

需要在 profile 文件中写完整列表，或使用 Map 结构替代 List。
```

### 3.1 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 格式 `exp-<YYYYMMDD>-<序号>`，当日内唯一 |
| `keywords` | list[string] | 是 | 用于索引匹配的关键词，至少两个 |
| `confidence` | enum | 是 | `low` / `medium` / `high`，初始创建时固定为 `low` |
| `hit_count` | int | 是 | 被后续任务命中的次数，初始为 0 |
| `last_hit` | string | 是 | 上次命中时间（ISO 日期），未命中时为空字符串 |
| `created` | string | 是 | 创建日期，ISO 8601 格式 |
| `source_type` | enum | 是 | `correction` / `constraint` / `failure` / `mcp` / `regression` / `promotion` |
| `source_change` | string | 是 | 产生该经验的变更标识 |
| `mcp_id` | string | 否 | 仅 `source_type: mcp` 时填写，记录解决问题的 MCP 标识 |

### 3.2 MCP 类型条目的扩展字段

当 `source_type` 为 `mcp` 时，frontmatter 中额外包含：

```yaml
mcp_id: "mcp-github-search"
mcp_context:
  problem_pattern: "跨仓库代码搜索"
  success: true
  environment: "monorepo, GitHub Enterprise"
```

## 4. 可信度升级规则

可信度反映经验的验证程度，决定其在索引中的排序权重和加载优先级。

### 4.1 `low`（新捕获）

- **条件：** `hit_count < 3`
- **含义：** 刚采集的教训，尚未经过跨变更验证
- **行为：** 仅在关键词精确匹配时加载，不主动推送

### 4.2 `medium`（多次验证）

- **升级条件：** `hit_count >= 3`，且命中来自**至少 2 个不同的变更**
- **含义：** 已在多个场景中被验证有效
- **行为：** 关键词匹配时优先加载

### 4.3 `high`（高频/高风险）

- **升级条件：** `hit_count >= 7`，且命中来自**至少 2 个不同的需求**；或被用户手动标记为高风险
- **含义：** 高频命中或高风险约束，已被充分验证
- **行为：** 列入活跃条目，session-start 时默认加载

### 4.4 升级时机

每次经验被命中时，检查是否满足升级条件。升级判定需要跨变更/跨需求的命中记录，通过 hit_log 追踪：

```yaml
hit_log:
  - change_id: "变更A"
    requirement_id: "需求X"
    date: "2026-04-15"
  - change_id: "变更B"
    requirement_id: "需求Y"
    date: "2026-04-20"
```

### 4.5 降级

- 若 `last_hit` 距当前超过 **90 天** 且无新命中，降级一档（high → medium → low）
- 降级检查时机：session-start 加载经验索引时

## 5. 规则晋升条件

当经验条目达到 `high` 可信度，且其内容具有广泛适用性（不局限于特定变更），应考虑晋升为正式规则。

### 5.1 自动晋升候选条件

- `confidence == high`
- `hit_count >= 10`
- 经验内容不限于特定变更的上下文（即去掉 change-specific 的上下文后仍然成立）

满足以上条件时，在 after-task 钩子中提示 AI 建议晋升，**晋升不自动执行**，由 AI 判断后决定。

### 5.2 人工晋升

用户随时可指定将任意经验晋升为规则，不受 hit_count 限制。

### 5.3 晋升执行流程

1. **确定目标位置：** 新建规则文件 `docs/context/rules/<topic>.md` 或追加到已有规则文件
2. **改写为规则语言：** 将经验的 detail 改写为命令式、明确的约束描述
3. **添加溯源引用：** 在规则中注明原始经验条目路径，例如 `<!-- source: experience/entries/exp-20260409-001.md -->`
4. **更新经验条目：** 在原经验 frontmatter 中添加 `promoted_to: docs/context/rules/<topic>.md`
5. **更新索引：** 将该条目移入 index.md 底部"已晋升"分区
6. **停止计数：** 晋升后的经验不再参与命中计数，但文件保留

## 6. 过期与清理策略

经验库需要自动淘汰机制防止无限膨胀，但**永不自动删除**，仅归档。

### 6.1 过期标记

- 条目 `last_hit`（或 `created`，若从未命中）距当前超过 **90 天** 且 `confidence == low`：标记为 `stale`（陈旧）
- 标记方式：在 frontmatter 中添加 `status: stale`

### 6.2 归档

- 已标记 `stale` 的条目在接下来 **90 天** 内仍未被命中：移入 `docs/context/experience/archive/` 目录
- 归档条目从 index.md 中移除，但文件完整保留

### 6.3 替代

- 当新证据与已有经验矛盾时，标记旧条目为 `status: superseded`，并在 frontmatter 中注明 `superseded_by: <新条目id>`
- 被替代的条目从索引中移除，文件保留

### 6.4 恢复

- 用户或 AI 可随时将归档或陈旧条目恢复为活跃状态
- 恢复时重置 `last_hit` 为当前日期，`status` 清除

### 6.5 时间线总结

```
创建 → (90天无命中且low) → stale → (再90天无命中) → archive
                                                        ↑
                          新证据矛盾 → superseded ──────┘
```

## 7. 经验索引自动维护

经验索引 `docs/context/experience/index.md` 是经验库的入口，必须保持与实际条目同步。

### 7.1 重建触发条件

以下任一事件发生时，必须重建索引：

- 新增经验条目
- 条目的 `confidence` 发生变更（升级或降级）
- 条目被归档（移入 archive）
- 条目被晋升为规则（promoted_to 被填写）
- 条目被标记为 stale 或 superseded

### 7.2 索引格式

索引表包含关键词、文件路径、加载时机、可信度、命中次数：

```markdown
## 活跃经验

| Keywords | Experience File | When To Load | Confidence | Hits | Notes |
|----------|-----------------|--------------|------------|------|-------|
| spring, profile, config | entries/exp-20260409-001.md | before design | high | 12 | 多次验证 |
| mybatis, pagination | entries/exp-20260410-002.md | before executing | medium | 5 | |

## 已晋升

| Keywords | Experience File | Promoted To | Hits |
|----------|-----------------|-------------|------|
| api, timeout | entries/exp-20260401-003.md | rules/api-standards.md | 15 |
```

### 7.3 排序规则

1. 按 `confidence` 降序（high > medium > low）
2. 同级别内按 `hit_count` 降序
3. 同 hit_count 按 `created` 降序（新条目优先）

### 7.4 活跃条目上限

- 排序后前 **20** 条未过期、未晋升的条目标记为"活跃"
- 活跃条目在 session-start 时默认加载到上下文
- 非活跃条目仅在关键词精确匹配时按需加载

## 8. MCP 经验规则

MCP（Model Context Protocol）工具的使用经验有其特殊性，需要额外规则。

### 8.1 采集规则

- 当 MCP 工具成功解决一个非平凡问题时，必须记录：
  - **问题模式：** 该 MCP 解决了什么类型的问题
  - **MCP 标识：** 使用了哪个 MCP（`mcp_id`）
  - **成功/失败：** 调用是否达到预期效果
  - **上下文环境：** 什么条件下该 MCP 有效（项目类型、技术栈等）

### 8.2 格式要求

- `source_type` 固定为 `mcp`
- `mcp_id` 必填
- frontmatter 中包含 `mcp_context` 扩展字段（见 Section 3.2）

### 8.3 反馈回流

- MCP 经验可通过 harness feedback 机制回流到工具仓库（交叉引用：变更"工具反馈回流设计与实现"）
- 回流仅涉及 MCP 与 harness 集成相关的经验，业务用法经验不回流
- 回流事件格式由"工具反馈回流设计与实现"变更定义

## 9. 应用项目与工具项目的经验路径

应用项目经验和工具项目经验有严格的路径分离，**业务知识永远不离开项目**。

### 9.1 应用项目经验（本地路径）

- **适用范围：** 业务知识、技术约束、框架行为、MCP 业务用法
- **存储位置：** `docs/context/experience/entries/`
- **索引位置：** `docs/context/experience/index.md`
- **生命周期：** 完整的 low → medium → high → 规则晋升路径
- **永不外流：** 业务经验仅在本项目内流转

### 9.2 工具项目经验（反馈回流路径）

- **适用范围：** 工作流摩擦点、模板缺陷、命令行为问题、钩子不足
- **不存储在本地 experience/ 目录**
- **回流通道：** harness feedback → 工具仓库聚合 → mcp-catalog 更新
- **事件格式和回流通道：** 由"工具反馈回流设计与实现"变更单独定义

### 9.3 归属判断标准

| 信号特征 | 归属 |
|----------|------|
| 涉及业务逻辑、API 行为、框架特性 | **应用项目经验** — 本地存储 |
| 涉及 harness 命令、模板、钩子、工作流行为 | **工具项目反馈** — 事件回流 |
| 涉及 MCP 工具的业务用法 | **应用项目经验** — 本地存储 |
| 涉及 MCP 工具与 harness 的集成问题 | **工具项目反馈** — 事件回流 |

两条路径共享相同的可信度升级机制（Section 4），但存储位置和消费方式不同。

## 10. 风险与权衡

### 10.1 索引膨胀

- **风险：** 经验条目增长过快导致 index.md 过长，影响上下文加载
- **缓解：** 活跃条目上限 20 条 + 过期淘汰机制 + 晋升后移出活跃区

### 10.2 误采集

- **风险：** 一次性问题被当作通用经验采集
- **缓解：** 初始可信度固定为 low，需经过多次跨变更命中验证才能升级；过期机制自动清理无用条目

### 10.3 晋升质量

- **风险：** 自动晋升候选的经验未必适合作为强制规则
- **缓解：** 晋升不自动执行，仅提示建议；AI 需将内容改写为规则语言后才写入规则文件

### 10.4 文件系统开销

- **风险：** 每条经验一个文件可能产生大量小文件
- **缓解：** 过期文件定期归档；实际经验采集频率不高（每个变更约 0–3 条）

### 10.5 跨变更追踪复杂度

- **风险：** hit_log 需要关联变更和需求信息，维护成本较高
- **缓解：** hit_log 为可选扩展字段；基础升级判定仅依赖 hit_count，精细判定在条目量大后再启用
