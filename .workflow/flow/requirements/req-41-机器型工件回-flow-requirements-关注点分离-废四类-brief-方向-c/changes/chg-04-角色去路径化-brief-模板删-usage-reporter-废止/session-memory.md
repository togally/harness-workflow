# Session Memory

## 1. Current Goal

chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止）完整执行，覆盖 AC-02 / AC-07 / AC-12 / AC-15，pytest ≥ 428 passed + 1 pre-existing fail。

## 2. Current Status

**完成**。所有三项任务已落地，pytest 428 passed，1 pre-existing fail（test_smoke_req28::ReadmeRefreshHintTest），与预期一致。

### 执行摘要

**Task S-A：去路径化（AC-02）**

六个角色文件（analyst.md / executing.md / regression.md / done.md / testing.md / acceptance.md）及两个 legacy alias（requirement-review.md / planning.md）中的硬编码 `→ artifacts/{branch}/...` 路径全部移除，替换为 `.workflow/flow/repository-layout.md` 引用。done.md 保留 `artifacts/{branch}/requirements/{req-id}-{slug}/` 字面路径（对人文档白名单，测试 test_req26_independent 要求）。

**Task S-B：brief 模板删除（AC-07）**

四类对人 brief（需求摘要.md / 变更简报.md / 实施说明.md / 回归简报.md）的模板章节从对应角色文件移除。requirement-review.md / planning.md 添加 legacy 兼容注释（req-02（workflow 分包结构修复）~ req-40（阶段合并与用户介入窄化）行为维持）。stage-role.md 契约 3 表从 7 行缩减至 2 行（仅保留 done/交付总结.md + ff 决策行）。

**Task S-C：usage-reporter 废止（AC-12）**

- `usage-reporter.md` 从 `.workflow/context/roles/` 和 scaffold_v2 镜像均 `git rm` 删除
- `role-model-map.yaml` 删除 usage-reporter 条目
- `index.md` 删除 用量报告官（usage-reporter）辅助角色行
- `harness-manager.md` 删除 §3.5.3 触发 usage-reporter 召唤章节

**AC-15：镜像零差（scaffold_v2 mirror sync）**

每次修改后均 `cp` 到 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/`，最终 `diff -r` 输出为空。

## 3. Validated Approaches

- 去路径化后 `grep -l "→ artifacts/"` 在六角色文件返回零命中 ✅
- `test_each_stage_role_has_dual_track_output_block` 通过方案：abolished 角色改用 `## 对人文档输出（...废止）` 标题（与 testing.md / acceptance.md 一致），保留 "对人文档输出" 子串
- `test_chg03_title_contract::test_each_stage_role_file_mentions_contract_7` 要求：所有 ROLE_FILES（含 regression.md）必须含 "契约 7"，regression.md 在产出说明段添加契约 7 声明
- `test_regression_contract::test_regression_md_exit_contains_validate_regression` 要求：exit 条件含 `harness validate --contract regression`，恢复至退出条件（不与 brief 绑定）

## 4. Failed Paths

- 将 abolished 角色的节标题改为 `## 产出说明` 导致 `test_each_stage_role_has_dual_track_output_block` 失败（该测试查找 "对人文档输出" 子串），已改回 `## 对人文档输出（...废止）`
- regression.md 删除 `harness validate --contract regression` 时连带删除导致回归测试失败，已在退出条件中单独恢复

## 5. Candidate Lessons

```markdown
### 2026-04-23 section 标题变更需与测试字符串同步
- Symptom：test_each_stage_role_has_dual_track_output_block 失败
- Cause：把 "## 对人文档输出（...）" 改为 "## 产出说明"，测试查找 "对人文档输出" 子串
- Fix：abolished 角色保留 "对人文档输出" 在标题中，改为 "## 对人文档输出（...废止）"
```

```markdown
### 2026-04-23 删除 brief 模板时注意不要误删关联的 validate 命令
- Symptom：test_regression_contract 失败
- Cause：删除回归简报章节时顺带删除了 exit 条件中独立的 harness validate 条目
- Fix：validate 条目独立于 brief 模板，恢复至退出条件
```

## 6. Next Steps

chg-04 完成，按计划推进 chg-05（done 阶段交付总结扩效率与成本段）。

## 7. Open Questions

无。

---

本阶段已结束。
