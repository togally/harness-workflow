# 工具项目自优化规范设计

## 1. 概述

Harness 作为工具项目，其模板、hook、命令、流程结构需要持续优化。与应用项目经验沉淀不同，工具项目的反馈来自**下游项目的使用数据**，而非本仓库内部的业务积累。

本规范定义：反馈采集 → 聚合分析 → 优化提案 → 人工确认 → 发版生效 的完整闭环。

## 2. 反馈信号分类

### 2.1 被动信号（下游项目自动采集）

| 信号类型 | 事件名 | 含义 | 采集时机 |
|----------|--------|------|----------|
| 阶段跳过 | `ff` | 用户频繁 ff 某些阶段，门禁价值低 | `harness ff` 执行时 |
| 阶段推进 | `stage_advance` | 记录阶段流转模式 | `harness next` 执行时 |
| 模板偏移 | `template_drift` | 模板被大幅修改，不贴需求 | 阶段切换时 diff |
| 回归创建 | `regression_created` | 同类回归反复出现 | `harness regression` 创建时 |
| MCP 使用 | `mcp_used` | 哪些 MCP 被实际调用 | MCP 调用成功后 |

### 2.2 主动信号（用户可选）

- `harness next --feedback "..."` — 阶段切换时附带评语
- `harness exit --feedback "..."` — 退出时可选评语
- 不强制、不打断流程

### 2.3 Agent 观察信号

Agent 在执行中发现的模式，写入 `session-memory.md` 后升级进入工具反馈池。

## 3. 三级反馈通道

### Level 1: 本地文件（当前实现）

```
下游项目 .harness/feedback.jsonl
  ↓
harness feedback → harness-feedback.json
  ↓
手动拷贝到工具仓库 → harness feedback --import
```

零依赖，立即可用，适合个人开发者。

### Level 2: MCP Server（团队场景，后续实现）

```
下游 Agent ←→ Harness Feedback MCP Server ←→ 工具仓库
```

MCP Server 暴露的 tool:
- `report_feedback(events)` — 提交反馈
- `query_known_issues(template?)` — 查询已知问题
- `query_optimization_proposals()` — 查询优化提案

### Level 3: Remote API + Dashboard（远期）

暂不实现，仅预留 JSON 格式兼容性。

## 4. 反馈聚合规则

### 4.1 聚合维度

| 维度 | 聚合方式 | 示例 |
|------|----------|------|
| 模板偏移 | 按模板文件名聚合 | `change.md` 在 8 个项目中被修改 15 次 |
| 阶段跳过 | 按 from_stage 聚合 | `plan_review` 跳过率 40% |
| 回归模式 | 按关键词聚合 | "编译失败" 类回归占 60% |
| MCP 使用 | 按 MCP id 聚合 | `nacos` 被 12 个项目使用 |

### 4.2 阈值规则

| 指标 | 阈值 | 触发动作 |
|------|------|----------|
| 模板偏移率 > 50% | 半数以上项目修改同一模板 | 生成优化提案 |
| 阶段跳过率 > 30% | 30% 以上项目跳过某阶段 | 生成门禁简化提案 |
| 同类回归 > 5 次 | 同模式回归超 5 次 | 生成流程防护提案 |
| MCP adoption >= 3 | 3+ 项目使用同一 MCP | catalog confidence → medium |
| MCP adoption >= 7 | 7+ 项目使用同一 MCP | catalog confidence → high |

## 5. 优化提案机制

### 5.1 提案格式

```yaml
# docs/context/tool-feedback/proposals/<slug>.yaml
id: <slug>
title: "change.md 模板增加风险评估字段"
type: template_improvement|hook_adjustment|command_enhancement|catalog_update
trigger: "template_drift: change.md, 8 projects, 15 modifications"
evidence:
  - "项目 A: 增加了'风险评估'段落"
  - "项目 B: 增加了'风险等级'字段"
proposal: "在 change.md 模板中默认增加 '## 风险评估' 段落"
risk: low|medium|high
status: draft|approved|rejected|applied
created: "2026-04-09"
```

### 5.2 评审标准

| 维度 | 标准 |
|------|------|
| 证据充分性 | 至少 3 个独立项目的反馈支持 |
| 向后兼容 | 不破坏已有项目的 harness update |
| 复杂度 | 优先低风险、小改动 |
| 可逆性 | 可通过 harness update --force-managed 回滚 |

### 5.3 审批流程

1. 聚合达阈值 → 自动生成提案（draft）
2. 维护者审阅 → approved/rejected
3. approved → 修改模板/hook/命令
4. 发版 → 下游 `harness update` 拉取

## 6. MCP Catalog 维护规则

- 任何项目 feedback 上报新 MCP → 收录，confidence: low
- adoption >= 3 → medium，install 时推荐
- adoption >= 7 → high，install 时强推荐
- 180 天无 adoption → stale → 再 180 天 → 降级
- 不自动删除，只降级

## 7. 发版生效流程

```
提案 approved → 修改模板/core.py → 更新版本号 → 发布 → 下游 harness update → 生效
```

managed files 自动刷新（尊重本地修改，不强制覆盖），新增文件自动创建。

## 8. 安全与隐私

- feedback.jsonl 只记录结构事件，不含业务代码
- export 输出统计摘要，不含文件内容
- 项目名可脱敏（hash）
- MCP 记录只含 id，不含查询内容
- 用户可随时删除 .harness/feedback.jsonl
