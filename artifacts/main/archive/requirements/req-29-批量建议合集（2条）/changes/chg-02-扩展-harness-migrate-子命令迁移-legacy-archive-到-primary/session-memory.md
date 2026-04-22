# Session Memory

## 1. Current Goal

- 新增 `harness migrate archive` 子命令，把 legacy `.workflow/flow/archive/` 下已有归档迁到 `artifacts/{branch}/archive/`。覆盖 req-29 AC-04。

## 2. Current Status

- planning 阶段已产出：change.md / plan.md / 变更简报.md。
- 强依赖 chg-01 先合入。
- executing 已完成（2026-04-19）：
  - ✅ Step 1 设计 `migrate_archive` 算法：识别 legacy 两种形态（`<branch>/{kind}/...` + 裸 `{kind}/...`），目标统一 `artifacts/{branch}/archive/{kind}/<dir>`。
  - ✅ Step 2 实现 helper：采用 briefing 硬约束的 `shutil.move` 语义（不做 plan.md 的 copy-verify-delete，与 `migrate_requirements` 完全对齐），目标已存在 → conflict 记录不覆盖、源保留；支持 dry-run；保留 legacy 空父目录。
  - ✅ Step 3 扩展 CLI：`resource` choices 加 `archive`，dispatch `migrate_archive`，帮助文案同步。
  - ✅ Step 4 新增 `tests/test_migrate_archive.py` 5 条用例：requirement happy、bugfix happy、dry-run、冲突、幂等。
  - ✅ Step 5 测试：`unittest tests.test_migrate_archive -v` 5/5 PASS；`discover -s tests` 145/145 PASS（36 skipped）无回归。
  - ✅ 对人文档 `实施说明.md` 已产出。
  - ❌ **本仓未真跑** `harness migrate archive`——按 briefing 硬约束等 chg-05 smoke 后或 session 末尾由主 agent 执行。

## 3. Validated Approaches

- 已确认现有 `src/harness_workflow/tools/harness_migrate.py` 模式：`resource` + `--dry-run` + 调用 helper；扩展 `archive` 分支即可。
- 已确认 legacy 下存在 `main/` 分支子树 + 裸 `req-20-...` 旧扁平条目两种形态，迁移算法需兼容。

## 4. Failed Paths

- Attempt: 无
- Failure reason: n/a
- Reminder: 不要直接 `shutil.move`，必须 copy-verify-delete，否则中断会丢数据。

## 5. Candidate Lessons

```markdown
### 2026-04-19 legacy 迁移命令安全范式
- Symptom: 历史数据迁移中断导致源/目标均不完整。
- Cause: 直接 move 不可回滚。
- Fix: copy → 按文件列表 + hash 验证 → 删 legacy；任何步骤失败就 abort 保留 legacy 完整。
```

## 6. Next Steps

- executing 接手时先在 dev fixture 上跑通 happy path 与冲突检测，再在本仓真跑。
- 本仓实跑前建议先记录一份 legacy archive 目录结构快照（git + tree），便于出错回滚核对。

## 7. Open Questions

- 是否要支持 `--force` 覆盖冲突条目？本 change 默认不做，若 executing 阶段认为必要可按 high-risk 决策点记录并提给 acceptance 确认。
