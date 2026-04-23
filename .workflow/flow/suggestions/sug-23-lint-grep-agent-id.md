---
id: sug-23
title: "硬门禁六 lint：自动 grep 检查主 agent 输出 ID 紧跟简短描述"
status: pending
created_at: 2026-04-23
priority: low
---

req-35（base-role 硬门禁六）落地后靠主 agent 自觉。建议加 lint 工具：grep -E '(reg|req|chg|sug|bugfix)-[0-9]+' 命中行后必须紧跟 '（' 或 '('，可放 .git hook / CI / 主 agent 输出前自检。
