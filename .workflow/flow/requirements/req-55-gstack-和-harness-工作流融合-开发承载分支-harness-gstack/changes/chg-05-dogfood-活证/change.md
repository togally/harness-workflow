---
id: chg-05
title: "dogfood 活证（用下一个真实需求端到端验证融合入口）"
parent_requirement: req-55
created_at: 2026-05-07
operation_type: change
stage: analysis
---

## Change Statement

用**下一个真实需求**（用户接下来调 `/harness-requirement` 启动的 req-56 或之后任意编号）作为 dogfood 端到端活证（候选 P，第 8 轮用户洞察修正后落地）：用户调 `harness requirement "<title>"` → harness-manager 创建 req 骨架 → 派发 analyst → analyst 按 chg-02 落地的 Step A1.5 触发协议**自动**检测 `gstack_status.agent_kind_compatible` → **主动提示**用户在主对话跑 `/office-hours` → 用户跑完反馈 design doc path → analyst 跑 adapter 重组覆盖该 req 的 `requirement.md`；retro 笔记落 `artifacts/project/experience/roles/analyst.md`。

本 chg 的产出 = 端到端验证 [req-55:gstack-harness 融合] 设计的**完整融合入口链**真能跑通——`/harness-requirement → harness-manager → analyst → /office-hours → adapter → requirement.md`。这是**真活证**：验证的是融合机制的"自动触发"语义，不是把 office-hours 单独抽出来手测。

## Key Deliverables

| # | 产物 | 落点 |
|---|---|---|
| (i) | 本 chg 在 req-55 周期内的"deferred 承诺"文档化 | 本 chg 的 session-memory.md：明示 chg-05 落地形态 = 下一个真实需求触发时由其 analyst 回写本 chg session-memory + retro |
| (ii) | retro 笔记模板（待下一个真实 req 触发后由 analyst 填实） | `artifacts/project/experience/roles/analyst.md`（chg-04 后已经 mirror，模板段在 chg-04 落地时一并预埋） |
| (iii) | 触发证据（下一个真实 req 完成时回填） | 该 req 的 design doc 在 `~/.gstack/projects/{slug}/...md` 存在 + 该 req 的 `requirement.md` 是 adapter 重组产物 + retro 四点已写入 analyst 经验文件 |

## Constraints / Reasoning

- **第 8 轮用户洞察推翻候选 R**：候选 R（用 req-55 自适用）的设计**绕过了融合入口**——req-55 已在 executing stage，让用户手动跑 /office-hours 再人工反馈给 analyst，跳过了 `/harness-requirement → analyst.Step A1.5 主动检测 + 主动提示` 这条**真正要被验证的链**。候选 R 是把 office-hours 单独抽出来手测，而非验证融合机制。用户原话："那我是不是不应该用 /office-hours 而是应该用 harness-requirement"——一句话点破设计 bug。
- **候选 P 才是真活证**：让下一个真实需求自然通过 `/harness-requirement` 入口走完整条链；analyst 的主动检测 + 主动提示在用户视角自然发生 → 验证的是**融合机制的端到端**而非孤立的 adapter 函数。
- **"sample req" 措辞已废弃**：第 7 轮把候选 P 描述为"用 sample req 演示，信号弱"是错误评估——候选 P 用任何下一个**真实** req 都同样有效，"sample" 与 "真实" 没有区别（都走同一条入口、同一条触发链）。第 8 轮去掉"sample" 限定，候选 P 即"下一个真实 req"。
- **req-55 自身 baseline 保留**：req-55 的 requirement.md 留作第 7 轮 analyst 手工 baseline（已落地，executing stage 在用），不再被 dogfood 重组覆盖；版本演进在 git history 可查。
- **本 chg 在 req-55 周期内不实跑**：candidate P 的"实跑"发生点 = 下一个真实需求；本 chg 在 req-55 内只是把这条 deferred 承诺文档化 + 让 chg-04 同步把 retro 模板段预埋到 analyst 经验文件。
- **retro 模板段预埋**：chg-04 mirror 范围已含项目级经验文件骨架；本 chg 增加一个 deliverable = 在 `artifacts/project/experience/roles/analyst.md` 末尾追加占位段「## gstack-harness 融合 retro（首次填写：req-56+）」+ 四点小标题（待真 dogfood 时回填内容）。

## Risks

| 风险 | 缓解 |
|---|---|
| 用户长时间不调下一个 `/harness-requirement` → chg-05 长期 deferred | 不视为风险：req-55 验收只到"deferred 承诺 + retro 模板段预埋"完成；真活证由后续 req 自然兑现，无 deadline；deferred 状态本身是合理的 |
| 下一个真实 req 时 analyst 触发协议失效（gstack_status 字段未写 / 触发链卡住） | chg-01 已落 runtime 字段；chg-02 已落 analyst.md Step A1.5 触发协议；测试套已过；fallback 协议已设计；下一个 req 触发即测 |
| office-hours 输出格式偏离 chg-02 adapter mapping 预期 | adapter mapping 已设计 fallback；下一个 req 真跑时 retro 会暴露偏差，反馈给 chg-02 修订 |
| retro 模板段预埋后用户看到困惑 | 模板段标"首次填写：req-56+"明示是占位，不影响 baseline 经验内容 |

## Acceptance Criteria

覆盖父 req AC-05：
- [chg-05 在 req-55 周期内交付] 本 chg session-memory.md 明示 deferred 承诺 + 下一个真实 req 触发后 analyst 自动回填的合约
- [retro 模板段预埋] `artifacts/project/experience/roles/analyst.md` 末尾含「## gstack-harness 融合 retro（首次填写：req-56+）」段 + 四点子标题
- [chg-04 mirror 同步] scaffold_v2 镜像 retro 模板段
- [真活证由下一个真实 req 兑现] 该 req 完成时由其 analyst 把 retro 四点回填到 analyst 经验文件 + 在本 chg session-memory.md 追加触发证据条目（design doc path / 触发链耗时 / 卡点）

## Dependencies

- [chg-01:gstack 内置发布契约]（gstack 已装载 + runtime.gstack_status 已写）
- [chg-02:analyst-office-hours 强映射]（adapter SOP + 触发协议已落 analyst.md）
- [chg-04:scaffold-v2 镜像]（retro 模板段同时 mirror，新项目复现 dogfood）

## Downstream

- 间接下游：req-56~59 渐进扩展时复用本 chg 验证的「`/harness-requirement → analyst → /office-hours → adapter`」入口模式，每开一个新角色映射就触发一次 dogfood 自动累积 retro

## Notes

- **历史版本说明**：本 chg 在第 7 轮 analyst 落 default-pick=候选 R（用 req-55 自适用）；第 8 轮用户提问 "那我是不是不应该用 /office-hours 而是应该用 harness-requirement" 暴露候选 R 绕过融合入口的设计 bug，本版重写为候选 P。第 7 轮版本可在 git history 检索（commit 标记 "chg-05 v1 候选 R"）。
- **降级路径已废弃**：第 7 轮原"R → P → Q 三级降级"链中 P 已上位为 default，Q（砍 chg-05）作为唯一保底；如未来 deferred 期间发现入口链根本不可触发（chg-01/02 落地有缺陷）→ enter regression 修源头，不降级到 Q。
- **真活证语义重定义**：从"在 req-55 内一次性自适用"改为"在下一个真实 req 触发时端到端自然兑现"——后者是融合机制的最佳验证语义。
