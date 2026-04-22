# Change

## 1. Title

修复 harness suggest CLI：filename fallback + 编号跨 archive 单调递增 + done 阶段 sug frontmatter 硬门禁

## 2. Goal

- 让 `harness suggest --apply` / `--delete` / `--archive` 对无 YAML frontmatter 的 sug 文件也能成功（以 filename 作为 fallback 匹配 sug-id），同时 `create_suggestion` 在编号时跨 `.workflow/flow/suggestions/` 当前目录与 `archive/` 子目录计算最大编号并 +1，保证单调递增；并在 done.md / stage-role.md 中落硬门禁"新 sug 必含 frontmatter"。

## 3. Requirement

- `req-28`

## 4. Scope

### Included

- `src/harness_workflow/workflow_helpers.py`（或等价模块）中的三处 sug 操作：`apply_suggestion` / `delete_suggestion` / `archive_suggestion`，在按 frontmatter 匹配失败时回退按 filename 前缀（`sug-NN`）匹配。
- 同文件中的 `create_suggestion`：扫 `.workflow/flow/suggestions/*.md` + `.workflow/flow/suggestions/archive/**/*.md`，取 `sug-NN` 最大编号后 +1，避免池清空后编号回滚。
- `done.md` + `stage-role.md` 追加"新 sug 必含 YAML frontmatter"SOP 条目；`create_suggestion` 写入时若调用方未提供 frontmatter，则直接报错退出。
- scaffold_v2（`harness_workflow/scaffold_v2/` 下与 done / stage-role 同名的骨架）同步补丁，确保 `harness install` 下游仓库获得一致门禁。
- 新增 `tests/test_suggest_cli.py`：(a) filename fallback 匹配，(b) create 跨 archive 的编号 +1，(c) 无 frontmatter 写入被拒绝。

### Excluded

- 不改 `harness suggest --list` 的输出格式。
- 不回填历史无 frontmatter 的 sug 文件内容（仅保证操作能识别）。
- 不修 `create_requirement` 的 slug 处理（req-28 父目录仍带全角括号的历史遗留，留作后续 sug）。

## 5. Acceptance

- Covers requirement.md **AC-15**：filename fallback + 编号单调递增 + done 阶段 frontmatter 门禁 + 新增测试全部通过。

## 6. Risks

- 风险 A：历史 archive 目录可能存在异常命名（非 `sug-NN`）的文件 → 缓解：正则匹配 `^sug-(\d+)` 并忽略不匹配项，测试用例覆盖空 archive / 异常命名两种边界。
- 风险 B：scaffold_v2 同步遗漏导致下游新装仓库门禁缺失 → 缓解：chg-01 plan 的静态检查步骤显式 diff scaffold_v2 与源文件。
- 风险 C：done 阶段历史 sug 不带 frontmatter → 缓解：只对"新写"加门禁，`apply/delete/archive` 的 fallback 兼容历史文件。
