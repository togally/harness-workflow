# Change: chg-03（CTO 派发 briefing 注入 task_context_index + 快照落盘）

## 1. Goal

- 扩展 `_build_subagent_briefing`：在 `harness next --execute` / `harness ff --auto` / regression 派发路径注入 `task_context_index`（建议清单，≤ 8 条，每条含 path + reason）与 `task_context_index_file`（快照相对路径），同时将快照落盘到 `.workflow/state/sessions/{req-id}/task-context/{stage}-{seq}.md`。

## 2. Scope

### 包含

- 扩展 `src/harness_workflow/workflow_helpers.py::_build_subagent_briefing` 签名，新增参数 `task_context_index: list[dict]` / `task_context_index_file: str | None`，在 briefing JSON 中序列化为双字段。
- 新增 helper `_build_task_context_index(req_id, stage, role, repo_root) -> list[{path, reason}]`：
  - 读取 `.workflow/context/project-profile.md`（若存在）做领域加权；缺失时退化为"按 stage 选默认 role/experience/constraint 文件"。
  - 基础推荐集：`roles/{role}.md` / `experience/roles/{role}.md` / `constraints/{risk,boundaries}.md` / `checklists/review-checklist.md`。
  - 硬上限 8 条：超限截断并 stderr `warn: task_context_index truncated from N to 8`。
- 新增 helper `_write_task_context_snapshot(req_id, stage, index, repo_root) -> Path`：
  - 路径：`.workflow/state/sessions/{req_id}/task-context/{stage}-{seq}.md`，`{seq}` 按本 req 本 stage 已有快照数递增（从 01 起）。
  - frontmatter：`req_id` / `stage` / `ts`（ISO）/ `index_count`。
  - 正文：每条 `{path}: {reason}` 一行。
- 覆盖派发入口：`harness next --execute`、`harness ff --auto`、regression 相关派发均调用 index 构建 + 快照写盘 + briefing 注入。
- subagent C2 回退语义：当 briefing 中 `task_context_index` 路径不存在时，subagent 应静默回退到 `.workflow/context/index.md` 全量加载；**通过文档（`roles/stage-role.md` 或 `base-role.md` 加一段说明）+ 单测断言覆盖**，CLI 不对 subagent 做强约束。
- 归档路径保留：本 chg 不新增归档代码；现有 `harness archive` 会把 `.workflow/state/sessions/{req-id}/` 整体迁入 `artifacts/{branch}/requirements/{req-id}-{slug}/sessions/`，依赖既有 archive 测试断言。

### 不包含

- 不改 scanner 模块（chg-01（项目描述扫描器 + project-profile 落地））。
- 不改 `update_repo`（chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护））。
- 不新增 CLI 观测命令（如 `harness status --context-stats`）。
- 不改 tools-manager 推荐派发、done 六层回顾派发（留后续 req）。
- 不引入 LLM 调用（纯静态规则构建 index）。

## 3. Acceptance Criteria

- 覆盖 req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）的 **AC-03**：本仓 `harness next --execute` 打印的 subagent briefing JSON 含 `task_context_index` 字段，非空时每条形如 `{"path": "...", "reason": "..."}`，条数 ≤ 8。
- 覆盖 **AC-04**：subagent 按索引路径加载不存在时不报错，回退 `.workflow/context/index.md`；通过单测断言 + 文档说明覆盖。
- 覆盖 **AC-07**：派发后 `.workflow/state/sessions/{req-id}/task-context/{stage}-{seq}.md` 落盘；frontmatter 至少含 `req_id` / `stage` / `ts` / `index_count`；正文每行等价 briefing 内 `task_context_index` 条目；归档路径沿用既有 archive，无需新代码。
- 单测：briefing 字段存在性 / 上限截断 warn / 快照 frontmatter + 正文 / {seq} 递增 / profile 缺失退化 / subagent 路径不存在回退 六类。

## 4. Dependencies

- **前置**：req-32 的 chg-01（项目描述扫描器 + project-profile 落地）必须先合入（用于领域加权）。
- 与 chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护）无硬依赖（profile 缺失时退化即可），但本仓使用体验上应在 chg-02 合入后验证。
- 复用 `workflow_helpers._build_subagent_briefing` 现有调用点（已被 `harness next` / `ff` / regression 共享）。

## 5. Impact Surface

- 新增文件：`tests/test_task_context_index.py`、`tests/test_task_context_snapshot.py`。
- 修改文件：
  - `src/harness_workflow/workflow_helpers.py`：扩展 `_build_subagent_briefing`，新增 `_build_task_context_index` 与 `_write_task_context_snapshot`，在派发点串接（约 80-150 行）。
  - `.workflow/context/roles/stage-role.md`（或 `base-role.md`）：新增一段"task_context_index 回退语义"说明（约 10 行）。
  - 同步 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md`（或 base-role），保证 install/update 一致。
- 新增 helper：`_build_task_context_index` / `_write_task_context_snapshot` / `_next_task_context_seq`。

## 6. Risks

- index backfire（塞过多）→ 硬上限 8 + stderr warn。
- profile 缺失 → 退化为 stage 默认推荐，不崩。
- {seq} 并发冲突 → 本 CLI 单进程无并发，按目录扫描计数即可。
