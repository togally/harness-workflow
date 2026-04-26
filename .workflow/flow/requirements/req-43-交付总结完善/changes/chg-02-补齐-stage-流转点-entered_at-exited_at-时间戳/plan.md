# Change Plan — chg-02（补齐 stage 流转点 entered_at + exited_at 时间戳）

> 所属 req：req-43（交付总结完善）；前置依赖：chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））（无 entries 渲染恒空，AC-06 反例 pytest 才有意义）。

## §目标

解决 AC-06 + req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C）） 实测遗留点 (b)：`harness next` / `harness archive` / 任何引发 stage 流转的 CLI 入口在落 `stage_timestamps[new_stage].entered_at` 时**同时**落 `stage_timestamps[prev_stage].exited_at`；schema 升级走 D-4 default-pick（同级新增 `{stage}_exited_at` 键，**不**嵌套字典，向后兼容）；新增 pytest 覆盖「跳跃流转」+「runtime 与 req yaml 同步」两反例。

## §影响文件列表

- `src/harness_workflow/workflow_helpers.py::_sync_stage_to_state_yaml`（line 5406-5471）：函数签名加 `prev_stage: str | None = None`；当 prev_stage 非空且 prev_stage 在白名单内时，在 `stage_timestamps` dict 同级写 `{prev_stage}_exited_at = now()`；保留既有 `stage_timestamps[new_stage] = now()` 写入逻辑不变。
- `src/harness_workflow/workflow_helpers.py::archive_requirement`（line ~5990 起）：归档前扫 `stage_timestamps`，若 done 等终态 entered_at 缺失则补当前时间作为 `done.entered_at` + 上一格 `_exited_at`（兜底 done 阶段断电式归档）。
- `src/harness_workflow/cli.py`：`harness next` / `harness archive` / `harness ff` 路径调 `_sync_stage_to_state_yaml` 前先从 runtime.yaml 读当前 stage 作为 `prev_stage` 参数传入；改 5-8 处调用点。
- `tests/test_stage_timestamps.py`（**新增**）：覆盖「跳跃流转」（如直接 planning → done） + 「runtime 与 req yaml 同步」（runtime 切 done 但 req yaml 还停 executing 反例）+ 既有 entered_at 不被覆盖等回归点。
- 不动 scaffold_v2 mirror（纯 CLI 源码 + tests，不进 scaffold）。

## §实施步骤

1. 改 `_sync_stage_to_state_yaml` 签名加 `prev_stage: str | None = None` kw-only 参数；逻辑：白名单内的 prev_stage 非空、且 stage_timestamps[prev_stage] 已有 entered_at（旧 schema：纯 ISO 字符串），则同级写 `stage_timestamps[{prev_stage}_exited_at] = now()`；保持 `stage_timestamps[new_stage] = now()` 不变。
2. CLI 层 `harness next` / `harness archive` / `harness ff` 调用点：调 `_sync_stage_to_state_yaml` 前先读 runtime.yaml 的 `stage` 字段作为 `prev_stage` 传入；调用方签名改 6-8 处。
3. `archive_requirement`：归档前扫 stage_timestamps，对 `done` 等终态——若 `stage_timestamps.get("done")` 缺失则补当前时间作为 `done` entered_at + 上一格 `{prev}_exited_at`（兜底 done 阶段断电式归档遗漏）。
4. 写 pytest `tests/test_stage_timestamps.py`（≥ 6 条 case）：白名单内正向流转 / 跨 stage 跳跃 / runtime↔req yaml 不同步 / prev_stage 为 None（兼容老调用方）/ 二次流转不覆盖既有 entered_at / archive 兜底补 done.entered_at。
5. 自检：本 chg 自身（req-43）跑端到端 `harness next` 流转链，最终 req yaml 含完整 entered_at + exited_at 对（每个经历过的 stage）。
6. 收口：`harness validate --human-docs` exit 0 + `pytest tests/` 全绿（基线 + 6 条新 case）。

## §测试用例设计

> regression_scope: targeted（CLI 流转点 + helper 签名扩展，schema 向后兼容，影响面限白名单 stage）
> 波及接口清单（git diff --name-only 预估 + 人工补全）：
> - `src/harness_workflow/workflow_helpers.py::_sync_stage_to_state_yaml`
> - `src/harness_workflow/workflow_helpers.py::archive_requirement`
> - `src/harness_workflow/cli.py`（harness next / archive / ff 调用点）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 正向流转 entered + exited 配对 | 调 `_sync_stage_to_state_yaml(root, "requirement", "req-99", "executing", prev_stage="planning")` | req yaml `stage_timestamps` 含 `planning_exited_at` + `executing`（entered_at） | AC-06 | P0 |
| TC-02 跨 stage 跳跃流转 | planning 直接跳 done（prev_stage="planning", new_stage="done"） | `planning_exited_at` 写入；`done` entered_at 写入；中间 stage 无伪造数据 | AC-06 | P0 |
| TC-03 runtime↔req yaml 同步反例 | runtime.yaml stage="done"，req yaml stage="executing"，触发 archive | archive_requirement 补齐 done.entered_at + executing_exited_at；CLI 不静默吞错 | AC-03 / AC-06 | P0 |
| TC-04 prev_stage=None 兼容老调用方 | 老路径不传 prev_stage | 仅写 new_stage entered_at（与既有行为一致），不写 *_exited_at；不抛异常 | AC-06 | P1 |
| TC-05 二次流转不覆盖既有 entered_at | 同 stage 二次流转（prev=executing, new=executing） | entered_at 保留首次写入值，不被覆盖（既有契约不退化） | AC-06 | P1 |
| TC-06 archive 兜底补 done.entered_at | 归档前 done.entered_at 缺失 | archive_requirement 补当前时间作 done.entered_at + 上一格 _exited_at | AC-03 | P1 |
| TC-07 端到端活证 | 跑 req-43 自身完整流转 planning→executing→testing→acceptance→done | 最终 req yaml 每个 stage 含 entered_at + 上一格的 _exited_at | AC-03 / AC-06 | P0 |

## §验证方式

- **AC-03（per-stage 时间字段齐全）**：TC-03 / TC-06 / TC-07；本 req 自身归档时 grep `entered_at` + `_exited_at` 在 req yaml 中按 stage 配对完整。
- **AC-06（stage 流转点联动写齐时间戳）**：TC-01 / TC-02 / TC-04 / TC-05 helper 单测覆盖正向 + 反例两路径；CLI 入口端到端跑过 ≥ 1 次新流转链路。
- pytest：`pytest tests/test_stage_timestamps.py -v` 全绿 + 基线全量不退化。
- `harness validate --human-docs` exit 0。

## §回滚方式

`git revert` chg-02（补齐 stage 流转点 entered_at + exited_at 时间戳） 的所有 commit；旧 schema（纯 `{stage: entered_at_str}`）天然向后兼容，已写入的 `*_exited_at` 同级键对老 helper 透明（多余字段不报错），无需数据迁移。

## §scaffold_v2 mirror 同步范围

无（本 chg 仅动 `src/harness_workflow/` 下 CLI 源码 + `tests/`，不在 scaffold_v2 mirror 范围内）。

## §契约 7 注意点

- 本 plan.md 首次引用工作项 id 已带 title：req-43（交付总结完善）/ chg-02（补齐 stage 流转点 entered_at + exited_at 时间戳）/ chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））/ req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））。
- 提交信息须形如：`feat: chg-02（补齐 stage 流转点 entered_at + exited_at 时间戳）schema 同级新键 + CLI 联动写入` —— 带 ≤ 15 字描述（硬门禁六）。
- AC-NN 引用首次保持完整（AC-03 / AC-06）；同段后续可简写。
