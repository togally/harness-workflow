---
id: sug-75
title: acceptance Step 1 与 human-docs 分阶段惯例对齐
status: pending
created_at: 2026-05-10
priority: medium
---

# sug-75：acceptance Step 1 与 human-docs 分阶段惯例对齐

## 现状

`acceptance.md` Step 1 字面要求：

> 验收开始前必须调用 `harness validate --human-docs --requirement <id>`，结果须为全 ok；未达项必须写入后续产出的 `acceptance-report.md`，并停下来把 subagent 交回 executing 角色补齐对人文档。

但 req-id ≥ 41 精简扫描下，human-docs 校验两份对人文档：

- `raw_artifact: artifacts/{branch}/requirements/{req-id}-{slug}/requirement.md`
- `done: artifacts/{branch}/requirements/{req-id}-{slug}/交付总结.md`

`交付总结.md` 由 **done 阶段**主 agent 产出（落位见 `repository-layout.md` §2 + `done.md` "对人文档输出"段）；**acceptance 阶段必然 0/2 或 1/2 pending**，与 Step 1"全 ok"字面要求结构性冲突。

历史实证：req-54 / req-55 acceptance 阶段 artifacts/.../交付总结.md 均不存在（done 阶段才落地），但 acceptance 仍以 PASS verdict 完成 archive，说明实际惯例 ≠ 角色文档字面。

req-56 acceptance / done 复现：acceptance 阶段 `harness validate --human-docs` REAL exit 1（0/2 pending）；done 阶段补 raw_artifact 副本 + 交付总结.md 后 REAL exit 0（2/2 present）。

## 触发场景

- req-56（harness requirement 默认调 /office-hours，--fallback 走原生 analyst，产出强制对齐 harness 文档规范）/ chg-03 / acceptance 阶段：testing 子 agent 独立评估 + acceptance 子 agent 处置 + done 主 agent 复现，三层均触发 by-design exit 1 与 Step 1 字面冲突的判定。
- 历史 req-54（硬门禁体系简化-砍4条降级-加1条项目级brief强约束） / req-55（gstack 和 harness 工作流融合-开发承载分支 harness-gstack）：acceptance 阶段同样 pending，同样 PASS verdict，无显式记录处置过程。

## 评估方案

至少 4 选项：

1. **(a) 修订 acceptance.md Step 1 文字**：把"全 ok"改为"分阶段 ok"——artifact-placement 在 acceptance 阶段必绿；human-docs 在 acceptance 阶段允许 raw_artifact + done 两项 pending（待 done 阶段补），不阻塞 verdict；Step 1 改为"调用并记录输出"，不再要求"交回 executing"。
2. **(b) 修订 human-docs 行为**：raw_artifact / done 在 acceptance 阶段视为 informational 不计入 exit；done 阶段才纳入 exit gate。
3. **(c) 把 raw_artifact 副本生成提前到 analysis 阶段尾**：analysis 完成后由 CLI 自动 cp `flow/requirements/{slug}/requirement.md` → `artifacts/{branch}/requirements/{slug}/requirement.md`；这样 acceptance 阶段 1/2 ok，仅 done 阶段补 交付总结.md 才 2/2。
4. **(d) 给 acceptance 角色加 default-pick 决策协议**：acceptance 子 agent 跑 human-docs 后默认 default-pick "raw_artifact / done pending 不阻塞"，PASS verdict 路由 done；只在 raw_artifact 形态错误（malformed）时 fail。

我推荐 **(a) + (c) 组合**：(a) 把惯例正式化到 acceptance.md，(c) 把 raw_artifact 副本生成自动化避免人工漏 cp；(b) 影响面太大不推荐。

## 影响面

- 文档层：`acceptance.md` Step 1 + `done.md` 对人文档段（落位） + `repository-layout.md` §2
- CLI 层（如选 c）：`harness next` analysis → executing 时自动 cp raw_artifact

## 工程量评估

- 选项 (a)：1 chg 文档改 ≤ 30 行
- 选项 (a) + (c)：2 chg，约 1-2 小时

## 承载需求

- 触发：req-56 / done 阶段六层回顾发现
- 承载：可单独立 req（小需求）或并到下一次 acceptance 优化 req
