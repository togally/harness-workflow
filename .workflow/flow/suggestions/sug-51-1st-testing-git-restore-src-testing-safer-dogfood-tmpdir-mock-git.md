---
id: sug-51
title: "1st testing 跑 git restore 擦 src/ 改动事故 — testing 红线 + safer dogfood 协议（tmpdir mock / 不动当前仓库 git 状态）"
status: pending
created_at: 2026-04-27
priority: high
---

req-45（harness next over-chain bug 修复（紧急）） 1st testing 在 revert dry-run 步骤实跑 git restore .，丢失 src/harness_workflow/workflow_helpers.py + validate_contract.py 全部 executing 改动（_is_stage_work_done helper / check_stage_work_completion / run_contract_cli 分支），触发 BUG-03 P0 Critical，需 regression 路由后 2nd executing 重做 + commit b64bcd7 + push。修复方向：(1) testing.md 加红线 — 任何破坏性 git 命令（git restore / reset --hard / checkout . / clean -f / branch -D）在 testing 阶段一律禁止，dogfood 必须用 tmpdir mock 工作区不动当前仓库 git 状态；(2) base-role 硬门禁四例外条款 (i) 数据丢失风险扩展子条款 — testing dogfood revert dry-run 不得直接对当前仓库工作区操作；(3) lint 子命令 harness validate --contract testing-no-destructive-git 扫 testing 阶段 action-log.md 是否含禁用命令。
