# Change Plan

## 1. Development Steps

### Step 1: 扩展 `DEFAULT_STATE_RUNTIME` 与 `save_requirement_runtime`

- **操作意图**：让 `runtime.yaml` 的 schema 具备 `*_title` 三字段位，save→load 往返不丢。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py`（约 57-69 行 `DEFAULT_STATE_RUNTIME`，370-394 行 `save_requirement_runtime`）。
- **关键代码思路**：
  - `DEFAULT_STATE_RUNTIME` 新增三个键：`current_requirement_title: ""` / `current_regression_title: ""` / `locked_requirement_title: ""`，位置紧邻对应 id 字段（如 `current_requirement` 之后插入 `current_requirement_title`）。
  - `save_requirement_runtime` 的 `ordered_keys` 列表按相同顺序插入三个新键，确保 yaml 字段顺序稳定。
  - `load_requirement_runtime` 的默认回填逻辑保持不变（`payload.update(DEFAULT_STATE_RUNTIME)` 天然兼容）。
- **验证方式**：
  - 新增用例 `test_runtime_yaml_preserves_title_fields`：save → load → 断言三个 `*_title` 在读出后仍为写入值。
  - `pytest tests/test_next_writeback.py` 零回归。

### Step 2: 新增 `_resolve_title_for_id` helper

- **操作意图**：提供"id → title"的单一数据源，所有写入点调用此 helper，避免各调用点自己实现读 state yaml 的逻辑。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py`（可放在 `load_requirement_runtime` 附近，便于 import）。
- **关键代码思路**：
  - 函数签名：`def _resolve_title_for_id(root: Path, work_item_id: str) -> str:`
  - 按 id 前缀分流：
    - `req-*` → `root / ".workflow/state/requirements/*.yaml"`，用 `load_simple_yaml` 遍历，按 `_get_req_id(payload) == work_item_id` 匹配，返回 `state.get("title", "")`。
    - `bugfix-*` → `root / ".workflow/state/bugfixes/*.yaml"`，同上（目录不存在时返回空串）。
    - `reg-*` → 当前 state 层无单独 yaml，尝试返回空串（regression 的 title 在 req 级，后续由 chg-02 的 render helper 统一回退）。
  - 找不到或文件读错误：一律返回 `""`，不抛异常（null-safe）。
- **验证方式**：
  - 新增单测 `test_resolve_title_for_id_returns_state_title`：构造 fixture req-99 yaml，断言返回正确 title。
  - 新增单测 `test_resolve_title_for_id_missing_returns_empty`：未知 id 返回空串。

### Step 3: 改造所有 runtime id 写入点

- **操作意图**：保证每次修改 `current_requirement` / `current_regression` / `locked_requirement` 时，对应 `*_title` 被同步刷新；实现"写入侧原子一致"。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py`（grep 命中行：~2412 / 2424 / 3516 / 3603 / 3723 / 3865 / 3873 / 3885 / 3892 / 3900 / 4926）。
- **关键代码思路**：
  - 在每个 `runtime["current_requirement"] = <new_id>` 之后追加：`runtime["current_requirement_title"] = _resolve_title_for_id(root, <new_id>) if <new_id> else ""`。
  - 对 `current_regression` / `locked_requirement` 做同样处理。
  - 如果某个写入点是"清空"（`runtime["current_requirement"] = ""`），则同步清空 `*_title = ""`。
- **验证方式**：
  - 新增 grep 断言单测 `test_title_sync_on_current_requirement_set`（用 tmp_path 构造 fixture 仓库，调 `create_requirement("test title")` → 读 runtime.yaml → 断言 `current_requirement_title == "test title"`）。
  - 手工 grep `runtime\["(current_requirement|current_regression|locked_requirement)"\]\s*=` 核对所有命中行均已同步。

### Step 4: `create_requirement` / `create_bugfix` 写 state yaml 带 title 必填

- **操作意图**：新建入口层面拦截"空 title"，杜绝 state yaml 产生空 title 记录。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py`（`create_requirement` / `create_bugfix` 所在函数）。
- **关键代码思路**：
  - `create_requirement(root, title)`：若 `title.strip() == ""`，`raise SystemExit("Requirement title is required (req-30 / chg-01).")`。
  - 写入 state yaml 时，`title` 字段直接取入参；不再允许默认空串。
  - `create_bugfix` 同样逻辑。
  - 为保持与 bugfix-3 `apply_suggestion` 的兼容：`apply_suggestion` 已经用 first_line 做 title（60 字符截断），传给 `create_requirement` 的 title 始终非空——无需额外改造。
- **验证方式**：
  - 新增用例 `test_create_requirement_requires_title`：传空 title 断言抛 SystemExit。
  - 现有 `test_smoke_req*.py` 全部复用 title 参数，零回归。

### Step 5: 活跃需求 title 回填（一次性）

- **操作意图**：确保当前 active_requirements（req-28 / req-29 / req-30）的 state yaml 的 `title` 非空，符合 AC-05 约束。
- **涉及文件**：`state/requirements/req-28-批量建议合集（7条）.yaml` / `req-29-*.yaml` / `req-30-*.yaml`（需 executing 阶段实际 grep 确认）。
- **关键代码思路**：
  - `grep -l '^title: *""' .workflow/state/requirements/*.yaml`：列出当前空 title 的 yaml。
  - 对每个空 title 文件，用 Edit 补齐 title 字段（值从对应 `artifacts/main/requirements/{dir}/requirement.md` 的首个 `## 1. Title` 下一行读取）。
  - 若 req-28 / req-29 已归档（位于 `artifacts/main/archive/`），且 state yaml 已不活跃（`active_requirements` 不含）则跳过，不回填。
- **验证方式**：
  - 手工 `grep ^title .workflow/state/requirements/req-2[89].yaml .workflow/state/requirements/req-30*.yaml`，断言三个文件 title 非空。

### Step 6: 编写单元测试

- **操作意图**：把 Step 1-4 的行为变化固化为自动化回归。
- **涉及文件**：`tests/test_runtime_title_fields.py`（新增）或合并到 `tests/test_next_writeback.py`（优先独立新文件，便于 grep）。
- **关键代码思路**：
  - `test_runtime_yaml_preserves_title_fields`：用 `save_requirement_runtime` / `load_requirement_runtime` 往返，三个 `*_title` 不丢。
  - `test_title_sync_on_current_requirement_set`：fixture 仓库创建 req-99 state yaml → 调 `workflow_next` 或直接 set `current_requirement` → 断言 runtime.yaml 的 `current_requirement_title` 已回填。
  - `test_title_sync_missing_state_fallback_empty`：`current_requirement = "req-404"`（不存在）→ `current_requirement_title == ""`，不抛错。
  - `test_create_requirement_requires_title`：`create_requirement(root, "")` 抛 SystemExit。
- **验证方式**：
  - `pytest tests/test_runtime_title_fields.py -v` 全绿。
  - `pytest` 全量零回归（现有 180+ 用例）。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `pytest tests/test_runtime_title_fields.py -v`：新增 4 条用例全部通过。
- `pytest` 全量：现有 180+ 测试零回归。
- `grep -n "runtime\[\"current_requirement\"\] *=" src/harness_workflow/workflow_helpers.py`：列出所有写入点，对照 Step 3 的改造清单无遗漏。
- `grep ^title .workflow/state/requirements/req-30*.yaml`：非空。

### 2.2 Manual smoke verification

- 在 tmp fixture 仓库中：
  1. `harness install` → `harness requirement "smoke title"` → 读 `.workflow/state/runtime.yaml`，断言 `current_requirement_title: "smoke title"`。
  2. `harness next` 推进 stage → runtime.yaml 的 `*_title` 仍保留不丢。
  3. `harness status` 输出中能看到 `current_requirement_title` 字段（渲染由 chg-02 负责，但字段本身应可读）。

### 2.3 AC Mapping

- AC-05 → Step 1 + Step 5 + 单测 `test_runtime_yaml_preserves_title_fields`。
- AC-06 → Step 2 + Step 3 + Step 4 + 单测 `test_title_sync_on_current_requirement_set` / `test_create_requirement_requires_title`。
- AC-09（部分）→ Step 6 的 4 条单测。

## 3. 执行依赖顺序

1. Step 1（schema 扩展）优先：其余步骤都依赖新字段位。
2. Step 2（helper）先于 Step 3（写入点改造）。
3. Step 3 与 Step 4 可并行，但都需先 pass Step 1 + Step 2。
4. Step 5（活跃需求回填）独立，可与 Step 1-4 并行。
5. Step 6（单测）在 Step 1-4 完成后统一跑。
6. **前置依赖**：无（本 change 是整个 req-30 的最前置）。
7. **后置依赖**：chg-02 依赖本 change 落地后的 `*_title` 字段；chg-03 / chg-04 独立。

## 4. 回滚策略

- **粒度**：按 Step 1-6 的提交粒度拆分 git 提交；每个 Step 一个 commit，方便单独 revert。
- **回滚触发条件**：
  - Step 1 提交后若 `save_simple_yaml` 写出的 yaml 顺序混乱（字段位漂移）→ revert Step 1；重新设计 `ordered_keys` 插入位置。
  - Step 3 提交后若 `pytest` 出现回归（尤其 `test_next_writeback.py`、`test_smoke_req*.py`）→ 定位哪个写入点把非空 title 覆盖成空（R1 缓存漂移的表现），针对性修正；必要时 revert Step 3 保守版本。
  - Step 4 若阻塞 `apply_suggestion` 或 `create_bugfix` 正常路径（title 意外为空触发 SystemExit）→ 将 "empty title fallback to id" 策略落实到 helper，避免破坏现有流程。
- **兜底**：所有修改集中在 `workflow_helpers.py` + 新增 test 文件 + 少量 state yaml；`git revert` 单次回滚可完全撤销，无数据库或外部系统副作用。

## 5. 风险表

| 风险 ID | 风险描述 | 缓解措施 |
|---------|---------|---------|
| R1 | runtime.yaml 的 `*_title` 与 state yaml 的 `title` 漂移 | 约定"state 权威、runtime 缓存、读失败 fallback"；`_resolve_title_for_id` 只从 state 读；chg-02 渲染层二次校验 |
| R2 | 11 处写入点遗漏导致 title 为空 | grep 清单 + `test_title_sync_on_current_requirement_set` 自动兜底 |
| R3 | `create_requirement` 对空 title 抛错破坏现有流程 | 只在 CLI 入口拦截；helper 内部调用保留"fallback to id" 的兼容路径；由 executing 阶段敲定并记录 decisions-log |
| R4 | state/bugfixes 目录当前为空，未来 bugfix 创建时若漏加 title 字段会悄悄退化 | `create_bugfix` 同步加 title 非空校验；单测 `test_create_bugfix_requires_title` 可选补充 |
