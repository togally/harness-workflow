---
id: sug-30
title: "bugfix 路径关注点分离回 .workflow/flow/bugfixes/"
status: pending
created_at: 2026-04-26
priority: high
---

bugfix 工件树（bugfix.md / diagnosis.md / session-memory.md / test-evidence.md / acceptance/checklist.md）当前全在 artifacts/main/bugfixes/ 路径下，违反 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））契约：机器型工件应回 .workflow/flow/bugfixes/，对人 bugfix-交付总结.md 留 artifacts/。bugfix-5 周期已确定起 bugfix-6 处理本议题，本 sug 作为正式记录。修复范围：repository-layout.md §2/§3 加 bugfix 落位规则、harness bugfix CLI 落位实际机器型工件、req-id ≥ 41 起严格执行、reviewer checklist 加 bugfix 路径抽样。
