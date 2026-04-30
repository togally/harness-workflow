---
id: bugfix-12
title: "runtime-block.yaml-误判用户野文件-白名单漏配"
created_at: 2026-04-30
operation_type: bugfix
stage: regression
---

# Regression Required Inputs

## 1. Current Problem

- Issue summary: `harness validate --contract user-write-protected-zones` 在非 dev_repo 用户仓里把 `.workflow/state/runtime-block.yaml`（harness 自家 raise_harness_block 写入的运行时状态文件）误判为用户野文件，输出 ABORT exit 1，阻塞用户后续 harness 命令链路。
- Related regression: bugfix-12（runtime-block.yaml-误判用户野文件-白名单漏配）
- Linked change: req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）/ chg-01（错误协议契约 + base-role 抛错门禁 + harness-manager 捕获路由）落地时新增 `raise_harness_block` 写 `state/runtime-block.yaml`，但漏改 `_SCAFFOLD_V2_MIRROR_WHITELIST`。

## 2. Required Human Inputs

| Item | Required | Notes |
| --- | --- | --- |
| Configuration | no | 修法纯白名单加 1 条字符串，无配置 / env / secret 变更 |
| Test data | no | 4 条 TC 全用 tmp_path + monkeypatch 构造，无外部 fixture |
| Account details | no | 不涉及账户 / 权限 / scope |
| External dependency details | no | 无外部依赖 / 不调外部接口 / 不动 PetMallPlatform |

## 3. Human Response Section

- Configuration: 无阻塞
- Test data: 无阻塞
- Account details: 无阻塞
- External dependency details: 无阻塞

## 4. Next Step

**无阻塞** — 诊断结论 + 修复方案 + 完成判据 lint 命令均已在 `regression/diagnosis.md` 写定。executing stage 可直接按 fix plan 推进，无需人工补充信息。
