---
id: sug-40
title: `harness update --scan-profile-only` flag——只刷 project-profile，不动 managed 模板
status: pending
created_at: "2026-04-22"
priority: low
---

# 背景

req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护）把 project-profile 生成挂到 `harness update` 末尾。用户只想更新 profile（比如改了 pyproject）时，必须整个 update 跑完，连带刷 scaffold 模板、managed 文件等副作用。

# 建议

新增 `harness update --scan-profile-only`：

- 只调 `project_scanner.write_project_profile(root)` 或 `_write_project_profile_if_changed`
- 跳过 `_sync_requirement_workflow_managed_files` / migration / feedback.jsonl 迁移等其它步骤
- stdout 简洁（只报 hash 是否漂移）

# 验收

- `harness update --scan-profile-only 2>&1` 输出仅包含 profile 相关行
- 不触碰 `.workflow/context/roles/` / scaffold_v2 模板
- `.workflow/context/experience/index.md` 不被刷
- TDD 单测
