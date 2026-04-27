---
id: sug-52
title: "dogfood 验证机制成熟度 — testing 标准 dogfood 实跑流程模板（不只跑 unit，跑 harness next 实测 BUG-01 类 over-chain）"
status: pending
created_at: 2026-04-27
priority: high
---

req-45（harness next over-chain bug 修复（紧急））实证：1st testing 9 unit 全过但 dogfood 实跑发现 BUG-01（gate 插桩位置错，第一格 over-chain 未阻断），凸显 unit pass != dogfood pass 的根本鸿沟。2nd testing 用 tmpdir mock + workflow_next 直调验证才发现 over-chain 真实修复。修复方向：(1) testing.md 经验沉淀新增 dogfood 标准流程模板 — 影响 CLI 行为类 chg 必跑 dogfood 实测，模板含：tmpdir 工作区构造 + 关键产物 mock 缺失场景 + workflow_next 直调断言 stage 落点 + stdout 含禁止跳转提示；(2) plan.md §测试用例设计 模板加 dogfood 实跑 TC 必填字段（如 TC-D-01 dogfood 实测 over-chain 阻断），与 unit TC 并列；(3) 长期：bugfix-6 testing 契约重塑后续 chg 把 dogfood 实跑列为 testing 角色硬门禁 — 影响 verdict-driven stage / harness next / harness validate 等 CLI bug 修复时必跑，缺即 FAIL。
