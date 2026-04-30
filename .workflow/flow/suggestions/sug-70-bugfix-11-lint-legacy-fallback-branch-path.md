---
id: sug-70
title: "bugfix-11 反例 lint legacy fallback 关键词过宽-误伤合法 branch-path 兼容路径注释"
status: pending
created_at: 2026-04-30
priority: medium
---

req-52 chg-04 在 workflow_helpers.py 注释中合法使用 'legacy fallback' 描述 branch-path 兼容路径，但被 bugfix-11 反例 lint test_req_01_no_legacy_branch_present_in_diff 字面命中，不得不在 round-2 改写为 'branch-path 兼容路径' 字面替换才避开冲突。建议 lint 关键词收窄：(1) 限定 docstring 上下文（仅扫码逻辑路径，跳过注释/docstring）；(2) 排除 'branch-path' 邻近词；(3) 加白名单豁免 chg-01 双轨过渡场景。来源：req-52 done 阶段六层回顾 Constraints 层。
