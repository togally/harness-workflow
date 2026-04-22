# Change

## 1. Title

chg-01（契约自动化 + apply-all bug）：`harness status --lint` / `harness validate` 契约自检 CLI + 辅助角色契约 7 扩展 + `create_suggestion` frontmatter 补齐 + 《回归简报.md》契约补强 + `apply_all_suggestions` path-slug 同源 bug 修复

> 父需求：req-31（批量建议合集（20条））

## 2. Background

源自 req-31（批量建议合集（20条））§5 Split Rules 的 **chg-01 分组**（A 组契约自动化 5 条 + D 组 apply-all bug 1 条，共 6 条 sug），以及 §4 验收标准的 **AC-01 / AC-02 / AC-03 / AC-04 / AC-08（apply-all 部分）**：

- **现状**：契约 1-7 目前只在 done 阶段靠人工 `grep` 校验（`harness status --lint` 尚未实现）；stage 角色产出对人文档后没有自动 `harness validate` 兜底；辅助角色 `harness-manager.md` / `tools-manager.md` 等尚未纳入契约 7 id+title 硬门禁；regression 阶段的《回归简报.md》契约仅靠角色文件的对人文档模板约束，无自动化校验；`create_suggestion`（`workflow_helpers.py:3388`）写入 sug 文件时 frontmatter 只含 `id` / `created_at` / `status` 三字段，缺 `title` / `priority`（契约 6 规定的五字段中两个未落盘）。
- **apply-all path-slug bug（已定位）**：`apply_all_suggestions`（`workflow_helpers.py:3569`，3605 行）拼接 req_dir 时用未清洗的 title 直接 `f"{req_id}-{title}"`，与 `create_requirement`（3646 行）用 `_path_slug(requirement_title)` 清洗后的结果不一致 → title 含 `/` `（）` `空格` `'` `"` 等字符时路径 miss，`req_md.exists()` 为 False 使清单追加被静默跳过；但紧接着 `path.unlink()` 照常执行，结果 **sug body 文件已物理删除、清单却未写入**。req-31（批量建议合集（20条））的 sug-08..sug-27 共 20 个 sug body 就是被此 bug 删除的。
- **sug-11（`apply_all_suggestions` 同源隐患下沉到 `_path_slug` helper）**与本 bug 同源——本 change 一并合并。

## 3. Goal

把"契约 1-7 在产出即被自检 + apply-all 再不误删 body"作为本 change 的终点状态：

1. 新增 `harness status --lint`（或等价 `harness lint` 子命令），能扫描 `artifacts/{branch}/**/*.md` + `.workflow/state/sessions/**/session-memory.md` + `.workflow/state/action-log.md`，逐文件报告契约 7 违规（裸 id）。
2. stage 角色产出对人文档（`变更简报.md` / `实施说明.md` / `需求摘要.md` / `测试结论.md` / `验收摘要.md` / `回归简报.md` / `交付总结.md`）后自动触发 `harness validate`（契约 1-7 全量），违规时阻塞 stage 推进。
3. 辅助角色 `harness-manager.md` / `tools-manager.md` / `review-checklist.md` 补契约 7 硬门禁条款；所有辅助角色首次引用 id 时强制带 title。
4. `create_suggestion` frontmatter 补 `title` / `priority` 两字段（契约 6 五字段全量落盘）；缺字段直接 fail。
5. regression 阶段《回归简报.md》契约（契约 3-4）落地校验——由 `harness validate --regression` 子检查实现。
6. `apply_all_suggestions` path-slug 同源 bug 修复：拼接 req_dir 时统一调 `_path_slug` helper；回归单测覆盖"legacy title 含特殊字符 `'` `"` `/` `（）` `空格` 时 apply-all 不再静默删除 body"。

## 4. Requirement

- req-31（批量建议合集（20条））

## 5. Scope

### 5.1 In scope（包含）

- **`src/harness_workflow/workflow_helpers.py`**：
  - `apply_all_suggestions`（3569）：把 3605 行 `req_dir = resolve_requirement_root(root) / f"{req_id}-{title}"` 改为 `req_dir = resolve_requirement_root(root) / f"{req_id}-{_path_slug(title)}"`（或回退到 `load_requirement_runtime(root)["current_requirement_title"]` → 再 `_path_slug` 清洗）；若清洗后为空，回退到 `req_id` 目录名。
  - `apply_all_suggestions` 的 "追加清单失败时不 unlink" 防护：重构为"先追加清单成功 → 再 unlink body"的原子顺序（清单追加失败时 **不** 执行 `path.unlink()`，改为打印 stderr + return 1）。
  - `create_suggestion`（3388）：frontmatter 追加 `title` / `priority` 两字段；`title` 必填（调用方 `apply_suggestion` / CLI `harness suggest` 入口传入，无传入时 raise `SystemExit`）；`priority` 默认 `medium`，接受 `high` / `medium` / `low` 之一，非法值 raise。
- **新增 `src/harness_workflow/validate_contract.py`**（或合并到现有 `validate_human_docs.py`）：
  - `check_contract_7(root, paths)`：扫描指定文件集，每文件按行逐次匹配正则 `(?P<id>(req|chg|sug|bugfix|reg)-\d+)`，记首次命中；若首次命中行不包含 `（...）` 或 `(...)`，判定违规，返回 `list[ViolationRecord(file, line, id, excerpt)]`。
  - `check_contract_3_4_regression(root, reg_dir)`：校验 regression 目录下是否有《回归简报.md》且字段齐全。
  - 合规样本：已归档 req-30 下的所有对人文档应全部 pass。
- **`src/harness_workflow/cli.py`**：
  - `status_parser` 增加 `--lint` flag（或新增 `lint` 子命令）：调用 `check_contract_7` 并按"文件:行号"报告。
  - `validate_parser` 扩展 `--contract` flag（默认 all）+ `--regression` 子选项；被 stage 角色在对人文档产出后调用。
- **辅助角色契约扩展**：
  - `.workflow/context/roles/harness-manager.md`：新增"契约 7（id + title 硬门禁）"段，示例命令输出带 title；首次引用 id 时带 title。
  - `.workflow/context/roles/tools-manager.md`：新增契约 7 合规段；briefing / 推荐工具输出中首次 id 带 title。
  - `.workflow/context/checklists/review-checklist.md`：新增"契约 7 校验"清单项（grep 或 `harness status --lint` 绿）。
- **`.workflow/context/roles/regression.md`**：加"《回归简报.md》契约自检"退出条件——执行 `harness validate --regression` 得绿。
- **`.workflow/context/roles/stage-role.md`**：在"契约 7"末尾补充"产出对人文档后 MUST 触发 `harness validate --contract all`"子条款（契约 4 升格）。
- **单元测试 / 集成测**：
  - `tests/test_apply_all_path_slug.py`（新增）：
    - `test_apply_all_with_special_chars_in_title_does_not_delete_body`：fixture 建 2 条 sug，pack_title 含 `'` `"` `（）` `/` 空格，调用 `apply_all_suggestions` 前记下 sug 文件 mtime + inode，调用后断言：① 生成的 req_dir 路径可存在 + requirement.md 末尾含合并建议清单；② **或者**若路径生成仍失败，sug 文件 **仍然存在**（即不再"清单 miss + unlink 照常"）。
    - `test_apply_all_contract_atomic_order`：mock `req_md.write_text` 抛 OSError → 断言 sug 文件 `path.unlink()` **未被调用**。
    - `test_apply_all_uses_path_slug_helper`：spy `_path_slug`，断言拼接 req_dir 前被调用，入参 = pack_title。
  - `tests/test_create_suggestion_frontmatter.py`（新增）：
    - `test_create_suggestion_writes_title_and_priority`：调 `create_suggestion(root, content="...", title="t", priority="high")` → 断言生成文件 frontmatter 五字段齐全。
    - `test_create_suggestion_rejects_invalid_priority`：priority="urgent" → raise SystemExit。
    - `test_create_suggestion_requires_title`：title=None → raise SystemExit。
  - `tests/test_contract7_lint.py`（新增）：
    - `test_lint_reports_bare_id`：fixture 写一个首行裸 `req-99` 的 md → `check_contract_7` 返回 1 条违规，包含 file + line + id。
    - `test_lint_passes_on_id_with_title`：fixture 文档首行 `req-99（test title）` → 0 违规。
    - `test_lint_integration_harness_status_lint`：tempdir + `harness status --lint` 退出码 != 0 when 有违规。
  - `tests/test_regression_contract.py`（新增或扩展 `tests/test_regression_helpers.py`）：
    - `test_validate_regression_requires_回归简报_md`：reg-99 目录无此文件 → violation。
  - `tests/test_assistant_role_contract7.py`（新增）：grep `.workflow/context/roles/harness-manager.md` / `tools-manager.md` 含"契约 7"关键字 + 至少一条 `{id}（{title}）` 格式示范。

### 5.2 Out of scope（不包含）

- 不补历史文档的契约 7 违规（只校验、不自动回填；修复由各需求在 done 阶段人工处理）。
- 不改 `harness validate --human-docs` 已有的对人文档字段检查逻辑（只扩展新的 `--contract` flag）。
- 不做 `harness status --lint` 的 CI 集成（留给 chg-02 或后续 sug）。
- 不改 sug 编号分配器（由 chg-03 负责，sug-19）。
- 不做 `ff_mode` 自动关（chg-02 负责，sug-27）。
- 不处理 sug-13 / sug-14 / sug-17 / sug-19（由 chg-03 负责）。
- 不处理 sug-16 / sug-21 的 `_sync_stage_to_state_yaml` 盲区（由 chg-02 负责）。

## 6. 覆盖的 sug 清单（契约 7，id + title）

| sug id | title | 合入方式 |
|--------|-------|---------|
| sug-10（regression 阶段《回归简报.md》契约执行补强） | `harness validate --regression` + regression 角色退出条件新增 |
| sug-11（`apply_all_suggestions` 同源隐患下沉到 `_path_slug` helper） | `apply_all_suggestions` 调 `_path_slug`；合入 apply-all path-slug bug 修复 |
| sug-12（`create_suggestion` 写 sug 文件时补齐 title 与 priority frontmatter 字段） | `create_suggestion` frontmatter 五字段 + 必填校验 |
| sug-15（stage 角色产出对人文档后当场 `harness validate` 自检） | 新增 `harness validate --contract all` + stage-role.md 契约 4 升格 |
| sug-25（`harness status --lint` 自动化契约 7 校验） | 新增 `harness status --lint` + `check_contract_7` helper |
| sug-26（辅助角色（harness-manager / tools-manager / reviewer）契约 7 扩展） | 3 份角色 / 清单文件文档编辑 + 测试点名 |

同时合入：`apply_all_suggestions` path-slug 拼接 bug（非独立 sug；与 sug-11 同源）。

## 7. 覆盖的 AC

| AC | 说明 | 本 change 覆盖方式 |
|----|------|-----------------|
| AC-01 | `harness status --lint` CLI 实现 + 扫描违规报告 + 单测覆盖 | Step 3 + Step 5 + `tests/test_contract7_lint.py` |
| AC-02 | stage 角色产出后自动 `harness validate`，违规阻塞 | Step 2 + Step 6 + stage-role.md 契约 4 升格 |
| AC-03 | harness-manager / tools-manager / review-checklist 补契约 7 | Step 4 + `tests/test_assistant_role_contract7.py` |
| AC-04 | 《回归简报.md》契约补强 + `create_suggestion` frontmatter 五字段全量 | Step 1（frontmatter）+ Step 7（regression）+ 两组单测 |
| AC-08（apply-all 部分） | `apply_all_suggestions` 下沉到 `_path_slug` + apply-all path-slug bug 修复 + 回归单测 | Step 1（apply_all）+ `tests/test_apply_all_path_slug.py` |

## 8. DoD（Definition of Done）

1. **DoD-1**：`harness status --lint` 命令已落地，对一个 fixture 仓库（有裸 id 文档）退出码 != 0 并列出违规；对 req-30（slug 沟通可读性增强：全链路透出 title）归档目录 退出码 == 0。
2. **DoD-2**：`harness validate --contract all` 命令已落地；stage-role.md 契约 4 章节新增"产出对人文档后 MUST 触发 `harness validate --contract all`"条款（grep 命中）。
3. **DoD-3**：`apply_all_suggestions` 用 `_path_slug` 清洗 pack_title；新增 `tests/test_apply_all_path_slug.py` 的 3 条用例全部通过；回归：现有 `tests/test_suggest_cli.py` 零回归。
4. **DoD-4**：`create_suggestion` frontmatter 五字段齐全；`tests/test_create_suggestion_frontmatter.py` 的 3 条用例全部通过。
5. **DoD-5**：`harness-manager.md` / `tools-manager.md` / `review-checklist.md` 均含"契约 7"段与一条 `{id}（{title}）` 示例（grep 命中）。
6. **DoD-6**：`regression.md` 退出条件含"执行 `harness validate --regression` 得绿"；`tests/test_regression_contract.py` 新增断言用例全绿。
7. **DoD-综合**：全量 `pytest` 零回归（≥ 183 passed 基线不下降）；本 change 产出的 `change.md` / `plan.md` / `变更简报.md` / `实施说明.md` 首次引用 id 均带 title（契约 7 自证）。

## 9. 依赖 / 顺序

- **前置**：无（chg-01 是 req-31 的最前置 change）。
- **后置**：chg-02 / chg-03 / chg-04 / chg-05 产出的对人文档可直接被 chg-01 落地的 `harness status --lint` + `harness validate` 自证——这也是 chg-01 优先的原因。
- **内部 Step 顺序**（见 plan.md）：Step 1（apply-all bug + frontmatter）→ Step 2（validate 扩展）→ Step 3（status --lint）→ Step 4（辅助角色文档）→ Step 5/6/7（单测 + stage-role 契约升格 + regression 契约）。
- **临时防护**：chg-01 未落地前禁止 `harness suggest --apply-all`（避免二次删除新登记 sug）；本 change 落地后解禁。

## 10. 风险与缓解

| 风险 ID | 风险描述 | 缓解措施 |
|---------|---------|---------|
| R1 | `apply_all_suggestions` 重构为"先追加清单再 unlink"的原子顺序，若 req_md 追加写入抛 OSError 中断，此前删除的其他 sug（部分 pending）会处于"body 删 + 清单部分写入"的半态 | 用 "写临时文件 + 成功后原子 rename + 成功后才 unlink 所有 sug"的两阶段提交；失败路径保留所有 body |
| R2 | `check_contract_7` 正则漏报 / 误报（如行内字符串 `req-123` 是版本号而非 id） | 正则限定 `(req\|chg\|sug\|bugfix\|reg)-\d+` 前后加 `\b` 或上下文判定；fixture 合规样本 = 已归档 req-30 全树，保证 0 误报 |
| R3 | 辅助角色文档改动引起既有测试（`tests/test_ff_auto.py` / smoke 测试）的 grep 断言失败 | 本 change 只 **新增** 契约 7 段，不修改现有段；grep 断言不受影响 |
| R4 | `create_suggestion` 新增 `title` 必填破坏历史调用（如 `done.md` 转 suggest 池 / `apply_suggestion` 的 fallback 路径） | 通过 grep 确认所有调用点（`apply_suggestion` / `cli.py` 的 `harness suggest` 入口 / `done.md` 人工场景），在每个调用点显式传入 title；历史 `done-report.md` 提取 sug 候选时 fallback 取首行 |
| R5 | body 丢失的推断风险：sug-10 / sug-11 / sug-12 / sug-15 / sug-25 / sug-26 的 body 已被 apply-all bug 物理删除，仅靠 title 推断细节 | 每个 Step 标注"title 级推断 + git log commit hash"（见 plan.md 对应 Step）；若 executing 阶段发现遗漏重要细节，允许回补 sug（req-31 §3.1 已明确） |
