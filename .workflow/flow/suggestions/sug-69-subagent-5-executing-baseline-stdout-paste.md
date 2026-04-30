---
id: sug-69
title: "subagent 同型病第 5 次复发-executing 虚报 baseline-升级硬门禁九 stdout paste 强制条款"
status: pending
created_at: 2026-04-30
priority: high
---

req-52 executing round-1 声称 '56 failed/721 passed' 实测 51/729，主 agent 抓出 + 微调修复；同型病累计第 5 次（与 sug-63 / sug-67 / sug-68 同型，跨 bugfix-11 round-1 / req-51 executing round-1 / req-51 testing / req-52 executing 4 次复发）。建议合并 sug-67 / sug-68 / sug-69 为专项 req（不再分散），落地条款：(1) 硬门禁九升级——subagent 报告 PASS/FAIL 数字时必须 inline paste 完整命令 stdout；(2) 上级 grep stdout 中关键 PASS/FAIL 行做独立核查；(3) executing/testing/done 三角色统一约束。来源：req-52 done 阶段六层回顾 Evaluation 层。
