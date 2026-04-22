# Change Plan

> 父 change：chg-02（工作流推进 + ff 机制）/ req-31（批量建议合集（20条））

## 1. Development Steps

### Step 1：`_reset_ff_mode_after_done_archive` helper + 调用点接入（sug-27，最轻量，最先做）

- **操作意图**：修复 `ff_mode` 在 done/archive 后需手工关的顽疾；为 req-31 AC-自证提供保障（本 req 完成后 `runtime.yaml.ff_mode == false`）。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py`（`workflow_next` 5285 / `archive_requirement` 4965 / `workflow_ff_auto`（在 `ff_auto.py` 里））；`src/harness_workflow/ff_auto.py`。
- **关键代码思路**：
  ```python
  # workflow_helpers.py
  _FF_RESET_TERMINAL_STAGES = frozenset({"done", "archive", "completed"})
  def _reset_ff_mode_after_done_archive(runtime: dict, new_stage: str) -> dict:
      if new_stage in _FF_RESET_TERMINAL_STAGES and runtime.get("ff_mode"):
          runtime["ff_mode"] = False
      return runtime

  # workflow_next 内（5366 行已有 "ff 单次生效" 的 single-shot reset，保留）
  # 额外在任何翻 stage 的点前统一过一道：
  runtime = _reset_ff_mode_after_done_archive(runtime, new_stage)

  # archive_requirement 落地前 load runtime → helper → save：
  runtime = load_requirement_runtime(root)
  runtime = _reset_ff_mode_after_done_archive(runtime, "archive")
  save_requirement_runtime(root, runtime)
  ```
- **body 丢失补位**：sug-27 title "`ff_mode` 在 done / archive 后应自动关闭" 推断来源 = req-31 requirement.md §4 AC-07 + §4 AC-自证（`runtime.yaml.ff_mode == false`）+ 当前 `workflow_helpers.py:5366` 已有的 single-shot reset 作为参照。
- **验证方式**：
  - 新增 `tests/test_ff_mode_auto_reset.py` 的 3 条用例（见 change.md §5.1）。
  - 手工：fixture 仓库 `ff_mode: true` + stage=done → `workflow_next` → 读 runtime.yaml 断言 `ff_mode: false`。

### Step 2：`_sync_stage_to_state_yaml` 总是初始化 stage_timestamps（sug-16）

- **操作意图**：消除"state yaml 无 stage_timestamps 字段时，sync helper 静默跳过"的盲区，使 regression/bugfix 所有路径都能写入时间戳。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py::_sync_stage_to_state_yaml`（4435）。
- **关键代码思路**：
  ```python
  # 原 4490 行：if "stage_timestamps" in target_state: ...
  # 改为：
  _STAGE_WHITELIST = frozenset({
      "requirement_review", "planning", "executing", "testing",
      "acceptance", "regression", "done", "archive"
  })
  if new_stage in _STAGE_WHITELIST:
      existing = target_state.get("stage_timestamps")
      if not isinstance(existing, dict):
          existing = {}
      existing[new_stage] = datetime.now(timezone.utc).isoformat()
      target_state["stage_timestamps"] = existing
  ```
- **body 丢失补位**：sug-16 title "`regression --testing` 路径盲区导致 stage_timestamps 字段缺" 推断来源 = 直接源码定位 `workflow_helpers.py:4490` 的 `if "stage_timestamps" in target_state` 条件分支 + `regression_action`（4015）调用方是否传 "testing" stage + commit `1d73f90`（归档 req-29）前后 state yaml 结构。
- **验证方式**：
  - 新增 `tests/test_stage_timestamps_completeness.py::test_regression_testing_writes_timestamp` + `test_sync_stage_initializes_missing_timestamps_field`。
  - 现有 `tests/test_next_writeback.py` 零回归（关键！该测试覆盖 `stage_timestamps` 现有行为）。

### Step 3：`regression_action` 所有子路径显式调 sync（sug-16 配套）

- **操作意图**：闭合 Step 2 的底层改造——在 regression 所有路径（start / testing / accept / reject）调用链末尾都明确触发 sync helper。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py::regression_action`（4015）。
- **关键代码思路**：
  - grep `regression_action` 函数体所有 stage 翻转点（如 `runtime["stage"] = "regression"` / `= "testing"`），每个翻转后紧邻一行：
    ```python
    _sync_stage_to_state_yaml(root, operation_type, operation_target, new_stage)
    ```
  - 若 `regression_action` 内没有明确 sync 调用点（目前可能只在顶层 `workflow_next` 调），在各子路径返回前补上。
- **验证方式**：
  - grep `tests/test_regression_helpers.py` 确认覆盖所有 regression_action 子路径；若缺，扩展测试断言 state yaml 含时间戳。

### Step 4：bugfix ff 路径每步调 sync（sug-21）

- **操作意图**：`workflow_ff_auto` 在 bugfix 分支遍历 stage sequence 时每步都调 sync helper，消除 `stage_timestamps` 缺字段。
- **涉及文件**：`src/harness_workflow/ff_auto.py::workflow_ff_auto`（bugfix 分支）。
- **关键代码思路**：
  ```python
  # ff_auto.py 的 stage 推进循环里：
  for stage in BUGFIX_SEQUENCE:
      runtime["stage"] = stage
      runtime = _reset_ff_mode_after_done_archive(runtime, stage)  # Step 1 helper
      save_requirement_runtime(root, runtime)
      _sync_stage_to_state_yaml(root, "bugfix", bugfix_id, stage)  # Step 4 新增
  ```
- **body 丢失补位**：sug-21 title "bugfix ff 路径下 stage_timestamps 仍缺 regression/executing/testing 字段" 推断来源 = 源码定位 `ff_auto.py::workflow_ff_auto` bugfix 分支 + commit `da91ab3`（bugfix-3 install/update 单 agent 作用域）附近的 bugfix 流转代码。
- **验证方式**：
  - 新增 `tests/test_stage_timestamps_completeness.py::test_bugfix_ff_writes_all_stage_timestamps`：构造 bugfix fixture → 调 `workflow_ff_auto` → 断言 state yaml 的 `stage_timestamps` 含 7 个 stage。

### Step 5：ff subagent idle timeout 兜底（sug-18）

- **操作意图**：ff 模式下派发 subagent 的长任务超时不再悬挂，超时抛异常由主 agent 接住 + 上报。
- **涉及文件**：`src/harness_workflow/ff_auto.py`（派发点）；可能新增 `src/harness_workflow/ff_timeout.py`。
- **关键代码思路**（优先方案 = asyncio.wait_for）：
  ```python
  # ff_timeout.py
  class FFSubagentIdleTimeout(TimeoutError):
      pass
  async def _dispatch_coro(callable_, *args, **kwargs):
      return callable_(*args, **kwargs)
  def dispatch_with_timeout(callable_, *args, idle_seconds: int = 300, **kwargs):
      try:
          return asyncio.run(asyncio.wait_for(_dispatch_coro(callable_, *args, **kwargs), idle_seconds))
      except asyncio.TimeoutError as e:
          raise FFSubagentIdleTimeout(f"Subagent idle > {idle_seconds}s") from e

  # ff_auto.py 派发点调用改为：
  try:
      result = dispatch_with_timeout(subagent_callable, briefing, idle_seconds=300)
  except FFSubagentIdleTimeout as e:
      print(f"[ff_auto] WARNING: {e}; pausing ff advancement", file=sys.stderr)
      # 不崩溃，保留 runtime 当前 stage，等主 agent 决定
      return 1
  ```
  - 降级方案（若 asyncio 改造风险大）：subagent 入口打时间戳 + 超过 300s 打 stderr warning + 返回 1（软超时）。
- **body 丢失补位**：sug-18 title "ff 模式下 subagent 任务拆分粒度与 API idle timeout 保护" 推断来源 = req-31 §4 AC-07（明确 "超时自动上报主 agent 而非悬挂"）+ ff_auto.py 现有同步派发结构 + `.workflow/context/roles/harness-manager.md`（subagent briefing 协议）。"任务拆分粒度" 部分因 body 丢失细节不全 — 本 change 仅落 timeout，拆分粒度留给后续 sug。
- **验证方式**：
  - 新增 `tests/test_ff_subagent_timeout.py` 的 2 条用例。

### Step 6：`harness next --execute` 扩展派发 subagent briefing（sug-09，最重）

- **操作意图**：让 `harness next --execute` 不止翻 stage，还能输出 subagent briefing 供主 agent 直接消费；降低"翻完 stage 要再开一轮对话"的成本。
- **涉及文件**：`src/harness_workflow/workflow_helpers.py::workflow_next`（5285）；可能新增 `src/harness_workflow/subagent_briefing.py`（briefing 模板构建器）。
- **关键代码思路**：
  ```python
  # subagent_briefing.py
  BRIEFING_TEMPLATE = """
  ```subagent-briefing
  {{
    "role": "{role}",
    "stage": "{stage}",
    "requirement_id": "{req_id}",
    "requirement_title": "{req_title}",
    "context_chain": [{{"level": 0, "agent": "main", "stage": "{stage}"}}]
  }}
  ```
  """
  def build_briefing(root, stage, req_id) -> str:
      role = STAGE_TO_ROLE[stage]  # e.g. "planning" -> "架构师"
      title = _resolve_title_for_id(root, req_id) or req_id
      return BRIEFING_TEMPLATE.format(role=role, stage=stage, req_id=req_id, req_title=title)

  # workflow_next(execute=True) 新增末尾：
  if execute and new_stage and new_stage not in ("done", "archive"):
      print(build_briefing(root, new_stage, req_id))
  ```
- **body 丢失补位**：sug-09 title "`harness next` 支持触发下一 stage 的实际工作（当前仅更新 stage）" 推断来源 = req-31 §4 AC-05 + `.workflow/context/roles/harness-manager.md`（stage 路由协议）+ 现状 `workflow_next`（5285）已有 `--execute` flag 但只用于确认 ready_for_execution，本 change 扩展为派发 briefing。
- **验证方式**：
  - 新增 `tests/test_next_execute.py::test_next_execute_advances_and_dispatches` + `test_next_without_execute_only_advances`。

### Step 7：回归 + 自证

- **操作意图**：chg-02 落地后，req-31 后续 change 基于本 change 的改造自证运转。
- **验证方式**：
  - `pytest` 全量绿。
  - `harness ff --auto` 跑通一个 dummy 需求 → `runtime.yaml.ff_mode` 自动降为 false。
  - 本 change 产出文档（change.md / plan.md / 变更简报.md / 实施说明.md）过 `harness status --lint` 得绿（依赖 chg-01）。

## 2. Verification Steps

### 2.1 单测 / 集成测清单

| 测试文件 / 用例 | 意图 | 关键断言 |
|----------------|------|---------|
| `tests/test_ff_mode_auto_reset.py::test_ff_mode_reset_after_done` | done 后自动关 ff_mode | `ff_mode == False` |
| `tests/test_ff_mode_auto_reset.py::test_ff_mode_reset_after_archive` | archive 后自动关 | 同上 |
| `tests/test_ff_mode_auto_reset.py::test_ff_mode_persists_during_execution` | executing 中不误关 | `ff_mode == True` |
| `tests/test_stage_timestamps_completeness.py::test_regression_testing_writes_timestamp` | regression_action(testing) 写 timestamp | state yaml `stage_timestamps.testing` 非空 |
| `tests/test_stage_timestamps_completeness.py::test_bugfix_ff_writes_all_stage_timestamps` | bugfix ff 全程 7 stage | 全部 7 字段非空 |
| `tests/test_stage_timestamps_completeness.py::test_sync_stage_initializes_missing_timestamps_field` | 缺字段自动初始化 | 从 missing → dict with 1 entry |
| `tests/test_ff_subagent_timeout.py::test_ff_subagent_idle_timeout_raises` | 超时抛异常 | `FFSubagentIdleTimeout` raised |
| `tests/test_ff_subagent_timeout.py::test_ff_continues_after_timeout_report` | 超时不崩溃 | main flow 返回 1 + stderr 含 WARNING |
| `tests/test_next_execute.py::test_next_execute_advances_and_dispatches` | --execute 翻 stage + briefing | stdout 含 `subagent-briefing` JSON fence |
| `tests/test_next_execute.py::test_next_without_execute_only_advances` | 无 --execute 仅翻 stage | stdout 不含 briefing |

### 2.2 Manual smoke verification

- fixture 仓库：
  1. `ff_mode=True` + stage=acceptance → `harness next` → stage=done → `harness next` → stage=archive → 读 `runtime.yaml` 断言 `ff_mode: false`。
  2. `harness bugfix "smoke"` → `harness ff --auto` → 全程跑完 → `state/bugfixes/bugfix-X.yaml` 的 `stage_timestamps` 含 7 stage 字段。
  3. `harness next --execute` on stage=plan_review → stdout 含 `executing` 角色的 subagent briefing JSON fence。

### 2.3 AC Mapping

- AC-05 → Step 6 + `tests/test_next_execute.py`。
- AC-06 → Step 2 + Step 3 + Step 4 + `tests/test_stage_timestamps_completeness.py`。
- AC-07 → Step 1 + Step 5 + `tests/test_ff_mode_auto_reset.py` + `tests/test_ff_subagent_timeout.py`。
- AC-自证 → Step 7：req-31 完成后 `runtime.yaml.ff_mode == false` 自证，依赖 Step 1。

## 3. body 丢失补位专段

| sug id | title | 推断来源 |
|--------|-------|---------|
| sug-09（`harness next` 支持触发下一 stage 的实际工作） | req-31 §4 AC-05 + `workflow_next` 现状签名 + `.workflow/context/roles/harness-manager.md` subagent briefing 协议 |
| sug-16（`_sync_stage_to_state_yaml` 在 `regression --testing` 路径盲区） | 源码 `workflow_helpers.py:4490` 条件分支 + `regression_action`（4015）调用链 |
| sug-18（ff 模式下 subagent 拆分粒度 + API idle timeout 保护） | req-31 §4 AC-07 + `ff_auto.py` 当前同步派发结构 + req-30 executing 阶段曾出现 subagent 悬挂经验（session-memory） |
| sug-21（bugfix ff 路径下 stage_timestamps 仍缺字段） | 源码 `ff_auto.py` bugfix 分支 + commit `da91ab3`（bugfix-3 install/update） |
| sug-27（`ff_mode` 在 done / archive 后应自动关闭） | req-31 §4 AC-07 + `workflow_helpers.py:5366` single-shot reset 已有模式 |

## 4. 回滚策略

- **粒度**：按 Step 1-7 拆分 git 提交；每个 Step 独立 revert。
- **回滚触发**：
  - Step 2 若 `tests/test_next_writeback.py` 回归（历史 state yaml 无 `stage_timestamps` 字段被强制初始化，断言失败）→ 加白名单保护（仅新建 state yaml 初始化），保留历史结构。
  - Step 5 若 `asyncio.wait_for` 改造破坏 `ff_auto.py` 现有同步流 → 降级为软超时（stderr warning 不 raise），保守发布。
  - Step 6 若 briefing JSON fence 输出与主 agent 解析不一致 → 改为自由文本格式（section-based），由 chg-01 文档同步更新。
- **兜底**：所有修改集中在 `workflow_helpers.py` + `ff_auto.py` + 新增 tests；`git revert` 单次可撤销。

## 5. 执行依赖顺序

1. Step 1（sug-27 `ff_mode` 自动关）**最先**——阻塞 req-31 AC-自证。
2. Step 2（sug-16 `_sync_stage` 改造）在 Step 1 后独立。
3. Step 3（regression_action 补 sync）依赖 Step 2 的 helper 行为稳定。
4. Step 4（bugfix ff 补 sync）依赖 Step 1（调 `_reset_ff_mode...`）+ Step 2。
5. Step 5（subagent timeout）独立，可与 Step 2-4 并行。
6. Step 6（`next --execute`）最重，依赖 Step 1（不要翻到 done 还发 briefing）。
7. Step 7（回归 + 自证）最后。

**前置依赖**：chg-01（契约自动化）——本 change 产出文档的契约 7 自检依赖 `harness status --lint`。

## 6. 风险表

| 风险 ID | 风险描述 | 缓解措施 |
|---------|---------|---------|
| R1 | `_sync_stage_to_state_yaml` 初始化 dict 可能引入 schema 漂移 | 白名单限定 + 历史 yaml 回归 `tests/test_next_writeback.py` |
| R2 | `_reset_ff_mode_after_done_archive` 调用点遗漏 | grep 断言 `ff_mode` 赋值全部经过新 helper |
| R3 | asyncio.wait_for 改造破坏同步流 | 降级软超时；asyncio.run 包裹仅在 ff_auto 入口一处 |
| R4 | briefing 输出格式不稳定 | 固定 JSON fence + 由 chg-01 `harness-manager.md` 契约 7 段约定 |
| R5 | body 丢失导致细节遗漏（如 sug-18 "任务拆分粒度"未覆盖） | 本 change 只落 timeout 部分，拆分粒度标注为"delta 未决"，executing 阶段若发现重要遗漏回补 sug |
| R6 | req-31 AC-自证依赖 chg-02 先于 chg-03/04/05 落地 | 依赖顺序 chg-01 → chg-02 → chg-03 → chg-04 → chg-05 强制 |
