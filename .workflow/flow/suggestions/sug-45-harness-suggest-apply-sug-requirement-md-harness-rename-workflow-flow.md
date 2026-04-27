---
id: sug-45
title: "harness suggest --apply 单 sug 不真填 requirement.md + harness rename 漏 .workflow/flow/ 目录"
status: pending
created_at: 2026-04-27
priority: medium
---

本周期 sug-43 apply 实证两条新 CLI bug：(1) harness suggest --apply <id> 单 sug 路径只创建空 requirement.md 模板就喊 'Applied'，**不真把 sug.content 写入 requirement.md**——req-44 实证。(2) harness rename requirement <old> <new> 改了 .workflow/state/requirements/ + artifacts/main/requirements/ 两处目录，但**漏了 bugfix-6 后新加的** .workflow/flow/requirements/ 目录——req-44 实证（手工 mv 修复）。两条都吸收到 req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症））AC-02 / AC-03，本 sug 仅作跟踪登记。
