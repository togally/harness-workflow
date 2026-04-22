---
id: sug-09
title: "harness next 从 acceptance → done 需重试两次的回退 bug"
status: pending
created_at: 2026-04-22
priority: medium
---

实测本轮 req-28 从 acceptance 跑 harness next，首次返回 Workflow advanced to testing（回退），第二次才正确 advanced to acceptance，第三次才到 done。疑似 stage 转移函数有副效应或 entry 钩子触发了回退。需定位根因并加单元测试覆盖各 stage 顺向推进的幂等性。
