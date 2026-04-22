---
id: sug-34
title: apply-all 解禁后 CLI 强化 warning，防止再次误触发
status: pending
created_at: "2026-04-21"
priority: medium
---

# 背景

req-31（批量建议合集（20条））chg-01 Step 1 已根治 `harness suggest --apply-all` 的 path-slug bug（原子化 + unlink 前校验 append 成功），该命令再次可用。但破坏性（打包成单一 req + 删除 sug body 文件）本身仍存在——即使无 bug，用户误触发仍会丢失工作。

本 req-31 触发 apply-all 前没有任何 stdout warning / 二次确认。

# 建议

`src/harness_workflow/workflow_helpers.py::apply_all_suggestions` 增强交互：

1. 进入函数后先 `pending` 计数，打印：
   ```
   ⚠️  apply-all will pack {N} suggestion(s) into a single requirement and PERMANENTLY DELETE the sug files.
      - sug-XX: title1
      - sug-YY: title2
      ...
   Continue? [y/N]:
   ```
2. 仅 `y`/`yes` 通过，否则 abort
3. 新增 `--yes` / `-y` flag 跳过确认（脚本化场景）
4. stderr（不是 stdout）打印删除动作，并在最终 summary 显示"N 个 sug body files deleted; {slug} requirement.md 已含 ## 合并建议清单"

# 影响

- 用户误触发概率大幅下降
- 向后兼容：`--yes` flag 覆盖 CI 脚本场景

# 关联

- `src/harness_workflow/workflow_helpers.py::apply_all_suggestions`
- req-31（批量建议合集（20条））chg-01（契约自动化 + apply-all bug）
- sug-12（create_suggestion frontmatter）关联——避免 apply-all 删除后 sug 无法重建
