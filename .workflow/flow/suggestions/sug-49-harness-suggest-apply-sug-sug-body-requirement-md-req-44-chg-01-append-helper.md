---
id: sug-49
title: "harness suggest --apply 单 sug 路径仍未真填 sug.body 到 requirement.md（req-44 chg-01 _append helper 未触发）"
status: pending
created_at: 2026-04-27
priority: medium
---

req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） chg-01 修了 apply 系列的部分 bug：apply-all 路径校验 ✓ + 不 abort ✓。但 single --apply 路径仍**没真把 sug.body 写入 requirement.md**——req-45 实证：sug-46（sug-38（harness next over-chain bug） 升 P0）apply 后，requirement.md §goal/scope/AC 全是空模板，仅 §title 存了 sug content 头截断。chg-01 的 _append_sug_body_to_req_md helper 可能没在 single apply 路径调用，或调用了但走错分支。修复方向：grep apply_suggestion 函数主体确认 _append helper 是否被调用 + body 真注入；补 e2e 单 apply 端到端用例。
