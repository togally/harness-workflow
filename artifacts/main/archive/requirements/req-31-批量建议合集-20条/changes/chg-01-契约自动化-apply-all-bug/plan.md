# Change Plan

> 父 change：chg-01（契约自动化 + apply-all bug）/ req-31（批量建议合集（20条））

## 1. Development Steps

### Step 1：修复 `apply_all_suggestions` path-slug + frontmatter 五字段（sug-11 + sug-12 + apply-all bug）

- **操作意图**：把 apply-all bug 根治 + `create_suggestion` 五字段补齐，作为 chg-01 的基石（其他 Step 的 fixture 依赖这两处 helper 行为）。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py`（`apply_all_suggestions` 3569、`create_suggestion` 3388、`_path_slug` 2446）。
- **关键代码思路**（伪代码）：
  ```python
  # apply_all_suggestions 3605 行改造
  slug_part = _path_slug(title)  # 与 create_requirement 3646 行同源
  req_dir = resolve_requirement_root(root) / (f"{req_id}-{slug_part}" if slug_part else req_id)
  req_md = req_dir / "requirement.md"

  # 原子化：先写临时清单、成功才 unlink body
  if not req_md.exists():
      print(f"[apply_all] ERROR: req_md missing at {req_md}; aborting before unlink", file=sys.stderr)
      return 1
  try:
      tmp = req_md.with_suffix(".md.tmp")
      tmp.write_text(req_md.read_text(encoding="utf-8") + "\n".join(lines), encoding="utf-8")
      tmp.replace(req_md)  # 原子 rename
  except OSError as e:
      print(f"[apply_all] ERROR: append failed ({e}); leaving bodies intact", file=sys.stderr)
      return 1
  # 只有写入成功才进入 unlink 循环
  for path, suggest_id, _ in pending:
      path.unlink()
      ...

  # create_suggestion 3388 改造
  def create_suggestion(root, content, title=None, priority="medium"):
      if not title or not title.strip():
          raise SystemExit("Suggestion title is required (契约 6).")
      if priority not in ("high", "medium", "low"):
          raise SystemExit(f"Invalid priority: {priority}")
      frontmatter = (
          f"---\nid: {suggest_id}\ntitle: {json.dumps(title, ensure_ascii=False)}\n"
          f"status: pending\ncreated_at: {date.today().isoformat()}\n"
          f"priority: {priority}\n---\n\n{content}\n"
      )
  ```
- **body 丢失补位**：sug-11 body 已被 apply-all bug 删除；title 级推断依据 = req-31（批量建议合集（20条））requirement.md §6 清单"`apply_all_suggestions` 同源隐患下沉到 `_path_slug` helper" + git log commit `2dd9db5`（slug 清洗与截断 sug 归档 TDD 9 用例）/ `90a75f6`（update_repo 幂等性）附近的实现线索。sug-12 title 明确指出补 "title 与 priority"，推断来源同上 + 契约 6 五字段定义。
- **验证方式**：
  - 新增 `tests/test_apply_all_path_slug.py`：3 条用例（见 change.md §5.1）。
  - 新增 `tests/test_create_suggestion_frontmatter.py`：3 条用例。
  - `pytest tests/test_suggest_cli.py tests/test_apply_all_path_slug.py tests/test_create_suggestion_frontmatter.py -v` 全绿。

### Step 2：扩展 `harness validate --contract all` + `--regression` 子选项（sug-15 + sug-10）

- **操作意图**：stage 角色产出对人文档后可一键自检契约 1-7；regression 阶段可单独校验《回归简报.md》契约。
- **涉及文件**：新增 `src/harness_workflow/validate_contract.py`；改 `src/harness_workflow/cli.py`（`validate_parser`）；改 `src/harness_workflow/validate_human_docs.py`（若合并 contract 7 check 到已有 runner）。
- **关键代码思路**：
  ```python
  # validate_contract.py
  @dataclass
  class ViolationRecord:
      file: Path; line: int; work_item_id: str; excerpt: str
  def check_contract_7(root: Path, paths: Iterable[Path]) -> list[ViolationRecord]:
      pattern = re.compile(r"\b(?P<id>(?:req|chg|sug|bugfix|reg)-\d+)\b")
      seen: set[tuple[Path, str]] = set()
      violations = []
      for p in paths:
          for lineno, line in enumerate(p.read_text(...).splitlines(), 1):
              for m in pattern.finditer(line):
                  wid = m.group("id")
                  if (p, wid) in seen: continue
                  seen.add((p, wid))
                  # 首次命中：检测同一行是否有 `（...）` 或 `(...)` 紧邻 id
                  if not _has_adjacent_title(line, m.start(), m.end()):
                      violations.append(ViolationRecord(p, lineno, wid, line.strip()))
      return violations
  def check_contract_3_4_regression(root, reg_dir):
      brief = reg_dir / "回归简报.md"
      if not brief.exists(): return [f"missing 回归简报.md in {reg_dir}"]
      # 字段校验：标题 / 问题 / 诊断结论 / 路由方向 / 验证方式 五段齐全
  ```
  - `cli.py` `validate_parser` 增加 `--contract {all,7,regression}`；routing 到 `validate_contract.run_cli(...)`。
- **body 丢失补位**：sug-15 body 丢失；title "产出对人文档后当场 `harness validate` 自检" 推断来源 = req-31 requirement.md §4 AC-02（显式要求 1 集成测）+ `.workflow/context/roles/stage-role.md` 契约 4 + session-memory.md `.workflow/state/sessions/req-30/session-memory.md`（同批次 sug）。sug-10 推断 = 《回归简报.md》在 `stage-role.md` 契约 3 已明确 regression 粒度，需要补字段校验；commit `015b9d3`（req-29 ff --auto）附近的 validate_human_docs 扩展模式可参考。
- **验证方式**：
  - 新增 `tests/test_contract7_lint.py` 的 `test_lint_reports_bare_id` + `test_lint_passes_on_id_with_title`（Step 3 复用）。
  - 新增 `tests/test_regression_contract.py::test_validate_regression_requires_回归简报_md`。

### Step 3：实现 `harness status --lint`（sug-25）

- **操作意图**：暴露 CLI 入口供 agent / done 阶段调用。
- **涉及文件**：`src/harness_workflow/cli.py`（`status_parser` 加 `--lint` flag）；`src/harness_workflow/workflow_helpers.py`（新增 `workflow_status_lint(root)` 或在 `workflow_status` 加 `lint=False` 参数）。
- **关键代码思路**：
  ```python
  status_parser.add_argument("--lint", action="store_true", help="Scan contract 7 violations.")
  # workflow_helpers.workflow_status_lint(root):
  targets = list(root.glob("artifacts/*/**/*.md")) + \
            list((root / ".workflow/state/sessions").rglob("session-memory.md")) + \
            [root / ".workflow/state/action-log.md"]
  violations = check_contract_7(root, [p for p in targets if p.exists()])
  for v in violations:
      print(f"{v.file.relative_to(root)}:{v.line}: contract-7 bare id {v.work_item_id} — {v.excerpt}")
  return 0 if not violations else 1
  ```
- **验证方式**：
  - `tests/test_contract7_lint.py::test_lint_integration_harness_status_lint`：subprocess 或直接 call `main(['status', '--lint'])`，断言非零退出 + stdout 含 `contract-7 bare id`。

### Step 4：辅助角色文档契约 7 扩展（sug-26）

- **操作意图**：把契约 7 从"stage 角色强制"扩展到辅助角色（harness-manager / tools-manager / reviewer）。
- **涉及文件**：
  - `.workflow/context/roles/harness-manager.md`
  - `.workflow/context/roles/tools-manager.md`
  - `.workflow/context/checklists/review-checklist.md`
- **关键代码思路**：
  - 三个文件末尾各加一节"### 契约 7（id + title 硬门禁）"，内容参照 `stage-role.md` 契约 7（首次引用带 title / 同上下文简写 / pending-title fallback），并提供至少 1 条 `{id}（{title}）` 示例。
  - 本 change.md 首次引用 req-31 / req-30 / sug-10..26 / bugfix-3 / chg-01 均带 title（自证）。
- **body 丢失补位**：sug-26 title 明确辅助角色列表 = harness-manager / tools-manager / reviewer；推断来源 = `.workflow/context/roles/index.md`（辅助角色索引）+ stage-role.md 契约 7。
- **验证方式**：
  - 新增 `tests/test_assistant_role_contract7.py`：grep 三个文件包含"契约 7"字符串 + 至少一个形如 `req-XX（...）` 的示例。

### Step 5：stage-role.md 契约 4 升格（sug-15 配套）

- **操作意图**：把"产出对人文档后 MUST 触发 `harness validate --contract all`"升格为硬门禁条款，使 stage 角色不能绕过自检。
- **涉及文件**：`.workflow/context/roles/stage-role.md`（契约 4 章节末尾）。
- **关键代码思路**：
  - 在"契约 4：硬门禁"段末尾增加子条款：
    > "每个 stage 角色在其 SOP 交接步骤之前，**必须**执行 `harness validate --contract all`；若输出违规，阻塞 stage 推进。退出条件清单中新增'已执行 `harness validate --contract all` 并得绿'。"
  - 7 个 stage 角色文件的"退出条件"段同步加一条 checklist。
- **验证方式**：
  - grep `.workflow/context/roles/stage-role.md` 命中"harness validate --contract"。
  - grep 7 个 stage 角色文件各自 `退出条件` 下命中相同字符串。

### Step 6：regression 角色契约补强（sug-10 配套）

- **操作意图**：`regression.md` 退出条件加"`harness validate --regression` 得绿"。
- **涉及文件**：`.workflow/context/roles/regression.md`。
- **关键代码思路**：
  - 在"退出条件"段加：`- [ ] 已执行 harness validate --regression 得绿（《回归简报.md》字段齐全）`。
  - 《回归简报.md》模板字段（问题摘要 / 诊断结论 / 根因 / 路由方向 / 验证方式）对齐 `stage-role.md` 契约 3。
- **验证方式**：
  - `tests/test_regression_contract.py::test_regression_md_exit_contains_validate_regression`（grep 断言）。

### Step 7：全量回归 + 契约 7 自证

- **操作意图**：确认 chg-01 自身产出首次引用工作项 id 时全部带 title；全量测试零回归。
- **涉及文件**：本 chg-01 的 `change.md` / `plan.md` / `变更简报.md`（executing 阶段产出）/ `实施说明.md`（executing 阶段产出）。
- **关键代码思路**：
  - executing 阶段交付前执行 `harness status --lint` on `artifacts/main/requirements/req-31-批量建议合集-20条/changes/chg-01-契约自动化-apply-all-bug/*.md`，退出码 0。
- **验证方式**：
  - `pytest` 全量绿；`harness status --lint` 对 req-31 chg-01 目录 0 违规。

## 2. Verification Steps

### 2.1 单测 / 集成测清单

| 测试文件 / 用例 | 意图 | 关键断言 |
|----------------|------|---------|
| `tests/test_apply_all_path_slug.py::test_apply_all_with_special_chars_in_title_does_not_delete_body` | 验证 apply-all bug 已修复 | title 含 `'` `"` `/` `（）` 空格时：req_md 含合并建议清单；或 path 失败时 sug body 仍存在 |
| `tests/test_apply_all_path_slug.py::test_apply_all_contract_atomic_order` | 写清单失败时 unlink 不触发 | mock OSError → `path.unlink` call_count == 0 |
| `tests/test_apply_all_path_slug.py::test_apply_all_uses_path_slug_helper` | 确认 `_path_slug` 被调用 | spy.assert_called_with(pack_title) |
| `tests/test_create_suggestion_frontmatter.py::test_create_suggestion_writes_title_and_priority` | 五字段落盘 | frontmatter grep 命中 `id` + `title` + `status` + `created_at` + `priority` |
| `tests/test_create_suggestion_frontmatter.py::test_create_suggestion_rejects_invalid_priority` | priority 合法性校验 | raise SystemExit |
| `tests/test_create_suggestion_frontmatter.py::test_create_suggestion_requires_title` | title 必填校验 | raise SystemExit |
| `tests/test_contract7_lint.py::test_lint_reports_bare_id` | 违规检测 | 1 条 ViolationRecord，字段齐全 |
| `tests/test_contract7_lint.py::test_lint_passes_on_id_with_title` | 合规样本 | 0 违规 |
| `tests/test_contract7_lint.py::test_lint_integration_harness_status_lint` | CLI 入口集成测 | 退出码 != 0 + stdout 含"contract-7" |
| `tests/test_regression_contract.py::test_validate_regression_requires_回归简报_md` | 缺文件违规 | 返回 "missing 回归简报.md" |
| `tests/test_assistant_role_contract7.py::test_harness_manager_md_contains_contract_7` | 文档扩展 | grep 命中"契约 7" |
| `tests/test_assistant_role_contract7.py::test_tools_manager_md_contains_contract_7` | 文档扩展 | 同上 |
| `tests/test_assistant_role_contract7.py::test_review_checklist_contains_contract_7` | 清单扩展 | 同上 |

### 2.2 Manual smoke verification

- 在 tmp fixture 仓库：
  1. `harness install` → `harness requirement "smoke title"` → 登记 3 条 sug（`harness suggest "..."`）→ `harness suggest --apply-all "pack title / with 'special'"` → 断言 req_dir 存在 + requirement.md 含清单。
  2. `harness status --lint` → 退出码 0（fixture 无裸 id）。
  3. 手工改一个对人文档插入裸 `req-01`（不带 title）→ `harness status --lint` → 退出码 != 0 + 定位到违规行。

### 2.3 AC Mapping

- AC-01 → Step 2 + Step 3 + `tests/test_contract7_lint.py`。
- AC-02 → Step 2 + Step 5 + stage-role.md 契约 4 升格。
- AC-03 → Step 4 + `tests/test_assistant_role_contract7.py`。
- AC-04 → Step 1（frontmatter）+ Step 2（validate --regression）+ Step 6（regression.md 退出条件）+ 对应单测。
- AC-08（apply-all 部分）→ Step 1 + `tests/test_apply_all_path_slug.py`。

## 3. body 丢失补位专段

| sug id | title | 推断来源 |
|--------|-------|---------|
| sug-10（regression 阶段《回归简报.md》契约执行补强） | `stage-role.md` 契约 3（regression 粒度）+ req-31 requirement.md §4 AC-04 + 同批次 req-30 session-memory |
| sug-11（`apply_all_suggestions` 同源隐患下沉到 `_path_slug` helper） | 直接源码定位（`workflow_helpers.py:3605` vs `create_requirement` 3646 行）+ commit `2dd9db5`（slug 清洗）/ `90a75f6`（update_repo 幂等） |
| sug-12（`create_suggestion` 写 sug 文件时补齐 title 与 priority frontmatter 字段） | 契约 6 五字段明确列出 + `create_suggestion` 当前实现（`workflow_helpers.py:3400`）frontmatter 只有 3 字段 |
| sug-15（stage 角色产出对人文档后当场 `harness validate` 自检） | req-31 requirement.md §4 AC-02 明确要求 + `stage-role.md` 契约 4 升格语境 |
| sug-25（`harness status --lint` 自动化契约 7 校验） | req-31 requirement.md §4 AC-01 + `render_work_item_id` helper（chg-02 之前落地）可复用 |
| sug-26（辅助角色（harness-manager / tools-manager / reviewer）契约 7 扩展） | `.workflow/context/index.md` 辅助角色索引 + stage-role.md 契约 7 规则复制 |

## 4. 回滚策略

- **粒度**：按 Step 1-7 拆分 git 提交；每个 Step 一个 commit，独立可 revert。
- **回滚触发**：
  - Step 1 重构后若 `tests/test_suggest_cli.py` 或 `tests/test_apply_all_path_slug.py` 失败 → revert Step 1；保守策略：只加 `_path_slug` 不改原子顺序，先单独修 path 拼接。
  - Step 2 新 validate runner 若阻塞其他 stage（`tests/test_smoke_req*.py` 回归）→ 把 `--contract all` 从 stage 角色退出条件移除，仅提供 CLI 手工入口。
  - Step 4 辅助角色文档若误改现有条款导致 `tests/test_cli.py` 回归 → revert 文档编辑即可（无代码耦合）。
- **兜底**：所有修改集中在 `workflow_helpers.py` + 新增 `validate_contract.py` + 新增 tests + 辅助角色 md 文件；`git revert` 单次回滚即可。

## 5. 执行依赖顺序

1. Step 1（apply-all + frontmatter）**最先**——为 Step 2-7 的 fixture 提供正确 helper。
2. Step 2（validate 扩展）依赖 Step 1 的 `_path_slug` 行为稳定。
3. Step 3（status --lint）依赖 Step 2 的 `check_contract_7` helper。
4. Step 4（辅助角色文档）独立，可与 Step 2/3 并行。
5. Step 5（stage-role 契约 4 升格）依赖 Step 2 的 `harness validate --contract all` CLI 落地。
6. Step 6（regression.md 契约）依赖 Step 2 的 `--regression` flag 落地。
7. Step 7（回归 + 自证）最后。

## 6. 风险表

| 风险 ID | 风险描述 | 缓解措施 |
|---------|---------|---------|
| R1 | apply_all 原子重构引入 "半态" 风险（req_md 写成功但后续 unlink 某 sug 失败） | 原子 rename + `unlink` 失败仅打印 stderr 不回滚（已删的已删，清单已登记，可接受）；保留 `failed_delete` 列表 return 1 |
| R2 | `check_contract_7` 正则匹配大文件（如历史 done-report）性能问题 | 限定扫描范围只包含 `artifacts/{branch}/**/*.md` + sessions + action-log；> 10 MB 文件跳过并打印 warning |
| R3 | body 丢失导致 Step 2 / 6 的校验字段与原 sug 设想不符（sug-10 的回归简报字段可能更严格） | executing 阶段若发现遗漏，回补 sug（req-31 §3.1 允许）；字段取 `stage-role.md` 契约 3 的最小集作为 baseline |
| R4 | 辅助角色文档更新触发 `tests/test_cli.py` 或 hook 校验失败（existing 文档断言过严） | grep 先确认现有测试对这些文件是否有硬编码行号断言；若有，同步更新断言 |
| R5 | `harness status --lint` 对已归档历史文档报大量违规 | 扫描范围默认仅 `artifacts/{branch}/**/*.md`，不含 `artifacts/{branch}/archive/`（除非显式 `--include-archive`）；契约 7 只对"本次提交之后"新增文档生效（stage-role.md 契约 7 fallback 条款已明确） |
