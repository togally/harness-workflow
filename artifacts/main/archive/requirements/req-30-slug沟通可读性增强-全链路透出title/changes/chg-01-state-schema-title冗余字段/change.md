# Change

## 1. Title

chg-01（state schema — title 冗余字段）：runtime.yaml / state yaml 扩展 `*_title` 并由统一写入 helper 维护

## 2. Background

源自 req-30（slug 沟通可读性增强：全链路透出 title）方案 B 的 **L3 层目标**（Runtime / state yaml 字段）与 **AC-05 / AC-06**：

- 现状：`.workflow/state/runtime.yaml` 仅存 `current_requirement` / `current_regression` / `locked_requirement` 等 id 字段，不含 title；subagent 拿到 runtime.yaml 后必须再打开 `state/requirements/{id}.yaml` 才能读到 title，增加一次 IO 且 CLI 渲染无数据源。
- `state/requirements/*.yaml` 已有 `title` 字段（如 `req-24.yaml` / `req-30.yaml`），但并非所有活跃文件都保证非空、且无统一的写入 helper 约束"新建时必须带 title"。
- `state/bugfixes/` 当前为空，但 helper（如 `create_bugfix`）未来写入时也必须同步带 title。

## 3. Goal

在**不破坏现有路径与字段结构**的前提下，把 title 作为一等元数据落到 state 层：

- `runtime.yaml` 新增三个冗余字段：`current_requirement_title` / `current_regression_title` / `locked_requirement_title`（缺省空字符串，null-safe）。
- `state/requirements/*.yaml` 的 `title` 字段对**活跃需求**（active_requirements 列表中的条目）非空；schema 保持向后兼容，历史归档 yaml 不强制回填。
- `state/bugfixes/*.yaml` 写入路径同步带 `title`。
- 在 `src/harness_workflow/workflow_helpers.py` 中引入统一的 "title 同步写入 helper"（方案建议：`_resolve_title_for_id(root, work_item_id)` + 改造 `save_requirement_runtime` 在 ordered_keys 中加入三个 `*_title` 字段），避免所有调用方各自实现。
- 当前活跃 3 个需求（req-28 / req-29 / req-30）一次性回填 `state/requirements/*.yaml` 的 `title`。

## 4. Requirement

- `req-30`

## 5. Scope

### 5.1 In scope（包含）

- **`src/harness_workflow/workflow_helpers.py`**：
  - `DEFAULT_STATE_RUNTIME` 增加三个 `*_title` 字段（默认空串）。
  - `save_requirement_runtime` 的 `ordered_keys` 白名单加入 `current_requirement_title` / `current_regression_title` / `locked_requirement_title`（位置紧邻对应 id 字段）。
  - 新增内部 helper `_resolve_title_for_id(root: Path, work_item_id: str) -> str`：按 id 前缀分流到 `state/requirements/` 或 `state/bugfixes/` 对应 yaml 的 `title` 字段；找不到时返回空串，不抛异常。
  - 改造所有写 `runtime["current_requirement"] = ...` / `runtime["current_regression"] = ...` / `runtime["locked_requirement"] = ...` 的写入点（见 `workflow_helpers.py` grep 命中行：约 2412 / 2424 / 3516 / 3603 / 3723 / 3865 / 3873 / 3885 / 3892 / 3900 / 4926）——在每个写入点紧随其后写入对应 `*_title`（用 `_resolve_title_for_id` 读取），保持成对原子写入。
  - `create_requirement` / `create_bugfix` / `harness_regression` 等 helper 在新建 id 时写 state yaml 必须同步 `title` 字段；title 为空或未传参时 raise `SystemExit` 带明确错误。
- **`state/requirements/req-28-*.yaml` / `state/requirements/req-29-*.yaml` / `state/requirements/req-30-*.yaml`**：活跃需求 yaml 的 `title` 字段人工核查非空（executing 阶段在 verification 用 `grep -l '^title: *""' .workflow/state/requirements/*.yaml` 做兜底校验）。
- **`.workflow/state/runtime.yaml`**：由 CLI 首次运行时自动回填三个 `*_title`（不用户手改）。
- **单元测试**：新增 `tests/test_runtime_title_fields.py`（或合并到 `tests/test_next_writeback.py`）：
  - `test_runtime_yaml_preserves_title_fields`：save → load 往返，三个 `*_title` 不丢。
  - `test_title_sync_on_current_requirement_set`：改 `current_requirement` 时，`current_requirement_title` 同步写入。
  - `test_title_sync_missing_state_fallback_empty`：对应 state yaml 不存在时，`*_title` 写空串不抛错。
  - `test_create_requirement_requires_title`：传空 title 时 `create_requirement` 抛 SystemExit。

### 5.2 Out of scope（不包含）

- CLI 渲染层改造（由 chg-02 负责）。
- 角色文件 / `stage-role.md` 汇报契约更新（由 chg-03 负责）。
- 归档目录 `_meta.yaml` 落盘（由 chg-04 可选负责）。
- 不改 `state/requirements/*.yaml` 的现有字段顺序或字段名；`title` 字段已存在，本 change 只保证"非空 + 同步"。
- 不回填历史归档目录（`artifacts/main/archive/requirements/*/_meta.yaml` 是 chg-04 的事）。
- 不改 slug / 目录路径结构（req-30 §4.2 明确排除）。

## 6. Definition of Done（验收条件，≥3 条）

1. **DoD-1**：`.workflow/state/runtime.yaml` 通过一次 `harness status` 命令触发的 load→save 往返后，同时包含 `current_requirement` + `current_requirement_title` 两个字段（当前值为 `req-30` + `slug 沟通可读性增强：全链路透出 title`），且 yaml 字段顺序稳定。
2. **DoD-2**：`state/requirements/req-28-*.yaml` / `req-29-*.yaml` / `req-30-*.yaml` 的 `title` 字段 grep 出来均非空字符串。
3. **DoD-3**：`tests/test_runtime_title_fields.py`（或等价文件）新增 4 条用例全部通过；现有 180+ 测试零回归（`pytest` 全绿）。
4. **DoD-4**：`_resolve_title_for_id` helper 在 `grep -n "runtime\[\"current_requirement\"\] *=" src` 命中的所有写入点之后被调用，无"只写 id 不写 title"的遗漏（executing 角色交付时附上 grep 证据）。

## 7. 关联 AC（逐条列出）

| AC | 说明 | 本 change 覆盖方式 |
|----|------|-----------------|
| AC-05 | `runtime.yaml` 新增 `*_title` 三字段 + `state/requirements/*.yaml` 活跃需求 title 非空 | Step 1~3 + 活跃需求人工回填 |
| AC-06 | 所有写 state yaml 的代码路径同步写 title | Step 2（helper）+ Step 3（批量改造写入点） |
| AC-09（部分） | 至少 2 条单测覆盖 | Step 5（4 条单测覆盖写入与往返） |

## 8. 依赖 / 顺序

- **本 change 是 chg-02 的前置**：chg-02 的 `render_work_item_id` helper 优先读 runtime.yaml 的 `*_title`（缓存），缺失时 fallback 到 state/requirements 的 `title`——chg-02 的 fallback 依赖本 change 落地 state 层 title 才稳定。
- **本 change 不依赖 chg-03 / chg-04**，但建议先于 chg-03（chg-03 的角色模板示例可以引用 state 层已有的 title 作为自证）。
- **执行顺序建议**：chg-01 → chg-02 → chg-03 → chg-04（可选）。

## 9. 风险与缓解

- **R1 缓存一致性**：runtime.yaml 的 `*_title` 与 state/requirements 的 `title` 漂移（例如用户直接改 state yaml 不触发 runtime 重写），CLI 会错显。
  - **缓解**：约定"state 权威、runtime 缓存、读 runtime 失败时 CLI fallback 到 state"；在 `_resolve_title_for_id` 中固定"只读 state 为源"的单向数据流；由 chg-02 的 `render_work_item_id` 在读取时做二次校验（runtime cache ≠ state 时以 state 为准并刷新 runtime）。
- **R2 批量写入点遗漏**：`workflow_helpers.py` 中写 `runtime["current_requirement"] = ...` 的点分散在 11 处左右，遗漏任何一处都会造成 `*_title` 为空的 bug。
  - **缓解**：executing 阶段用 grep 扫描 `runtime\["(current_requirement|current_regression|locked_requirement)"\]\s*=` 全部命中行，逐一审查并在 PR description 列出 checklist；单测 `test_title_sync_on_current_requirement_set` 作为自动化兜底。
- **R3 `create_requirement` 向后兼容性**：历史代码可能传空 title（没有 title 参数），直接 raise 会破坏测试。
  - **缓解**：新规则只对"经 CLI 入口创建的新需求"生效；helper 内部调用（如 bugfix 分流）若暂无 title，允许回退到 id 作为 title（并打印 stderr 提示 "title fallback to id"），避免大面积破坏——executing 阶段敲定具体策略并记录到 decisions-log。
