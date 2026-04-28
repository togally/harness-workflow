---
id: sug-55
title: "chg-02 部署同步契约 dev mode flag（HARNESS_DEV_MODE=1）"
status: pending
created_at: 2026-04-28
priority: medium
---

chg-02 R2 风险条款已声明：开发态频繁 pipx 重装影响开发效率，建议引入 HARNESS_DEV_MODE=1 环境变量豁免 acceptance 阶段的部署同步硬条目检查；harness install --check 子命令做版本对比预警。本 chg-02 留 followup 未实现，需后续 req 落地。来源：chg-02 OQ-3 + change.md §6 风险 R2。
