---
id: sug-37
title: `harness validate --contract 7` 新增 `--scope <req-id>` / `--since <git-ref>` 过滤
status: pending
created_at: "2026-04-22"
priority: medium
---

# 背景

req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）testing 阶段发现 `harness validate --contract 7` 全仓扫描产出 319 条历史 legacy 违规（主要来自 `artifacts/requirements/req-0X...md` 老文档 + `.workflow/state/action-log.md`）。本 req 范围违规必须 `grep -E "req-32|chg-0[1-3]"` 手工过滤，信号被噪声淹没。

# 建议

- `harness validate --contract 7 --scope req-32` —— 只扫该 req 相关目录（`artifacts/{branch}/requirements/req-32-*/` + `src/` 新增/修改文件）
- `harness validate --contract 7 --since HEAD~5` —— 只扫最近 N 个 commit 涉及的文件
- 支持组合：`--scope req-32 --since HEAD~5` 交集

# 验收

- CLI 两个 flag 生效
- 本仓 `--scope req-32` 输出 0 条（P1-01 修后已为 0）
- 本仓 `--since HEAD~12` 覆盖 req-32 全部 commit 无遗漏
- TDD 单测
