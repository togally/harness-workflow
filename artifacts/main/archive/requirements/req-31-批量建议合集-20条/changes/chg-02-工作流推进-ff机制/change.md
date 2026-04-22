# Change

## 1. Title

chg-02（工作流推进 + ff 机制）：`harness next --execute` 触发下一 stage 实际工作 + `_sync_stage_to_state_yaml` 覆盖 regression/bugfix ff 全路径 + ff 模式 subagent timeout 兜底 + `ff_mode` 在 done/archive 后自动关

> 父需求：req-31（批量建议合集（20条））

## 2. Background

源自 req-31（批量建议合集（20条））§5 Split Rules 的 **chg-02 分组**（B 组工作流推进 + C 组 stage_timestamps 字段完整性合并，共 5 条 sug），以及 §4 的 **AC-05 / AC-06 / AC-07**：

- **现状**：
  - `harness next`（`workflow_next` in `workflow_helpers.py:5285`）只翻 `runtime.yaml` 的 `stage` 字段，不触发下一 stage 的实际工作（subagent 派发 / executing agent 调用）；用户经常需要手工再开一次对话请 agent 执行新 stage。
  - `_sync_stage_to_state_yaml`（`workflow_helpers.py:4435`）在 `regression --testing` 子路径调用方不通 + bugfix ff 主路径覆盖不完整，实测导致 `stage_timestamps` 缺 `regression` / `executing` / `testing` 字段（sug-16 / sug-21 双命中）。
  - `ff_mode`（`workflow_helpers.py:5366` 已有"`ff 单次生效`"的单次重置）在 **非 ff 单次** 场景（如 done → archive 全链路）未自动复位；req-30（slug 沟通可读性增强：全链路透出 title）done 阶段手动关 `ff_mode`，经验不稳固。
  - ff 模式派发 subagent 长任务时缺 API idle timeout 兜底（sug-18），实测 req-30 chg-03 曾出现 subagent 悬挂 10 分钟无响应。
- **关键依赖**：本 change 的"`ff_mode` 自动关"必须在 req-31 完成前落地，否则 req-31 AC-自证（`runtime.yaml.ff_mode == false`）不通过。

## 3. Goal

- `harness next` 引入 `--execute` flag（或等价行为）：翻 stage 的同时，按目标 stage 派发对应角色的 subagent / 触发实际工作；原默认行为（仅翻 stage）保留向后兼容。
- `_sync_stage_to_state_yaml` 覆盖 `regression --testing` 调用点 + bugfix ff 全路径（regression_action / `workflow_ff_auto` bugfix 分支），所有 stage 均写入 `stage_timestamps`。
- `ff_mode` 在 done + archive 成功后由 CLI 自动重置为 `false`（独立 helper `_reset_ff_mode_after_done_archive`）；本 req 完成后 `runtime.yaml.ff_mode == false` 自证。
- ff 模式下 subagent 长任务有 API idle timeout 兜底（≤ 5 分钟 idle 自动上报主 agent，而非悬挂）。

## 4. Requirement

- req-31（批量建议合集（20条））

## 5. Scope

### 5.1 In scope

- **`src/harness_workflow/workflow_helpers.py`**：
  - `workflow_next`（5285）：扩展 `execute: bool = False` 参数（当前签名已有，但默认仅"确认 ready_for_execution"）；改为当 `execute=True` 时：① 翻 stage；② 根据新 stage 派发对应角色 briefing（通过 stdout 输出 subagent 任务描述 + context_chain，由主 agent 读后调用 Task 工具）；③ 打印 "Executing stage: {stage}"。
  - `_sync_stage_to_state_yaml`（4435）：现状仅在 stage 字段存在 `stage_timestamps` 时才写入（4490 行 `if "stage_timestamps" in target_state`）；改为**总是初始化**空 dict 并写入时间戳（覆盖 regression / bugfix ff 盲区）。
  - 新增 helper `_reset_ff_mode_after_done_archive(runtime: dict, new_stage: str) -> dict`：当 `new_stage in ("done", "archive", "completed")` 时强制 `runtime["ff_mode"] = False` + 返回 runtime；被 `workflow_next` / `archive_requirement` / `workflow_ff_auto` 统一调用。
  - `regression_action`（4015）：所有子路径（start / testing / accept / reject）调用完后显式调 `_sync_stage_to_state_yaml`；确保 `stage_timestamps.regression` / `stage_timestamps.testing` 落盘。
- **`src/harness_workflow/ff_auto.py`**：
  - bugfix 分支（FF 遍历 bugfix stage sequence）每步调 `_sync_stage_to_state_yaml`；`workflow_ff_auto` 在到达 `done` 后调 `_reset_ff_mode_after_done_archive`。
  - 新增 subagent idle timeout 兜底：包一层 `with_timeout(callable, idle_seconds=300)`，超时抛 `FFSubagentIdleTimeout` 异常，主 agent 接住后上报 + 暂停 ff 推进（不强制进程退出，避免丢上下文）。实现方式：给 subagent 调用入口（`dispatch_subagent`）加 `signal.SIGALRM` 或 `asyncio.wait_for` 包装（依 Python runtime 决定，executing 阶段敲定，**优先 `asyncio.wait_for`** 因为不会破坏同步流）。
- **`src/harness_workflow/cli.py`**：
  - `next_parser`（约 200）已有 `--execute` flag，但当前语义是"确认 ready_for_execution"；扩展为"派发 subagent 执行当前 stage"（保持 CLI flag 不变，行为增强）。
  - `archive` 子命令（若不存在，归属到 `workflow_next` 里 stage=archive 的路径）在归档成功后调 `_reset_ff_mode_after_done_archive`。
- **单元测试**：
  - `tests/test_next_execute.py`（新增）：
    - `test_next_execute_advances_and_dispatches`：fixture stage=plan_review → `workflow_next(execute=True)` → 断言：① stage 翻到 executing；② stdout 含 subagent briefing（如"executing 角色任务：..."）。
    - `test_next_without_execute_only_advances`：原行为验证，只翻 stage 无 briefing。
  - `tests/test_stage_timestamps_completeness.py`（新增，sug-16 + sug-21）：
    - `test_regression_testing_writes_timestamp`：模拟 `regression_action(mode="testing")` → 断言 state yaml 的 `stage_timestamps.testing` 非空。
    - `test_bugfix_ff_writes_all_stage_timestamps`：模拟 bugfix ff 全程 → 断言 `stage_timestamps` 含 `regression` / `executing` / `testing` / `acceptance` / `done` 全部字段。
    - `test_sync_stage_initializes_missing_timestamps_field`：state yaml 无 `stage_timestamps` 字段 → 调 `_sync_stage_to_state_yaml` → 字段被创建并写入。
  - `tests/test_ff_mode_auto_reset.py`（新增，sug-27）：
    - `test_ff_mode_reset_after_done`：fixture `ff_mode=True` + stage=done → `_reset_ff_mode_after_done_archive` → `ff_mode=False`。
    - `test_ff_mode_reset_after_archive`：同上，stage=archive。
    - `test_ff_mode_persists_during_execution`：stage=executing → `ff_mode` 保持 True（不误关）。
  - `tests/test_ff_subagent_timeout.py`（新增，sug-18）：
    - `test_ff_subagent_idle_timeout_raises`：mock subagent callable `time.sleep(400)` → `with_timeout(..., idle_seconds=300)` → 抛 `FFSubagentIdleTimeout`。
    - `test_ff_continues_after_timeout_report`：timeout 后 main flow 不崩溃，打印 stderr 警告。

### 5.2 Out of scope

- 不改 ff stage sequence 本身（req-29（批量建议合集（2条））已定义，不动）。
- 不扩展 `ff --auto` 到 acceptance 之后（req-31 §3.2 已明确排除）。
- 不改 `harness next` 在 `done` → `archive` 之间的默认自动行为（仍需人工确认）。
- 不做 subagent 结果流式渲染 / 进度报告（超范围）。
- 不处理契约自检类 sug（由 chg-01 负责）。
- 不处理 helper 修复类 sug（由 chg-03 负责）。
- 不处理归档 / 数据管道（由 chg-04 负责）。

## 6. 覆盖的 sug 清单（契约 7，id + title）

| sug id | title | 合入方式 |
|--------|-------|---------|
| sug-09（`harness next` 支持触发下一 stage 的实际工作（当前仅更新 stage）） | `workflow_next --execute` 扩展为派发 subagent briefing |
| sug-16（`_sync_stage_to_state_yaml` 在 `regression --testing` 路径盲区导致 stage_timestamps 字段缺） | `_sync_stage_to_state_yaml` 改为总是初始化 dict + `regression_action` 子路径全覆盖 |
| sug-18（ff 模式下 subagent 任务拆分粒度与 API idle timeout 保护） | `ff_auto` 调用 subagent 时包 `with_timeout(idle_seconds=300)` + 超时上报不悬挂 |
| sug-21（bugfix ff 路径下 stage_timestamps 仍缺 regression/executing/testing 字段） | bugfix 分支每步调 `_sync_stage_to_state_yaml`，与 sug-16 联合修复 |
| sug-27（`ff_mode` 在 done / archive 后应自动关闭） | 新增 `_reset_ff_mode_after_done_archive` + 在 `workflow_next` / `archive_requirement` / `workflow_ff_auto` 统一调用 |

## 7. 覆盖的 AC

| AC | 说明 | 本 change 覆盖方式 |
|----|------|-----------------|
| AC-05 | `harness next --execute` 触发下一 stage 实际工作 + 单测 2 条 | Step 1 + `tests/test_next_execute.py`（2 条用例） |
| AC-06 | `stage_timestamps` 在 `regression --testing` + bugfix ff 全程无缺字段 + 单测 | Step 2 + Step 4 + `tests/test_stage_timestamps_completeness.py`（3 条用例） |
| AC-07 | `ff_mode` done/archive 后自动关 + subagent timeout 兜底 + 本 req 完成后自证 `ff_mode == false` | Step 3 + Step 5 + `tests/test_ff_mode_auto_reset.py` + `tests/test_ff_subagent_timeout.py` |

## 8. DoD

1. **DoD-1**：`harness next --execute` 能在 fixture 仓库中：① 翻 stage；② stdout 含 subagent briefing；`tests/test_next_execute.py` 两条用例全绿。
2. **DoD-2**：`_sync_stage_to_state_yaml` 改造后，`tests/test_stage_timestamps_completeness.py` 三条用例全绿；现有 `tests/test_next_writeback.py` 零回归。
3. **DoD-3**：`_reset_ff_mode_after_done_archive` 在 stage=done/archive 时强制关 `ff_mode`；req-31 本身执行完 acceptance/done/archive 后 `.workflow/state/runtime.yaml` 的 `ff_mode: false` 自证。
4. **DoD-4**：ff subagent 调用包 `with_timeout(idle_seconds=300)`；`tests/test_ff_subagent_timeout.py` 两条用例全绿。
5. **DoD-5**：`regression_action` 所有子路径（start / testing / accept / reject）显式调 `_sync_stage_to_state_yaml`，grep 证据：每处调用后紧邻一行 `_sync_stage_to_state_yaml(...)`。
6. **DoD-综合**：全量 `pytest` 零回归；本 change 产出首次引用 id 均带 title（契约 7 自证 — 由 chg-01 的 `harness status --lint` 校验）。

## 9. 依赖 / 顺序

- **前置**：chg-01（契约自动化 + apply-all bug）——需要 `harness status --lint` / `harness validate --contract all` 为本 change 的对人文档自检提供工具。
- **后置**：chg-03 / chg-04 / chg-05 可依赖 chg-02 的 `_reset_ff_mode_after_done_archive` helper 稳定性（但实际无代码耦合，顺序依赖即可）。
- **内部 Step 顺序**（见 plan.md）：Step 1（sug-27 ff_mode 自动关，最轻量，阻塞 req-31 自证）→ Step 2（sug-16 _sync_stage 改造）→ Step 3（sug-21 bugfix ff 分支补 sync）→ Step 4（sug-18 subagent timeout）→ Step 5（sug-09 next --execute，最重）。

## 10. 风险与缓解

| 风险 ID | 风险描述 | 缓解措施 |
|---------|---------|---------|
| R1 | `_sync_stage_to_state_yaml` 改为"总是初始化 dict" 后，可能对不含该字段的历史 yaml 产生 schema 漂移，触发既有测试 grep 断言失败 | 兼容策略：仅当 `new_stage in STAGE_WHITELIST` 时初始化；其他 stage（如 archive、suggestion）保持原逻辑；grep 现有测试全覆盖 |
| R2 | `_reset_ff_mode_after_done_archive` 调用点散落（`workflow_next` / `archive_requirement` / `workflow_ff_auto`），遗漏任何一处都会回归 sug-27 现象 | Step 1 测试覆盖 3 个入口路径；grep 断言：`ff_mode` 赋值处全部调用新 helper，无直接 `runtime["ff_mode"] = True` 的新代码 |
| R3 | `with_timeout(idle_seconds=300)` 若用 `signal.SIGALRM`，在 non-main thread 会抛错；若用 `asyncio.wait_for`，既有同步 subagent dispatch 代码需改造 | 优先 `asyncio.wait_for`（在 ff_auto 里包一层 event loop），同步 dispatch 改为 `asyncio.run(asyncio.wait_for(coro, timeout))`；若重构成本过高，降级为"在 subagent 入口打时间戳 + 超过阈值打 stderr warning"的软超时 |
| R4 | `workflow_next --execute` 派发 subagent briefing 的 stdout 格式不稳定 → 主 agent 解析失败 | 约定 briefing 以固定 JSON fence（` ```subagent-briefing\n{...}\n``` `）输出；文档化在 `.workflow/context/roles/harness-manager.md`（由 chg-01 已更新） |
| R5 | body 丢失推断：sug-09 原 body 可能有更具体的 subagent 派发接口设想（如 Task 工具 spec）与本 change 选择的"stdout briefing"方案不一致 | executing 阶段若发现遗漏，回补 sug；本方案已标注为"最小可行路径"，不锁死派发接口 |
| R6 | req-31 自身完成时 `ff_mode` 自证依赖 chg-02 先落地 | 依赖顺序 chg-01 → chg-02 强制执行；chg-02 落地后才能启动 chg-03/04/05，保证 ff_mode 自动关在 req-31 archive 前生效 |
