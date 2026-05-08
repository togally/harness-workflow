---
id: sug-73
title: "git reset --hard 防御机制（reg-01 触发）"
status: pending
created_at: 2026-05-08
priority: high
---

reg-01（chg-01/02/04 代码改动被 git reset 抹掉）实证：长会话内 6 次 git reset --hard 把 tracked 改动全部抹掉，恢复靠 git fsck dangling stash commits 找回。需评估防御方案：(a) base-role 加硬门禁禁止 subagent Bash 跑 git reset 类命令；(b) 加 git hook 在 reset --hard 前 prompt user 确认；(c) archive revert dry-run 改用 git stash 替代 git checkout -- .（避免 'archive 失败 → 反射性 reset' 用户惯性触发）；(d) executing/testing 派发后强制 commit-as-checkpoint。承载需求：req-55（gstack 和 harness 工作流融合（开发承载分支 harness-gstack））archive 后 sug。
