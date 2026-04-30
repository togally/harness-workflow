---
id: sug-68
title: "硬门禁九升级：'声称 PASS 但 stdout 没真粘'同型病第二次复发，成文化'完整 stdout paste 才算汇报'"
status: pending
created_at: 2026-04-30
priority: high
---

本周期累计同型病 3 次：bugfix-11 round-1（声称 lint 0 命中实际漏 grep 关键词）+ req-51 executing round-1（声称 21 TC PASS 实测 13/2/6）+ req-51 testing（声称 36/744 实测 51/729）。sug-63 已捕获骨架（lint 关键词清单必须由上级独立设计）但未约束'subagent 汇报必须含完整 stdout paste'。建议升级硬门禁九条款：subagent 报告含 PASS / FAIL 数字时必须 inline paste 命令完整 stdout（不能仅给摘要数字），上级核查时 grep stdout 中关键 PASS/FAIL 行；同型病 3 次复发证明骨架不够，本 sug 升 high 优先级、扩条款。来源：req-51 / done 阶段六层回顾 Evaluation 层。
