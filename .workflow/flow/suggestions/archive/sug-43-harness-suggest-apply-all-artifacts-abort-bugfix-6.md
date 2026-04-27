---
id: sug-43
title: "harness suggest --apply-all 残留 artifacts/ 旧路径检查导致 abort（bugfix-6 后遗症）"
status: applied
created_at: 2026-04-27
priority: high
---

现状：apply-all 创建 req 后期望在 artifacts/main/requirements/{req-id}/requirement.md 找 requirement.md（旧路径），但 bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））把 requirement.md 移到 .workflow/flow/requirements/{req-id}/requirement.md（新路径），apply-all 在旧路径找不到 → log ERROR → 'aborting before unlink' → sug 文件没被删，req 创建后 requirement.md 是空模板。req-44（批量建议合集（34条））实证。修复方向：apply_all 路径校验改为 .workflow/flow/requirements/.../requirement.md（新路径），并补 e2e 测试覆盖 apply-all + bugfix-6 路径。
