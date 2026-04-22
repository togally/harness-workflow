---
id: sug-14
title: "harness archive 加 --yes / -y 非交互 flag"
status: pending
created_at: 2026-04-22
priority: low
---

harness archive 交互式提示 'Auto-commit archive changes? [y/N]:' 不接受 stdin piped 输入。自动化脚本只能绕路先 Ctrl-C 再手工 commit。建议加 --yes 或 -y flag 直接跳过。
