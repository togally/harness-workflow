# Change

## 1. Title

CLI 路径迁移 flow layout（FLOW_LAYOUT_FROM_REQ_ID + create_*/archive_ 改写）

## 2. Goal

- 在 `workflow_helpers.py` 新增常量 `FLOW_LAYOUT_FROM_REQ_ID = 41` 与 helper `_use_flow_layout(req_id) -> bool`，改写 `create_requirement` / `create_change` / `create_regression` / `archive_requirement` 四个 handler，让 req-id ≥ 41 的机器型工件全部落到 `.workflow/flow/requirements/{req-id}-{slug}/...` 下；req-id ∈ [39, 40] 维持 state/ legacy fallback；req-id ≤ 38 维持原 legacy。

## 3. Requirement

- `req-41`（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））

## 4. Scope

### Included

- `src/harness_workflow/workflow_helpers.py`：
  - 新增常量 `FLOW_LAYOUT_FROM_REQ_ID = 41`（与既有 `LEGACY_REQ_ID_CEILING = 38` / `FLAT_LAYOUT_FROM_REQ_ID = 39` 并列）；
  - 新增 helper `_use_flow_layout(req_id: str) -> bool`（解析数字部分 ≥ 41 → True，非法 id → False）；保证 `_use_flow_layout(x) → True` 时 `_use_flat_layout(x)` 同样 True（flow 层是 flat 层的超集）；
  - 扩展 path resolver：`resolve_requirement_root` / `resolve_requirement_reference` / `_resolve_target` / `load_requirement_runtime` 同步识别 `.workflow/flow/requirements/{req-id}-{slug}/` 新位；
- CLI handler 改写（位于 `workflow_helpers.py` 或对应 command 模块）：
  - `create_requirement`：req-id ≥ 41 → `.workflow/flow/requirements/{req-id}-{slug}/requirement.md`；
  - `create_change`：req-id ≥ 41 → `.workflow/flow/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/{change.md, plan.md, session-memory.md}`；
  - `create_regression`：req-id ≥ 41 → `.workflow/flow/requirements/{req-id}-{slug}/regressions/{reg-id}-{slug}/{regression.md, ...}`；
  - `archive_requirement`：req-id ≥ 41 → 整体搬 `.workflow/flow/requirements/{req-id}-{slug}/` 到 `.workflow/flow/archive/{branch}/req-{req-id}-{slug}/`；artifacts/ 下对人产物维持现行归档逻辑；
- pytest：
  - 新增 `tests/test_use_flow_layout.py`（或并入既有 fixture 文件）含 ≥ 4 条用例：req-40（阶段合并）→ False / req-41（本需求：机器型工件回 flow）→ True / req-50（未来虚拟）→ True / 非法 id（空 / null / `abc`）→ False；
  - 新增 `test_create_requirement_flow_layout_req_41` / `test_create_change_flow_layout_req_41` / `test_create_regression_flow_layout_req_41` / `test_archive_requirement_flow_layout_req_41`（tempdir dry-run，断言路径落位）；
  - 维持既有 `create_*` 测试对 req-39（对人文档家族契约化）/ req-40（阶段合并）行为不变（legacy fallback 不破坏）；
- 涉及文件：
  - `src/harness_workflow/workflow_helpers.py`
  - `tests/test_use_flow_layout.py`（新）/ 并入 `tests/test_create_requirement.py` / `tests/test_create_change.py` / `tests/test_archive_requirement.py`（按既有组织方式）

### Excluded

- **不动** `.workflow/flow/repository-layout.md`（归属 chg-01（repository-layout 契约底座），本 chg 依赖其作为权威路径源）；
- **不动** `validate_human_docs.py` 扫描逻辑（归属 chg-03（validate_human_docs 重写删四类 brief））；
- **不动** 角色文件（归属 chg-04（角色去路径化 + brief 模板删 + usage-reporter 废止））；
- **不修改** `record_subagent_usage` 内部实现（已实现，chg-06（harness-manager Step 4 派发硬门禁）接入链路）；
- **不迁移** req-39 / req-40 已落地的 state/sessions/ 内容（AC-06 要求不破坏）；
- **不改** `.workflow/state/feedback/` / `runtime.yaml` / `action-log.md` 位置（Excluded 明文声明）。

## 5. Acceptance

- Covers requirement.md **AC-03**（`FLOW_LAYOUT_FROM_REQ_ID` + `_use_flow_layout` helper 落地）：
  - `grep -q "FLOW_LAYOUT_FROM_REQ_ID = 41" src/harness_workflow/workflow_helpers.py`；
  - `grep -q "_use_flow_layout" src/harness_workflow/workflow_helpers.py`；
  - `pytest tests/ -k "test_use_flow_layout" -v` ≥ 4 用例 PASS（req-40 False / req-41 True / req-50 True / 非法 id False）。
- Covers requirement.md **AC-04**（create_* 路径校验）：
  - `pytest tests/ -k "test_create_requirement_flow_layout_req_41" -v` PASS，断言 `requirement.md` 落 `.workflow/flow/requirements/req-41-{slug}/requirement.md`；
  - `pytest tests/ -k "test_create_change_flow_layout_req_41" -v` PASS，断言 `change.md` + `plan.md` 落 `.workflow/flow/requirements/req-41-{slug}/changes/{chg-id}-{slug}/`；
  - `pytest tests/ -k "test_create_regression_flow_layout_req_41" -v` PASS，断言 regression 产物落 `.workflow/flow/requirements/req-41-{slug}/regressions/{reg-id}-{slug}/`；
  - `artifacts/` 下断言不写机器型文件（四类 brief 空壳由 chg-03（validate_human_docs 重写删四类 brief）配套跳过扫描）。
- Covers requirement.md **AC-05**（archive_requirement 路径校验）：
  - `pytest tests/ -k "test_archive_requirement_flow_layout_req_41" -v` PASS，断言 `.workflow/flow/requirements/req-41-{slug}/` 整体搬到 `.workflow/flow/archive/{branch}/req-41-{slug}/`；
  - `.workflow/state/sessions/req-41/` 归档后不存在；
  - `artifacts/{branch}/requirements/req-41-{slug}/` 保留对人产物。
- Covers requirement.md **AC-06**（回归不破坏）：
  - `pytest tests/` 全量 PASS；
  - `harness archive req-39` / `harness archive req-40` 行为不变（tempdir mock 验证仍走 state/sessions/ legacy fallback）。

## 6. Risks

- **风险 1：path resolver 改写遗漏导致 legacy req-39/40 行为被误伤**。缓解：executing 开局先 grep `LEGACY_REQ_ID_CEILING` / `FLAT_LAYOUT_FROM_REQ_ID` 所有引用点列表，逐点判断是否需加 flow 分支；pytest 保留既有 req-39/40 用例作回归护栏。
- **风险 2：`archive_requirement` 搬运逻辑对 flow/requirements/ 子树的 regressions/ / task-context/ / usage-log.yaml 漏搬**。缓解：用 `shutil.move`（或 `git mv`）整目录搬运，而非按文件列表白名单；pytest 断言搬运后源目录不存在、目标目录所有子文件 / 子目录都存在。
- **风险 3：`_use_flow_layout` 与 `_use_flat_layout` 语义混淆导致 req-41 既落 flow/ 又落 state/**。缓解：helper 注释明确 `flow ⊂ flat`（flow=True 时 flat=True），CLI handler 先判 flow 再降级 flat 再降级 legacy，三分支互斥；pytest 用例覆盖 flow/flat/legacy 三档。
- **风险 4：pytest fixture 里旧的 `state/sessions/` 硬编码路径导致 req-41 用例假绿**。缓解：新用例独立 tempdir，断言物理路径字符串包含 `.workflow/flow/requirements/req-41`；grep 历史 fixture 文件找 `state/sessions/req-4[1-9]` 硬编码点清理。
