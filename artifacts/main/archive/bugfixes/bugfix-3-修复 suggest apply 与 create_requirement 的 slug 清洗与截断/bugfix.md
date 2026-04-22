---
id: bugfix-3
title: 修复 suggest apply 与 create_requirement 的 slug 清洗与截断
created_at: 2026-04-20
---

# Problem Description

- **触发**：`harness suggest --apply sug-08` 后，需求目录被建议正文中的 `/` 拆成多级嵌套（`req-30-清理 .workflow/flow/archive/main/ ….` 3 级），`.workflow/state/requirements/` 同样被污染，`runtime.yaml` 的 `current_requirement`/`active_requirements`/`stage` 被错配。
- **影响面**：不只 `suggest --apply`；任何路径（`harness requirement "含/的 title"`、`harness bugfix "含/的 title"`、`harness suggest` 正文长句）都可能触发。
- **重现步骤**：见 regression/diagnosis.md。

# Root Cause Analysis

见 `regression/diagnosis.md`：
- `apply_suggestion` 取首行无截断当 title；
- `create_requirement` / `create_bugfix` 直接把 raw title 拼进 Path，**未调 `slugify_preserve_unicode`**、无长度上限；
- 附：`apply_suggestion` 成功后 sug 文件未归档到 `flow/suggestions/archive/`。

# Fix Scope

**In scope**（`src/harness_workflow/workflow_helpers.py`）：
1. `create_requirement`：对 `requirement_title` 走 `slugify_preserve_unicode` + 长度上限（建议 ≤ 60 字符）生成 `dir_name` 的 slug 段，原 title 保留进 state yaml `title` 字段和 template `TITLE` 占位符。
2. `create_bugfix`：同上修复模式。
3. `apply_suggestion`：把 title 取值改为"首行 + 长度截断（≤ 60）"；slug 清洗职责下沉给 `create_requirement`。成功后将 sug 源文件 move 到 `.workflow/flow/suggestions/archive/`。
4. 同步 `requirement.md.tmpl`、`bugfix.md.tmpl` 等若依赖原 title 展示文案处确认无需改（仅 path 段用 slug）。
5. 新增或扩充单元测试：
   - `create_requirement` 传入 `"含/的 标题"` → 单级 `req-NN-<slug>/`；
   - `create_requirement` 传入 200+ 字 title → slug ≤ 60 且 state yaml 保留完整 title；
   - `apply_suggestion` 对 sug-08 风格长句 → 单级目录 + sug 文件移入 archive。

**Out of scope**：
- `migrate archive` 本身的清理（原 sug-08 的业务目的，留待本 bugfix 完成后再重跑 apply 并进入 req-NN 的 planning 流程）。
- `create_change` / `create_regression` / `rename_*` 已正确，不改。

# Fix Plan

按顺序：

1. **helper 提取**（workflow_helpers.py，新增或复用）：
   - 若项目无 `_path_slug(title, max_len=60)`，封装 `slugify_preserve_unicode(title)[:max_len].strip("-")` 并在空串时回退到 id。
2. **`create_requirement` / `create_bugfix` 改造**：
   - `slug_part = _path_slug(requirement_title)`；`dir_name = f"{req_num_id}-{slug_part}" if slug_part else req_num_id`；
   - state yaml path 同步改成用 `dir_name` 而非 raw title。
3. **`apply_suggestion` 改造**：
   - `raw_body = ...`；`title = raw_body.splitlines()[0].strip()[:60]`；空则回退 `suggest_id`；
   - `create_requirement` 调用不变（由它负责 slug 清洗）；
   - 成功后 `target.replace(suggestions_dir / "archive" / target.name)` 并确保 `archive/` 目录存在；
   - frontmatter 翻转改在搬动后执行。
4. **测试**：在 `tests/test_suggest_cli.py` 和 `tests/test_smoke_*` 中新增对应用例；全量 `python3 -m unittest discover tests` 必须与基线一致（无新回归）。
5. **验收**：在 tmp 仓或当前仓用 `harness requirement "含/的 标题"` 和重跑 `harness suggest --apply sug-08` 双验证；apply 后 sug-08 应在 `flow/suggestions/archive/` 且 req 目录单级、state yaml 路径单级、runtime.yaml 正常。

# Validation Criteria

- [ ] `harness requirement "含/的 标题"` 只产出单级 `req-NN-<slug>/`，state yaml 同理；
- [ ] `harness suggest --apply sug-08` 只产出单级 `req-NN-<短 slug>/`，sug-08 搬到 `flow/suggestions/archive/`，frontmatter `status: applied`；
- [ ] 长 title（>100 字）被截断为 ≤ 60 字符 slug，state yaml `title` 仍保留原句；
- [ ] `harness bugfix "含/的 标题"` 单级；
- [ ] `python3 -m unittest discover tests` 与基线一致，无回归（基线可用当前 171 tests 对齐）；
- [ ] 新增的 3+ 条针对 slug 清洗的单元测试全绿。
