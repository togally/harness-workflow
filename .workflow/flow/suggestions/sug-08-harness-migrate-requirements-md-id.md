---
id: sug-08
title: "扩展 harness migrate requirements 支持散落 .md 文件 + 同 id 冲突归并"
status: pending
created_at: 2026-04-22
priority: high
---

当前 workflow_helpers.migrate_requirements._process_source 只处理 child.is_dir()，不处理散落 .md 文件。req-28 / chg-03 因此 ABORT 由 git rm 走 chg-07 承接。需扩展：支持单 .md 迁移 + 同 id 冲突自动消歧（slug 去冲）。建议配套 --dry-run / --json 输出与单元测试。
