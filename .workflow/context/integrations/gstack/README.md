# harness × gstack 角色映射（integrations/gstack）

harness 工作流角色 ↔ gstack slash skill 强映射层。每个 harness 角色在执行时直接调用对应的 gstack skill，gstack 产出即为该 stage 的标准产物（requirement.md / change.md / plan.md）。

## 调用矩阵

| 角色（role_key） | gstack skill | 触发时机 | fallback 行为 |
|---|---|---|---|
| analyst | /office-hours | Step A1.5：需求澄清前（analysis stage 入口） | agent_kind_compatible=false 或 gstack 未装载 → 走原生 A1~A3，report 标注 fallback |

## 触发悖论说明

subagent（executing / analyst / 任何 harness 派发的子 agent）**不能**直接派发 slash skill（`/office-hours` 是 user-facing slash command，仅 Claude Code 主对话可触发）。

解决方案（路径 α）：analyst.md SOP 改为提示主 agent / 用户在主对话执行 `/office-hours`；主 agent / 用户兜底触发后，把 design doc path 回传给 analyst；analyst 接到 path 后跑 adapter 重组到 requirement.md。

## adapter mapping 压缩表

| office-hours 设计文档段 | requirement.md 段 | 处理 |
|---|---|---|
| `# Design:` 头部 / Problem Statement + Demand Evidence | frontmatter + `## Goal` | 重写 frontmatter；汇总 2~3 条 Goal bullet |
| Constraints + Recommended Approach / Approaches Considered（未选） | `## Scope.Included` / `## Scope.Excluded` | 提炼可交付清单；列未选方向 |
| Success Criteria | `## Acceptance Criteria` | 编号化 AC-01/02/... |
| Next Steps / The Assignment | `## Split Rules` | 转为 chg 拆分原则 |
| Premises / Open Questions / Cross-Model 等多余段 | `## Office Hours Notes` | 整体追加末尾，保留 Spec Review Loop 思考价值 |

详细 mapping 表见 `analyst.md` Step A1.5.adapter。

## 渐进扩展路标

本层本 req 仅落 analyst → /office-hours 一条映射。后续渐进扩展（各 req 自行落地，本注释仅为路标）：

- req-56: executing → /investigate
- req-57: testing → /qa
- req-58: acceptance → /review
- req-59: regression → /codex
