---
id: sug-33
title: "briefing 话术 lint：拦截 testing 全量回归 over-instructing"
status: pending
created_at: 2026-04-26
priority: medium
---

briefing 话术 lint：拦截 testing 默认全量回归 over-instructing（bugfix-6 B6 降级）

## 背景
来源：bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））regression diagnosis.md B6 修复点。
B6 原计划在 validate_contract.py 中新增 lint 规则 4：grep 主 agent 派发文本含 pytest tests/ -x 等全量回归指令
且无 plan.md / diagnosis.md §测试用例设计 引用 → WARN。

## 降级理由
本 bugfix scope 已含 13 修复点，B6 涉及读取 briefing 文本（session-memory / action-log 路径）的基础设施问题，
与本 bugfix 核心关注点（关注点分离 + 测试契约重塑）无技术耦合，技术实现路径独立。

## 建议实现要点
- lint 类型：WARN（不 FAIL，避免误伤合规场景）
- 触发条件：grep 派发文本含 pytest tests/ 全量 且缺 plan.md §测试用例设计 引用
- 验证方式：在历史 bugfix-5（同角色跨 stage 自动续跑硬门禁） session-memory 上跑应至少 WARN 1 次
- 挂载点：harness validate --contract test-case-design-completeness 扩展规则 4
- 实现文件：src/harness_workflow/validate_contract.py + briefing 文本读取 helper
