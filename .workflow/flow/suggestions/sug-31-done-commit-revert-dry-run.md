---
id: sug-31
title: "done 后 commit + revert dry-run 自动化"
status: pending
created_at: 2026-04-26
priority: medium
---

bugfix-5（同角色跨 stage 自动续跑硬门禁） testing 一次和二次均提到 'bugfix-5 当前未提交 commit，无 SHA 可 dry-run，SKIP（建议 acceptance 后补跑）'，acceptance 二次同样未提交。建议 done 阶段或 harness archive 前自动检测：若工作树干净且最近 commit 含本 req/bugfix id，自动跑 git revert --dry-run HEAD（不实际 revert），输出落 done-report 或 acceptance-report 的 revert 抽样段。当前是 testing/acceptance 跨 stage 通病，影响每个 bugfix 的回滚可信度证据。
