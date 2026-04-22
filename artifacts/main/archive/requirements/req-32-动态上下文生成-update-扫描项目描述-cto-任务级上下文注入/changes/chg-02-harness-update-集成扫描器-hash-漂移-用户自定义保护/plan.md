# Plan: chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护）

## 前置准备

- 已合入 req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）的 chg-01（项目描述扫描器 + project-profile 落地）。
- 读 `src/harness_workflow/workflow_helpers.py`：`update_repo`（行 ~3249）、`_sync_requirement_workflow_managed_files`（行 ~2900）、`_is_user_authored`（行 ~2297）、`_managed_hash`（行 ~2239）。
- 跑基线：`pytest -q` 全绿；`harness update --dry-run`（若有）或实际执行后观察现状输出。

## 步骤（严格 TDD 红绿）

### Step 1: 首次生成 profile（update 末尾调用 scanner）

- 红：新增 `tests/test_update_project_profile.py::test_update_generates_profile_first_run`：使用 `tmp_path` 伪仓（含 pyproject.toml），调用 `update_repo(tmp_path, ...)`，断言 `.workflow/context/project-profile.md` 落盘且 frontmatter 含 `content_hash`。测试失败（update_repo 尚未接入）。
- 绿：在 `workflow_helpers.py::update_repo` 末尾新增内部函数 `_write_project_profile_if_changed(root, actions, stderr)`；首次写盘并 `actions.append("generated .workflow/context/project-profile.md")`。
- 产物：`update_repo` 末尾 ~15 行补丁 + 新增 helper ~30 行 + 测试用例 1。

### Step 2: hash 稳定 + 漂移 stderr 提示

- 红：新增 `test_update_profile_hash_stable_on_second_run`（两次 update，stderr 不含 "hash 漂移"）+ `test_update_profile_drift_on_pyproject_change`（第二次前修改 pyproject 的 dependency，stderr 匹配 `project-profile 已刷新（hash 漂移：[0-9a-f]{8}→[0-9a-f]{8}）`）。
- 绿：`_write_project_profile_if_changed` 读旧 profile 的 `content_hash` 字段 → 与新 hash 对比；一致则不写 + 不打印；不一致则覆盖写 + stderr 打印漂移行。
- 产物：helper 内新增 diff 分支 ~20 行 + 2 条测试。

### Step 3: 用户自定义 CLAUDE/AGENTS/SKILL 保护兜底测试

- 红：新增 `test_update_skips_user_authored_claude_md`（tmp 仓先 `harness install` → 用户改 CLAUDE.md 内容 → `harness update` → 断言 CLAUDE.md 未被覆盖 + stderr 含 `skip user-authored: CLAUDE.md`）。
  - 本条验证既有 `_is_user_authored` 在 update 路径下仍然生效；若已绿可标记为回归守护，不新增实现代码。
- 绿：确认 `_sync_requirement_workflow_managed_files` 已调用 `_is_user_authored`；若 stderr 消息缺失则补一条打印；若已具备则测试直接绿。
- 产物：0-10 行补丁 + 1 条守护测试。

### Step 4: SKILL.md 缺失兜底 + 旧 profile 损坏兜底

- 红：新增 `test_update_no_skill_md_ok`（仓内无 SKILL.md，update 不抛错）+ `test_update_profile_old_file_corrupt_rebuild`（旧 profile frontmatter 缺 `content_hash`，update 当作漂移重建）。
- 绿：`_write_project_profile_if_changed` 读旧 hash 失败时视为无旧 profile → 触发漂移打印并覆盖写；`_is_user_authored` 对缺失文件直接返回 False 路径已兜底。
- 产物：helper 兜底分支 ~10 行 + 2 条测试。

## 验证

- 单元测试：`pytest tests/test_update_project_profile.py -v`（≥ 5 条用例全绿）。
- 集成：在本仓根执行 `harness update`，第一次看到 `generated .workflow/context/project-profile.md`，第二次 stderr 静默；手动改 `pyproject.toml` 的某个依赖版本后再执行，stderr 出现 `project-profile 已刷新（hash 漂移：...→...）`。
- 回归：`pytest -q` 零回归。
- 契约自检：`harness validate --contract all` 绿。

## 产物清单

- 新增：`tests/test_update_project_profile.py`（~180 行，≥ 5 条用例）。
- 修改：`src/harness_workflow/workflow_helpers.py`（新增 `_write_project_profile_if_changed` + `update_repo` 末尾接入，约 50-70 行新增/修改）。
- 测试：上述测试文件。
