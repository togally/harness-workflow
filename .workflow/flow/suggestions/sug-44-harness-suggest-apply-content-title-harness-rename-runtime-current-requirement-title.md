---
id: sug-44
title: "harness suggest --apply 取 content 头当 title + harness rename 不同步 runtime current_requirement_title"
status: pending
created_at: 2026-04-27
priority: medium
---

两个相关 CLI bug 一并登记：(1) harness suggest --apply <id> 创建 req 时取 sug 的 content 第一行（截断版）当 req title，**应该取 sug 的 title 字段**。req-44 实证：sug-43 title='harness suggest --apply-all 残留 artifacts/ 旧路径检查导致 abort（bugfix-6 后遗症）'，apply 创建的 req title='现状：apply-all 创建 req 后期望在 artifacts/main/requirements/{req-id'（content 头截断）。(2) harness rename requirement <old> <new> 改了目录名 + state yaml requirement_title，**没同步** runtime.yaml 的 current_requirement_title 字段。req-44 实证：rename 后 runtime current_requirement_title 仍残留旧 mangled 标题，需手动 Edit 修。修复方向：apply 走 sug.title 字段；rename 同步 runtime 三字段（current_requirement_title / locked_requirement_title 如设了 / active_requirements 如含旧 id）。
