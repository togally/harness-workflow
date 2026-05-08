---
id: chg-05
title: "dogfood 活证（用下一个真实需求端到端验证融合入口）"
parent_requirement: req-55
created_at: 2026-05-07
schema_version: 1
---

# chg-05 session-memory

## 执行摘要

本 chg 在 req-55（gstack 和 harness 工作流融合，开发承载分支 harness-gstack）周期内仅完成 Step 1~3（文档级落地）；Step 4~6 是 deferred 段，由下一个真实 req 触发时由其 analyst 兑现。

## Step 执行状态

| Step | 状态 | 产物 |
|------|------|------|
| Step 1：analyst.md retro 模板段预埋 | 完成 | `artifacts/project/experience/roles/analyst.md` |
| Step 2：scaffold_v2 mirror 同步 | 完成 | `src/harness_workflow/assets/scaffold_v2/artifacts/project/experience/roles/analyst.md`；diff 自检清洁 |
| Step 3：deferred 承诺文档化（本文件） | 完成 | 本 session-memory.md |
| Step 4：用户调 `/harness-requirement` 启动 req-56+ | deferred（下一个真实 req） | - |
| Step 5：该 req analyst 自动跑融合入口链 | deferred | - |
| Step 6：该 req analyst 回填 chg-05 deferred 承诺 | deferred | - |

## deferred 承诺

**承诺声明**：本 chg 的真活证由**下一个真实 `/harness-requirement` 触发的 req（req-56 或之后任意编号）**兑现，不在 req-55 周期内实跑。

**触发条件**：用户调 `harness requirement "<title>"` → harness-manager 创建 req 骨架 → 派发 analyst → analyst 在 Step A1.5 检测 `runtime.yaml.gstack_status.agent_kind_compatible` → 为 true 时主动提示用户跑 `/office-hours` → 用户反馈 design doc path → analyst 跑 chg-02 adapter SOP 重组该 req 的 `requirement.md`。

**兑现判定**：以下三项全部满足时视为 chg-05 已兑现：
1. 该 req 的 design doc 在 `~/.gstack/projects/{slug}/...md` 存在；
2. 该 req 的 `requirement.md` 是 adapter 重组产物；
3. retro 四点已回填到 `artifacts/project/experience/roles/analyst.md` 的「## gstack-harness 融合 retro」段。

## 触发证据（待下一个真实 req 回填）

- trigger_req_id: <待回填>
- trigger_date: <待回填>
- design_doc_path: <待回填>
- 触发链耗时（用户视角）: <待回填>
- 卡点 / 摩擦: <待回填>
- retro 四点已落 analyst 经验: 是 / 否（应是）

## 回填合约

下一个真实 req 的 analyst 在其 Step A1.5.adapter 完成后，**必须**：

1. 把 retro 四点真实内容回填到 `artifacts/project/experience/roles/analyst.md` 的「## gstack-harness 融合 retro」段（替换占位 sub-section 内容，把"req-56+"替换为实际触发的 req-id）；
2. 在本 chg-05 session-memory.md 的「触发证据」段追加一条记录（含上述 6 字段）；
3. 在该 req 自己的 session-memory.md 留一行 cross-link 指向本文件的「触发证据」段。

> 不满足以上三项不视为 chg-05 已兑现；融合机制端到端验证必须由 `/harness-requirement` 入口自然触发，用户手填不构成活证。

## 依赖状态

| 依赖 | 状态 |
|------|------|
| chg-01（gstack 内置发布契约）：runtime.gstack_status 字段已写 | 已落地 |
| chg-02（analyst-office-hours 强映射）：adapter SOP + Step A1.5 触发协议已落 analyst.md | 已落地 |
| chg-04（scaffold-v2 镜像）：mirror 机制已建立 | 已落地 |

## 备注

- **第 8 轮重写说明**：本 chg 原候选 R（用 req-55 自适用）已被第 8 轮用户洞察推翻——候选 R 绕过了融合入口，改为候选 P（下一个真实 req 端到端兑现），才能验证「`/harness-requirement → analyst → /office-hours → adapter`」完整链路的自动触发语义。
- req-55 自身 requirement.md 保留作 analyst 手工 baseline，不被 dogfood 重组覆盖。

## ✅ chg-05 完成标记

- 落地时间：2026-05-07
- 落地范围：plan.md Step 1~3（req-55 周期内段：retro 模板段预埋到 analyst 经验文件 + scaffold_v2 mirror + 本 session-memory deferred 承诺写入）；Step 4~6 是 deferred 段，由下一个真实 req 触发兑现
- 硬门禁九产出核查：通过（主 agent 独立核查 retro 模板段 4 子节 / live ↔ scaffold_v2 mirror diff 清洁 / deferred 承诺 + 触发证据预留 + 回填合约 全部就位）
- 第 8 轮设计修正留底：候选 R → P 重写已落 chg-05 change.md / plan.md + 主 session-memory §8.B 第 8 轮段
