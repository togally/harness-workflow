---
id: sug-36
title: "legacy archive 双源整合 + harness migrate archive 后续"
status: pending
created_at: 2026-04-26
priority: low
---

legacy .workflow/flow/archive 与 artifacts/main/archive/ 双源长期并存，CLI archive 命令 stdout 已多次提示 harness migrate archive 后续动作但尚未实现。建议新增 harness migrate archive 子命令做双源整合 + 旧 archive 单一权威源选定（默认 artifacts/main/archive/，对人 only 与 req-42 archive 重定义对齐）。来源：bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） done 阶段六层回顾 Flow 层识别
