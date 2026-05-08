---
id: chg-02
title: "analyst → /office-hours 强映射 + adapter 后处理"
parent_requirement: req-55
created_at: 2026-05-07
operation_type: change
stage: analysis
---

## Change Statement

把 [req-55:gstack-harness 融合开荒] 中的"angle a 强化版"角色 ↔ gstack 命令强映射在本 chg 落第一条：**analyst（分析阶段角色）→ /office-hours（gstack YC Office Hours skill）**。仅改 1 个角色 SOP 文件 `.workflow/context/roles/analyst.md`，新增 1 个极简 1 行映射 yaml 和 1 个 ≤ 50 行 README；不改任何代码。adapter 后处理是文档化 SOP（不是代码工具）——由 analyst 角色按 SOP 把 office-hours 输出的 design doc 重组到 harness requirement.md 标准位置。

依赖 [chg-01:gstack 内置发布] 完成（用户主对话能直接 `/office-hours` 触发），但本 chg 不改 chg-01 任何资产，仅消费装载结果。

## Key Deliverables

| # | 产物 | 落点 |
|---|---|---|
| (a) | analyst SOP 强映射段（含触发协议 + adapter 后处理 + fallback） | `.workflow/context/roles/analyst.md`（在 Step A2 前插入新段） |
| (b) | 极简映射表 | `.workflow/context/integrations/gstack/role-command-map.yaml`（1 行 + 注释说明渐进扩展计划） |
| (c) | 调用矩阵 README | `.workflow/context/integrations/gstack/README.md`（≤ 50 行，含调用矩阵 + adapter mapping 压缩版 + 触发悖论说明） |

### (a) analyst.md 强映射段三部分详解

#### (a)(i) 触发协议（路径 α default-pick）

> subagent 不能派发 slash command（`/office-hours` 是 user-facing slash skill，仅主对话可触发）；analyst 在 Step A2 前先**提示主 agent / 用户**在 Claude Code 主对话跑 `/office-hours`，主题 = 当前 req 的标题，反馈输出 path 给 analyst 后再继续。

文档化伪代码：
```
Step A1.5（新增于 A1 与 A2 之间）：
1. 检查 runtime.yaml.gstack_status.agent_kind_compatible
   - false → 走 fallback 协议（见 (a)(iii)）
2. 输出 batched-report 给主 agent：
   "本 req 已配置 analyst → /office-hours 强映射；请在 Claude Code 主对话执行：
    /office-hours
    主题：<req title>
    完成后把 design doc 输出 path 反馈给我（格式：~/.gstack/projects/{slug}/{user}-{branch}-design-{datetime}.md）"
3. 暂停，等主 agent 在用户配合下完成 /office-hours，把 path 回传
4. 接到 path 后跳到 (a)(ii) adapter
```

#### (a)(ii) adapter 后处理 SOP（章节 mapping 表）

| office-hours 设计文档段（startup mode） | 重组到 harness requirement.md 段 | 处理方式 |
|---|---|---|
| `# Design: <title>` 头部 | frontmatter `id / title / created_at / operation_type / stage` | 重写 yaml frontmatter；id 取自 req-id；title 取自 design doc 头；stage = "analysis" |
| `## Problem Statement` + `## Demand Evidence` | `## Goal` | 汇总成 2~3 条 bullet：核心问题 + 用户价值 + 验证证据 |
| `## Constraints` + `## Recommended Approach` | `## Scope.Included` | 提炼为可交付项清单 |
| `## Approaches Considered`（"未选"分支） | `## Scope.Excluded` | 列"已比选但不采用"方向 |
| `## Success Criteria` | `## Acceptance Criteria` | **强对齐**：逐条编号化为 AC-01 / AC-02 / ...；每条标 `[AC-NN:简短描述]` |
| `## Next Steps` + `## The Assignment` | `## Split Rules` | 转为 chg 拆分原则 + 渐进扩展规划 |
| `## Premises` / `## Cross-Model Perspective` / `## Open Questions` / `## Distribution Plan` / `## Dependencies` / `## What I noticed` / `## Reviewer Concerns` 等多余段 | `## Office Hours Notes` 附加段 | 整体追加到 requirement.md 末尾，保留 office-hours 自带的 Spec Review Loop（5 维度 + 3 轮迭代 + quality score）思考价值 |

#### (a)(iii) fallback 协议

触发场景：
- 场景 1：runtime.yaml.gstack_status.agent_kind_compatible == false（用户用的不是 Claude Code）
- 场景 2：runtime.yaml.gstack_status 不存在（gstack 未装载，可能 chg-01 还没 ship 或装载失败）
- 场景 3：主 agent 拒派发 / 用户拒跑 /office-hours

行为：
- analyst 走原生 Step A1~A3 手工填实 requirement.md
- 写入一句 warn 到 batched-report：`/office-hours 未启用，本 req requirement.md 由 analyst 手工填实（fallback 模式）`
- 不阻塞 stage 推进；recovery hint：「请在后续 req 装载 gstack 后通过 chg-05 dogfood 模式补 office-hours 自适用证据」

### (b) role-command-map.yaml（极简 1 行）

```yaml
# .workflow/context/integrations/gstack/role-command-map.yaml
# Schema: { role-id: [gstack-skill-id, ...] }
# 当前仅落 analyst → /office-hours 一条强映射；后续 req 渐进扩展 ≤ 1 行 / req

analyst: ["/office-hours"]

# 渐进扩展计划（路标，不在本 req 落地）：
# req-56:  executing:   ["/investigate"]
# req-57:  testing:     ["/qa"]
# req-58:  acceptance:  ["/review"]
# req-59:  regression:  ["/codex"]
```

### (c) README.md（≤ 50 行）

包含五段：
1. 一句话定位：harness 角色 ↔ gstack 命令强映射的人读说明
2. 调用矩阵表（角色 / gstack skill / 触发时机 / fallback 行为）
3. 触发悖论说明（subagent 不能派发 slash skill，由主 agent / 用户兜底）
4. adapter mapping 压缩版（office-hours 段 → requirement.md 段，3 行表格）
5. 渐进扩展规划路标（与 (b) 注释同步）

## Constraints / Reasoning

- **仅改 1 个角色文件**（不改 5 角色全部）：用户拍板"一步步融入"；本 req 范围最窄。
- **adapter 是文档化 SOP，不是代码工具**：analyst 按 SOP 手工执行重组；不上 Python 转换器（避免引入工具维护成本 + Lock-in）。
- **role-command-map.yaml 极简 1 行**：避免一开始上 catalog 卡片 / 复杂 schema；本 req 仅"一对一无备选"。
- **README ≤ 50 行**：调用矩阵 + adapter mapping 压缩版 + 触发悖论说明三段，不出 catalog 卡片不出长文。
- **触发协议路径 α**（subagent 不能直接调 slash skill）：保留"角色 = 调 gstack 命令"语义；analyst 文档化"提示主 agent / 用户跑 + 跑 adapter"；主 agent / 用户兜底 slash command 调用——这是 [req-55:gstack-harness 融合开荒] 第 6 轮触发悖论解决方案。
- **fallback 不阻塞 stage 推进**：与 [reg-02:同步契约统一] 总则一致——融合是增强而非约束，gstack 不可用时 analyst 走原生 SOP。
- **不动 role-model-map.yaml / 不上 lint**：本 req 只"打通最小可用集"；lint 推后续 req。

## Risks

| 风险 | 缓解 |
|---|---|
| analyst.md 注入位置（Step A2 前）不准确 | 落地前先读 analyst.md 当前结构；A1.5 段插入位置精确到 A1 末尾 + A2 头之间，避免破坏 base-role / stage-role 加载链顺序 |
| adapter mapping 表执行时遇到 office-hours 输出偏离模板 | mapping 表标"如某段缺失则 skip + 记 warn 到 Office Hours Notes 节"，柔性处理 |
| 主 agent / 用户拒跑 /office-hours 导致 analyst 永久阻塞 | fallback 协议明确给"走原生 SOP" 的退出路径；不阻塞 stage 推进 |
| 渐进扩展规划与未来 req-56~59 实际拍板分歧 | role-command-map.yaml 注释段只写"路标，不在本 req 落地"；具体扩展由各 req 自身重新拍板，本注释段可改 |

## Acceptance Criteria

覆盖父 req AC-03 / AC-04：
- analyst.md 在 Step A2 前嵌入"调用 /office-hours"段（含触发协议 + adapter mapping 表 + fallback）
- role-command-map.yaml 含 1 行 `analyst: [/office-hours]` + 注释说明渐进扩展
- README ≤ 50 行
- adapter mapping 表完整覆盖 startup mode 和 builder mode 的核心段映射

## Dependencies

- [chg-01:gstack 内置发布契约]（用户主对话能直接 `/office-hours` 的物质前提）

## Downstream

- chg-04 镜像本 chg 改造到 scaffold_v2
- chg-05 dogfood 调本 chg adapter 把 design doc 重组覆盖本 req requirement.md

## Notes

- adapter mapping 表的细节由 analyst 在第 6 轮调研时已绘（详见 req-55 session-memory.md §5.5）；本 chg 落地时可直接复制该表到 analyst.md
- office-hours 自带 Spec Review Loop = harness analysis stage 当前缺失的质量门，是意外收益
