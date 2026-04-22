# Change

## 1. Title

修复 harness bugfix / next 闭环：runtime.yaml 持久化 operation_type / operation_target

## 2. Goal

- 让 `harness bugfix "<title>"` 写入 `operation_type: "bugfix"` 与 `operation_target: "<bugfix-id>"` 到 `.workflow/state/runtime.yaml`，并在 `save → load` 往返与后续 `harness next` / `harness status` 中不被裁剪；同时提供一次性回填脚本补齐历史 bugfix。

## 3. Requirement

- `req-28`

## 4. Scope

### Included

- `src/harness_workflow/workflow_helpers.py`（或等价模块）的 `create_bugfix`：在创建 bugfix 后写入 `operation_type` + `operation_target` 到 `runtime.yaml`。
- `load_requirement_runtime` / `save_requirement_runtime`（或等价 dict 化函数）保留 `operation_type` + `operation_target` 字段，不因 schema 白名单被裁剪。
- stage 推进同步：`harness next` 执行时，若 `operation_type == "bugfix"`，把 stage 同步写入 `.workflow/state/bugfixes/<bugfix-id>.yaml`（AC-03 对 bugfix 生效）。
- 一次性回填脚本（`scripts/backfill_bugfix_runtime.py` 或等价）：扫 `.workflow/state/bugfixes/` 已存在的 bugfix，当其是 current_requirement 时补写 `operation_type` + `operation_target`。
- 新增 `tests/test_bugfix_runtime.py`：(a) `create_bugfix` 后字段齐全；(b) `save → load` 往返保留；(c) stage 推进后 bugfix yaml 同步。

### Excluded

- 不对历史 bugfix-3/4/5/6 做 stage 回推——它们的归档由 chg-03 处理。
- 不触碰 `requirement.yaml` 的现有 schema（只加字段、不改字段语义）。
- 不改 `harness regression` 流程本身。

## 5. Acceptance

- Covers requirement.md **AC-12**：`operation_type` / `operation_target` 在 bugfix 周期内持久化，round-trip 不丢；AC-03（state yaml 同步）对 bugfix 生效。

## 6. Risks

- 风险 A：已有代码中 runtime.yaml 序列化路径分散（多处 open/write） → 缓解：集中到 `save_requirement_runtime` 单点，搜索引用确认无旁路写入。
- 风险 B：字段写入与 `conversation_mode` / `locked_*` 等既有字段排序冲突 → 缓解：以 dict 合并为准，保持字段幂等可读。
- 风险 C：回填脚本误触活跃非 current 的 bugfix → 缓解：仅当 bugfix 对应 id == `current_requirement` 时回填，其余跳过并在日志打印。
