---
id: sug-60
title: "harness requirement stdout 文案误导（artifacts 实际未落物）"
status: pending
created_at: 2026-04-29
priority: low
---

harness requirement / harness bugfix 命令首行 stdout 输出形如 'Requirement workspace: artifacts/main/requirements/...'，但 bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）方向 C 落地后 artifacts/ 实际未落机器型工件，文案与真实落点不一致，对人误导。建议把 stdout 首行改印 '.workflow/flow/requirements/{req-id}-{slug}/'（bugfix 同改 .workflow/flow/bugfixes/）；artifacts/ 仅占位 README 时改用次要提示行。来源：bugfix-11 acceptance round-2 §旁支观察 #1。
