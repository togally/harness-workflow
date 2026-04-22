---
id: sug-38
title: req-32 AC-05 stderr 文案 spec 回写——承认 authored/modified 双场景
status: pending
created_at: "2026-04-22"
priority: medium
---

# 背景

req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护）AC-05 要求"CLAUDE.md / AGENTS.md 用户自定义时 `harness update` 跳过 + stderr 提示"。

实际代码有两条分支：
- `_is_user_authored=True`（新文件、用户首次编写）→ stderr `skipping user-authored file`（req-31 sug-14 遗产）
- `managed_state` 已登记 hash + 用户再改 → `skipped modified` 兜底 → req-32 testing 收口新增 stderr `skipping user-modified file`

spec 文案仅描述第一种场景，实际实现覆盖两种。

# 建议

在 `requirement.md` / `change.md` 的 AC-05 / Impact Surface 小节追加一行：
> AC-05 对应两类场景：`skipping user-authored file`（新建用户文件）/ `skipping user-modified file`（已 managed 被用户改过）。两者文案不同但语义一致：皆表示本次 update 跳过保护。

# 验收

- `artifacts/main/requirements/req-32-.../requirement.md` AC-05 追加说明
- `artifacts/main/requirements/req-32-.../changes/chg-02-.../change.md` AC 区追加说明
- 契约 7 零新增违规

注：本 sug 属事后 spec 对齐，不涉及代码改动。
