# Change: chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护）

## 1. Goal

- 将 req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）的 chg-01（项目描述扫描器 + project-profile 落地）产出的 `ProjectScanner` 集成进 `harness update`：生成/刷新 `project-profile.md`，实现 hash 漂移 stderr 提示，并确保 CLAUDE.md / AGENTS.md / SKILL.md 用户自定义不被覆盖。

## 2. Scope

### 包含

- 在 `src/harness_workflow/workflow_helpers.py::update_repo` 末尾调用 `build_project_profile(repo_root)`，落盘到 `.workflow/context/project-profile.md`。
- 实现 hash 漂移检测：读取旧 profile（若存在）的 `content_hash` → 与新 hash 对比 → 差异时 stderr 打印 `project-profile 已刷新（hash 漂移：<old8>→<new8>）`，一致时静默。
- 复用 `_is_user_authored` 判据（req-31（批量建议合集（20条））的 chg-03（CLI/helper 剩余修复）的 sug-14（用户自定义 CLAUDE/AGENTS/SKILL 保护））保护 `CLAUDE.md` / `AGENTS.md` / `SKILL.md`：若用户已自定义，update 跳过覆盖并 stderr 提示 `skip user-authored: <relative>`。
- 单元测试覆盖三类场景：① 首次生成（无旧 profile）② 二次执行 hash 不变（静默）③ 描述文件变更触发 hash 漂移 stderr；④ 用户自定义 CLAUDE.md 被跳过；⑤ SKILL.md 缺失时不报错。

### 不包含

- 不新建 scanner 模块本身（底座在 chg-01）。
- 不改 subagent briefing / 不落快照（chg-03（CTO 派发 briefing 注入 task_context_index + 快照落盘）负责）。
- 不新增 `harness update --scan` / `--check` flag；能力默认嵌入 `update` 主流程。
- 不扩展 `_is_user_authored` 判据本身（仅消费）。

## 3. Acceptance Criteria

- 覆盖 req-32 的 **AC-02**：本仓连续两次 `harness update`：第一次产生 profile，第二次 stdout/stderr 中不出现 "hash 漂移"；篡改描述文件（如 pyproject.toml）后第三次执行出现 `project-profile 已刷新（hash 漂移：...→...）`。
- 覆盖 req-32 的 **AC-05**：用户对 CLAUDE.md 做非模板修改后，`harness update` 不覆盖该文件，stderr 含 `skip user-authored: CLAUDE.md`。
- 单元测试：hash 稳定 / 漂移 / 用户自定义跳过 / 旧 profile 缺失兜底 四类各至少一条。

## 4. Dependencies

- **前置**：req-32 的 chg-01（项目描述扫描器 + project-profile 落地）必须先合入。
- 复用 `workflow_helpers._is_user_authored` / `_managed_hash` / `_managed_file_contents`。
- 复用现有 `update_repo` 末尾 `_sync_requirement_workflow_managed_files` 调用后的扩展点。

## 5. Impact Surface

- 新增文件：`tests/test_update_project_profile.py`。
- 修改文件：
  - `src/harness_workflow/workflow_helpers.py`：`update_repo` 末尾新增 scanner 调用 + hash 漂移检测分支（约 30-60 行）。
- 新增/扩展 helper：`_write_project_profile_if_changed(root, actions)`（内部函数，封装 hash 对比 + 写盘 + stderr 提示）。

## 6. Risks

- update 频繁触发 scanner 性能下降 → scanner 设计为纯静态解析，整仓耗时 < 100ms；测试可加 perf sanity。
- 用户自定义检测误伤 → 仅使用 `_is_user_authored`（hash 对比既有模板），不做新判据。
