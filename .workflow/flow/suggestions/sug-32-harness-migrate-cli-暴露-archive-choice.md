---
id: sug-32
title: harness migrate CLI subparser 暴露 archive choice
status: pending
created_at: "2026-04-21"
priority: low
---

# 背景

req-31（批量建议合集（20条））chg-04 实现了 `migrate_requirements` + 扩展 `migrate_archive` 功能，能把 `.workflow/flow/archive/main/` 下扁平格式的 36+ 历史归档迁到 `artifacts/main/archive/requirements/`。

但 `src/harness_workflow/cli.py` 的 `harness migrate` subparser 只暴露 `requirements` 这一 choice（历史遗留），未暴露 `archive`——用户无法通过 CLI 直接调用归档迁移。

testing / acceptance 判"AC-10 ✅ 有 UX 小瑕疵"，底层功能完整。

# 建议

- `src/harness_workflow/tools/harness_migrate.py` 的 argparse subparser 加 `choices=["requirements", "archive"]`
- `harness migrate archive [--dry-run]` 作为 CLI 入口
- 更新 `harness migrate --help` 描述
- 新增 1 条 CLI 单测（`harness migrate archive --dry-run` stdout 含候选列表）

# 关联

- `src/harness_workflow/tools/harness_migrate.py`
- `src/harness_workflow/cli.py`
- req-31（批量建议合集（20条））acceptance-report.md D-2
- req-29（批量建议合集（2条））chg-02（遗留工作）
