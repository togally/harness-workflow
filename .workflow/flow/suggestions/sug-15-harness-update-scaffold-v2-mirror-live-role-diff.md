---
id: sug-15
title: "harness update 检测 scaffold_v2 mirror 与 live role 的 diff 自动同步或告警"
status: pending
created_at: 2026-04-22
priority: medium
---

req-30 testing 阶段发现：修改 .workflow/context/roles/base-role.md 和 stage-role.md 时漏掉同步 src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/*.md 镜像，导致 test_scaffold_v2_mirror_matches_roles 新增失败。hotfix 手工同步 2 个文件解决。建议 harness update 或新命令 harness mirror-check 对比 live vs scaffold_v2 mirror 的 diff，默认告警 / 可选自动同步。避免这类 Scope 隐式遗漏反复出现。
