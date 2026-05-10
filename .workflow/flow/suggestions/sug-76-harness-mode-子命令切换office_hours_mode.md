---
id: sug-76
title: 加 harness mode 子命令切换 office_hours_mode（避免 regression 重置）
status: pending
created_at: 2026-05-10
priority: low
---

# sug-76：加 harness mode 子命令切换 office_hours_mode

## 现状

req-56（harness requirement 默认调 /office-hours，--fallback 走原生 analyst，产出强制对齐 harness 文档规范）/ chg-01 落地后，`office_hours_mode` 字段在 `harness requirement` 创建瞬间一次性决定（`required` 或 `fallback`），写到 `state/requirements/{req-id}-{slug}.yaml`。

如果用户跑了 `harness requirement "X"`（默认 `required`，触发 office-hours 路径），但 office-hours 跑到一半想转 fallback（小需求或 office-hours 体验不好），目前**没有轻量级切换 CLI**，必须：

- 走 `harness regression "想换 fallback 模式"` 重置 → 再 `harness requirement "X" --fallback` 重创 req（烧 req-id），或
- 手工编辑 `state/requirements/{req-id}-{slug}.yaml` 把 `office_hours_mode` 从 `required` 改 `fallback`（绕过 CLI，破坏审计链）

req-56 / chg-02 analyst.md Step A1.5.escape 段已埋伏 recovery hint："用户后悔想转 fallback 时，先 `harness regression` 走 regression 重置 mode"——但这是重型路径。

## 触发场景

- req-56 chg-02 implement 阶段在 escape 段记录 recovery hint 时识别为 sug 候选（不在本 req scope）
- 实际可能在用户使用 office-hours 路径中途想退出时高频触发

## 评估方案

加 `harness mode` 子命令：

```bash
harness mode --fallback         # 把当前 current_requirement 的 office_hours_mode 改 fallback
harness mode --required         # 改回 required（不常见但保留）
harness mode --requirement <id> --fallback   # 显式指定 req
```

行为：
- 读 `state/requirements/{req-id}-{slug}.yaml`，update `office_hours_mode` 字段
- 落审计日志到 `feedback.jsonl`（"mode_switched: required→fallback"）
- 与 `harness requirement` 一样的兼容兜底逻辑（`agent_kind_compatible=false` 时无视参数强制 fallback + warning）

## 影响面

- CLI 层：`cli.py` 加 `mode_parser`；`tools/harness_mode.py` 新建；`workflow_helpers.py` 加 `switch_office_hours_mode(root, req_id, mode)`
- 状态：feedback.jsonl 新事件类型 `mode_switched`
- 测试：单元 + dogfood

## 工程量评估

- 1 chg，约 50-80 行 Python + 5-8 个测试用例，半天工时

## 承载需求

- 触发：req-56 chg-02 implement 阶段
- 承载：低优先级 sug，可与 sug-75 并到一个小 req
