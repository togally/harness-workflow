# Change Plan — chg-01（apply / apply-all CLI 路径与内容修复）

> 所属 req：req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症））
> 关联 sug：sug-43（apply-all artifacts/ 旧路径检查导致 abort）/ sug-44（apply 取 content 头当 title + rename 不同步 runtime）/ sug-45（apply 单 sug 不真填 requirement.md + rename 漏 .workflow/flow/）
> 关联 bugfix：bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））

## 1. 目标

让 `harness suggest --apply-all` 在 bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） 落地后能正常 unlink 全部 sug + 真把 sug 内容合并写入新 req 的 `requirement.md`；同时把 `harness suggest --apply <id>` 单 sug 路径修到位（取 sug.title 当 req title，并真把 sug.body 写入 requirement.md），AC-01 + AC-02 一并闭环。

## 2. 影响文件列表

- `src/harness_workflow/workflow_helpers.py`
  - `apply_all_suggestions`（line 4489 起）：构造 `req_md` 时按 `_use_flow_layout(req_id)` 分支落 `.workflow/flow/requirements/{dir_name}/requirement.md`（True）或既有 `resolve_requirement_root(root)/{dir_name}/requirement.md`（False，legacy 兼容）。
  - `apply_suggestion`（line 4300 起）：(a) `title` 从 `state.get("title", "").strip() or first_line[:60]` 优先取 sug frontmatter title；(b) `create_requirement` 成功后调用新私有 helper 把 sug.body 写入新 req requirement.md。
  - 新增私有 helper `_append_sug_body_to_req_md(root, req_id, dir_name, sug_id, sug_title, sug_body) -> Path`：apply / apply_all 同源调用，单点维护路径解析 + body append 逻辑（追加 `## 合并建议清单 / ### {sug_id}（{sug_title}）` 段）。
- `tests/test_apply_all_path_slug.py`：扩 TC-01 / TC-02 / TC-03（apply-all 后 bugfix-6 路径 + legacy req-id 兼容 + req_md 缺失不 unlink）。
- 新增 `tests/test_apply_suggestion_content.py`：TC-04 / TC-05 / TC-06（单 sug title 取值 + body 真写入 + 后 bugfix-6 路径落位）。

## 3. 实施步骤

1. **加 helper 骨架**：在 `workflow_helpers.py` 紧邻 `apply_suggestion` 之上新增 `_append_sug_body_to_req_md`，输入 `(root, req_id, dir_name, sug_id, sug_title, sug_body)`，按 `_use_flow_layout(req_id)` 解析 `req_md` 路径，存在则在文末追加 `## 合并建议清单` 段（多次调用幂等聚合到同一段下），返回写入路径；不存在则 raise FileNotFoundError 由调用方决定是否 abort。
2. **改 `apply_all_suggestions`**：把现有 `req_md = resolve_requirement_root(...) / dir_name / "requirement.md"` 替换成对每个 sug 调 `_append_sug_body_to_req_md(...)`；保留 "req_md 不存在 → log ERROR + return non-zero + 不 unlink sug" 防御逻辑。
3. **改 `apply_suggestion`**：(a) `title` 计算行改为 `title = (state.get("title") or "").strip() or first_line[:60]`；(b) 在 `create_requirement` 成功路径后立即调用 `_append_sug_body_to_req_md(root, new_req_id, new_dir_name, suggest_id, title, body)`；写入失败仍要 unlink 当前 sug（与 apply_all 行为对齐，避免半挂）。
4. **跑 pytest**：`pytest tests/test_apply_all_path_slug.py tests/test_apply_suggestion_content.py -v` 全绿；再跑全量 `pytest -q` 确认无回归。
5. **手跑端到端**：在本仓库复现 `harness suggest --apply-all`（pending sug 池 ≥ 1 条）→ 验证 sug 全 unlink + 新 req `requirement.md` 含 `## 合并建议清单` 段。
6. **commit**：commit message `fix(chg-01): apply / apply-all CLI 路径与内容修复（req-44 / 修复 sug-43+sug-44+sug-45）` —— 契约 7 + 硬门禁六合规。

## 4. 测试用例设计（bugfix-6 B1 强制段）

> regression_scope: targeted
> 波及接口清单：
> - `src/harness_workflow/workflow_helpers.py::apply_all_suggestions`
> - `src/harness_workflow/workflow_helpers.py::apply_suggestion`
> - `src/harness_workflow/workflow_helpers.py::_append_sug_body_to_req_md`（新增）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 apply-all 后 bugfix-6 路径成功 | 1 个 pending sug，新 req-id ≥ 41，仅 `.workflow/flow/requirements/{slug}/` 含空 requirement.md | exit 0；sug 文件被 unlink；该 requirement.md 含 `## 合并建议清单` + sug body marker | AC-01 | P0 |
| TC-02 apply-all legacy req-id 路径仍兼容 | 模拟 `_use_flow_layout` 返回 False（req-id ≤ 40） | exit 0；body 写入 `artifacts/{branch}/requirements/{slug}/requirement.md`；不动 flow/ | AC-01 | P1 |
| TC-03 apply-all req_md 不存在不 unlink | flow/ 与 artifacts/ 两处 requirement.md 均缺失 | exit ≠ 0；sug 文件保留；stderr 含 ERROR | AC-01 | P0 |
| TC-04 apply 单 sug 取 sug.title 当 req title | sug frontmatter `title: X`，content 首行 `# Y` | 新 req 目录 slug 来源 'X'；runtime current_requirement_title='X' | AC-02 | P0 |
| TC-05 apply 单 sug 真写入 requirement.md | sug.body 含 `BODY-MARKER-XYZ` | 新 req requirement.md 文末含 `## 合并建议清单` + `BODY-MARKER-XYZ` | AC-02 | P0 |
| TC-06 apply 单 sug 后 bugfix-6 路径落位 | 新 req-id ≥ 41 | requirement.md 落在 `.workflow/flow/requirements/{slug}/`，artifacts/ 不残留 sug body | AC-02 | P0 |

> AC 映射：AC-01 → TC-01/02/03；AC-02 → TC-04/05/06；AC-04（scaffold mirror）本 chg = no-op；AC-05（e2e 用例数）本 chg 贡献 6 条 ≥ 2 条。

## 5. 验证方式

- 静态：`pytest tests/test_apply_all_path_slug.py tests/test_apply_suggestion_content.py -v` 全绿；`pytest -q` 全量无回归。
- 动态（端到端）：本仓库构造 ≥ 1 条 pending sug → `harness suggest --apply-all` → grep `.workflow/flow/requirements/{new-slug}/requirement.md` 含 `## 合并建议清单`；`ls .workflow/flow/suggestions/sug-*.md` 应不含被 apply 的 sug。
- 契约：交付前必跑 `harness validate --human-docs` + `harness validate --contract test-case-design-completeness`，exit 0 才允许 PASS。

## 6. 回滚方式 + scaffold mirror + 契约 7 注意点

### 回滚

- `git revert <chg-01 commit sha>` 即可回到 bugfix-6 后未修复状态（`apply-all` 仍 abort，但不引入新回归）。
- 数据回滚：若已有 sug 被 unlink 且新 req requirement.md 写入异常，可从 `.workflow/state/sessions/{req-id}/` 重建，或人工把 sug 文件从 git 历史 checkout 回 `.workflow/flow/suggestions/`。

### scaffold mirror（AC-04）

- 本 chg 仅改 `src/` + `tests/`，不动 `.workflow/` 文档树或 scaffold 模板；scaffold mirror = **no-op**，AC-04 在本 chg 范围内自动满足。

### 契约 7 + 硬门禁六注意点

- 本 plan.md / 同 chg 目录下 `change.md` / commit message / TaskList / session-memory 内首次引用 sug-43（apply-all artifacts/ 旧路径检查导致 abort）/ sug-44（apply 取 content 头当 title + rename 不同步 runtime）/ sug-45（apply 单 sug 不真填 requirement.md + rename 漏 .workflow/flow/）/ bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））/ req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） 必带括号简短描述；批量列举 ≥ 2 个 id 时禁止裸数字扫射。
- testing 用例命名 `TC-01 apply-all 后 bugfix-6 路径成功` 自带语义描述，符合密集展示反向豁免子条款。
