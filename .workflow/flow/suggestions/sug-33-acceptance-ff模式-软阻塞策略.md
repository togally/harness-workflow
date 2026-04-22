---
id: sug-33
title: acceptance 阶段与 ff 模式冲突的"软阻塞"判定策略
status: pending
created_at: "2026-04-21"
priority: medium
---

# 背景

req-31（批量建议合集（20条））acceptance 阶段发现 10 份对人文档未补（5 变更简报 + 5 实施说明），属 executing 阶段预知延期。testing/acceptance 判"非阻塞 D-1"，但 ff 模式下该决策路径不明确：

- 严格遵守 stage-role "对人文档契约" → 应阻断 ff 推进到 done
- 按 ff 自主决策 → 可接受延期、交 done 阶段六层回顾补齐
- 当前表现为 acceptance 放行 + done 阶段选择"延期转 sug"

需要明确的"软阻塞"策略：什么情况下 acceptance 应该硬阻断，什么情况下可延期。

# 建议

在 `context/roles/acceptance.md` 和 `context/evaluation/acceptance.md` 新增 "ff 模式软阻塞判定矩阵"：

| 差异类型 | 阻断条件 | 延期条件 | 决策点 |
|---------|---------|---------|--------|
| 代码缺失（AC 实现未完成） | always 阻断 | 不允许 | executing 返工 |
| 对人文档缺失（变更简报/实施说明） | 若涉及 AC-自证或契约 7 核心条款 | 其他场景可延期 | 在 acceptance-report 显式登记 decision_point |
| 测试缺失 | 若涉及 AC-综合或 AC-自证 | 其他场景可延期 | 同上 |
| UX 小瑕疵（CLI help / parser）| 通常不阻断 | 可延期 | 转 sug |
| legacy fallback 类 | 通常不阻断 | 可延期 | 转 sug |

配套：acceptance-report.md 模板新增 "软阻塞决策点" 小节，明确列出每条延期的理由和后续跟踪（sug-id / bugfix-id）。

# 关联

- `.workflow/context/roles/acceptance.md`
- `.workflow/context/evaluation/acceptance.md`
- req-31（批量建议合集（20条））acceptance-report.md D-1
- sug-35（10 份对人文档补齐任务）
