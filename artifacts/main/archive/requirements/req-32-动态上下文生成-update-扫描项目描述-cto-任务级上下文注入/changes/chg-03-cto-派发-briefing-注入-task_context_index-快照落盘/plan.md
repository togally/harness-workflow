# Plan: chg-03（CTO 派发 briefing 注入 task_context_index + 快照落盘）

## 前置准备

- 已合入 req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）的 chg-01（项目描述扫描器 + project-profile 落地）。
- 读 `src/harness_workflow/workflow_helpers.py`：`_build_subagent_briefing`（行 ~5653）与所有调用点（行 ~5769 及 regression / ff 派发路径）。
- 读 `.workflow/context/roles/stage-role.md` / `base-role.md`，决定把 C2 回退语义写在哪一份（建议 `stage-role.md` 新增"task_context_index 回退语义"小节）。
- 跑基线：`pytest -q` 全绿。

## 步骤（严格 TDD 红绿）

### Step 1: briefing 签名扩展 + 基础字段注入

- 红：新增 `tests/test_task_context_index.py::test_briefing_contains_task_context_index` / `::test_briefing_contains_task_context_index_file`：调用 `_build_subagent_briefing(new_stage, req_id, req_title, task_context_index=[...], task_context_index_file="...")`，断言返回字符串（JSON/briefing 块）中含两字段。
- 绿：扩展 `_build_subagent_briefing` 签名，新增两个 kw-only 参数；在现有 briefing 模板末尾注入 `task_context_index` 数组 + `task_context_index_file` 字符串。
- 产物：`_build_subagent_briefing` 补丁 ~20 行 + 2 条测试。

### Step 2: `_build_task_context_index` helper（规则 + 8 条上限）

- 红：新增 `test_build_index_basic_stage_defaults`（profile 缺失场景，返回 role + experience + risk/boundaries + checklist ≥ 4 条且 ≤ 8 条）、`test_build_index_truncates_above_8`（mock 输入 12 条候选，断言返回 8 条 + stderr warn `task_context_index truncated from 12 to 8`）、`test_build_index_reads_project_profile_when_present`（profile 含 `stack_tags: [python+poetry]` 时，返回 index 含 Python 相关 experience 文件）。
- 绿：新增 `_build_task_context_index(req_id, stage, role, repo_root, stderr) -> list[dict]`：
  - 基础集合：stage → 默认文件清单（静态字典）。
  - 若 `.workflow/context/project-profile.md` 存在：`load_project_profile` → 读 `stack_tags` 做加权（如 `python+*` 追加 `experience/tool/python.md` 若存在）。
  - 截断 + warn 分支。
- 产物：新增 helper ~80 行 + 3 条测试。

### Step 3: `_write_task_context_snapshot` 落盘 + {seq} 递增

- 红：新增 `tests/test_task_context_snapshot.py::test_snapshot_frontmatter_and_body`（tmp 仓，调用 `_write_task_context_snapshot("req-99（测试伪 req）", "executing", [...], root)` 风格的 fixture id → 断言 `.workflow/state/sessions/<fixture-req-id>/task-context/executing-01.md` 存在，frontmatter 含四字段，正文每行 `{path}: {reason}`）、`::test_snapshot_seq_increments`（连续两次同 req 同 stage → `-01.md` + `-02.md`）、`::test_snapshot_different_stage_seq_independent`（`executing-01.md` 与 `testing-01.md` 并存）。
- 绿：新增 `_write_task_context_snapshot(req_id, stage, index, repo_root) -> Path`：扫描目录 → 下一个 seq → 写文件；frontmatter 用 YAML；正文按 `{path}: {reason}` 每行。
- 产物：新增 helper ~60 行 + 3 条测试。

### Step 4: 派发点串接（next --execute / ff --auto / regression）

- 红：新增 `tests/test_task_context_index.py::test_next_execute_emits_briefing_with_index`（集成测试，`harness next --execute` 的 stdout 含 `task_context_index` 字段 + 落盘快照路径存在）、`::test_ff_auto_emits_snapshot`（类似）、`::test_regression_dispatch_includes_index`（regression 派发路径覆盖）。
- 绿：在 `_build_subagent_briefing` 的所有调用点（行 ~5769 附近 + regression 派发 + ff 派发）前构建 index + 写快照 + 传入 briefing；相对路径相对 repo_root 存到 `task_context_index_file`。
- 产物：派发点补丁 ~40-60 行 + 3 条测试。

### Step 5: C2 回退语义（文档 + 单测）

- 红：新增 `::test_subagent_fallback_when_index_path_missing`（mock briefing 含一条不存在路径 `.workflow/context/does-not-exist.md` → 约定的 fallback helper / 文档断言：index 中不存在路径时 subagent 应读 `.workflow/context/index.md`；此处通过 `_resolve_task_context_paths(index, root)` 返回 `(existing, missing)` 分流）。
- 绿：新增 `_resolve_task_context_paths` helper 供未来 subagent lint 使用；同步在 `.workflow/context/roles/stage-role.md`（及 `assets/scaffold_v2/` 镜像）新增 "task_context_index 回退语义" 10 行小节；CLI 不强制。
- 产物：helper ~20 行 + 文档 ~10 行 + 1 条测试；修改 `scaffold_v2/.workflow/context/roles/stage-role.md` 保持一致。

## 验证

- 单元测试：
  - `pytest tests/test_task_context_index.py -v`（≥ 7 条用例全绿）
  - `pytest tests/test_task_context_snapshot.py -v`（≥ 3 条用例全绿）
- 集成：
  - 本仓 `harness next --execute` stdout 含 `task_context_index` 字段；`.workflow/state/sessions/req-32/task-context/executing-01.md` 落盘。
  - `harness ff --auto`（若当前状态允许）产生下一个 seq 快照。
  - `harness archive <req-32>` 后 `artifacts/main/requirements/req-32-.../sessions/task-context/*.md` 存在（验证既有归档不丢）。
- 回归：`pytest -q` 零回归。
- 契约自检：`harness validate --contract all` 绿。

## 产物清单

- 新增：
  - `tests/test_task_context_index.py`（~240 行，≥ 7 条用例）
  - `tests/test_task_context_snapshot.py`（~120 行，≥ 3 条用例）
- 修改：
  - `src/harness_workflow/workflow_helpers.py`（扩展 `_build_subagent_briefing` + 新增 `_build_task_context_index` / `_write_task_context_snapshot` / `_resolve_task_context_paths` + 派发点串接，约 200 行）
  - `.workflow/context/roles/stage-role.md` 新增回退语义小节
  - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md` 同步
- 测试：上述两文件。
