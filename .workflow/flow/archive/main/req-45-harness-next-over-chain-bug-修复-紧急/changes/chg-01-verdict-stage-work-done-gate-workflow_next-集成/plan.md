# Plan — chg-01（verdict stage work-done gate + workflow_next 集成）

> 隶属：req-45（harness next over-chain bug 修复（紧急））
> 角色：analyst（opus）落地于 planning stage，按 bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） B1 新契约必含 §4 测试用例设计。

## 1. 目标

修复 dogfood 实证 bug：`harness next` 从 verdict-driven stage（testing / acceptance）出发的 while 自动连跳**未检查**该 stage 关键产物是否真正落地。给 while 连跳条件 `same_role or no_user_decision` 叠加第三条门禁——`_is_stage_work_done(from_s, root, op_target, operation_type)` 必须为 True，否则停在该 stage 不连跳；不破坏 bugfix-5（同角色跨 stage 自动续跑硬门禁） / bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） 已落 same-role 续跑契约和 stage_policies 字段。覆盖 req-45 5 条 AC 全部。

## 2. 影响文件列表

- `src/harness_workflow/workflow_helpers.py`
  - 新增 helper `_is_stage_work_done(stage: str, root: Path, req_id: str, operation_type: str) -> bool`，落于 `_get_exit_decision`（line 7322）之后、`workflow_next`（line 7338）之前。
  - 修改 `workflow_next` 的 while 连跳块（line 7447-7468）：在 `if not (same_role or no_user_decision): break` 之后追加 work-done gate 分支——仅对 `no_user_decision` 路径插桩，`same_role` 路径不加额外门禁（保 bugfix-5 契约）。
- `src/harness_workflow/validate_contract.py`
  - 新增 `check_stage_work_completion(root, stage)`，复用同一 `_is_stage_work_done` helper。
  - `run_contract_cli` 增加 `if contract == "stage-work-completion": ...` 分支；`harness validate --contract all` 自动包含。
- `tests/test_workflow_next_workdone_gate.py`（**新增**）：8 用例（详见 §4）。
- `assets/scaffold_v2/`：经 grep 确认本次新增 helper / contract 子命令均位于 src/ 业务层，**无需** scaffold mirror（详见 §scaffold mirror 段）。

## 3. 实施步骤

1. **实现 `_is_stage_work_done` helper**（`workflow_helpers.py` line 7322 后）：
   - 通过 `_resolve_req_flow_dir(root, req_id, operation_type)`（若已存在则复用）解析 `.workflow/flow/requirements/{req-slug}/` 或 `.workflow/flow/bugfixes/{bugfix-slug}/` 目录；解析失败返回 True（保守降级）。
   - 按 stage 检查关键产物：
     - `testing` → `{req-flow}/test-report.md` 存在且文件中含 `结论` / `§结论` 段及 `PASS|FAIL|PARTIAL` 任一关键字。
     - `acceptance` → `{req-flow}/acceptance/checklist.md` 存在且含 `结论` 段（**与 dogfood 实况对齐**：bugfix-6 / req-43 / req-44 acceptance subagent 实际落 `acceptance/checklist.md`，不是 `acceptance-report.md`；后者属历史 legacy 路径，不再使用）。
     - `planning` → `{req-flow}/changes/chg-*/plan.md` ≥ 1 且每份均含 `## 4` 测试用例设计章节（bugfix-6 B1 契约）。
     - `executing` → 每个 `chg-*/session-memory.md` 末尾含 ✅ 或 `状态：PASS`，且 `tests/` 下至少 1 个 `test_*.py` mtime ≥ stage_entered_at。
     - bugfix 模式：`testing` / `acceptance` 同上；`executing` 改查 `bugfix.md` `§修复方案` 段全部 ✅。
     - `done` / 未知 stage / 解析失败 → 返回 True（避免误阻塞 terminal / regression 出口）。
2. **接通 `workflow_next` while 块**（line 7447-7468）：
   - 在判断 `if not (same_role or no_user_decision): break` 之后追加：
     ```python
     if no_user_decision and not same_role and not _is_stage_work_done(from_s, root, operation_target, operation_type):
         break
     ```
   - **关键**：`same_role` 路径不受 work-done gate 影响（bugfix-5 契约），仅 `no_user_decision` 路径插桩。
3. **新增 `validate_contract.py` 分支**：
   - `check_stage_work_completion(root, stage)` 复用 helper，stdout 列具体缺项（`test-report.md 缺 §结论` / `chg-01/plan.md 缺 §4 测试用例设计` 等）。
   - `run_contract_cli` 加 `stage-work-completion` 分支；`all` 入口自动 fan-out。
4. **新增 `tests/test_workflow_next_workdone_gate.py`**：按 §4 表 8 用例落地，公共 fixture `_make_req_tree(stage, with_artifacts=...)` 抽出文件树构造。
5. **跑 `pytest tests/ -x`**：本测试 8/8 PASS + 全量回归零退化。
6. **跑 `harness validate --contract all`**：bugfix-5 / bugfix-6 既有契约不退化；新增 `stage-work-completion` 分支可正常调用。
7. **dogfood 自验**：本 chg 落地后，模拟 testing 缺 `test-report.md` 时 `harness next` 不应跳过 acceptance；产物齐时连跳行为保留。

## 4. 测试用例设计

> regression_scope: targeted（仅 `workflow_helpers.py` workflow_next + `validate_contract.py` 两文件，bugfix-5 / bugfix-6 契约面已稳定）
> 波及接口清单（git diff --name-only 预估）：
> - `src/harness_workflow/workflow_helpers.py`（新 helper + workflow_next while 插桩）
> - `src/harness_workflow/validate_contract.py`（新增 contract 分支）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 | runtime stage=executing；chg session-memory **缺** ✅ 标记，无新 pytest 文件；调 `workflow_next` | stage 翻到 testing 后 while 在 testing→acceptance 出口断开（work-done gate 检查 testing 时 `test-report.md` 也缺），exit 0 | AC-01 | P0 |
| TC-02 | runtime stage=testing；`test-report.md` **不存在**；调 `workflow_next` | stage 翻到 acceptance 后**不**继续跳 done（acceptance 也无 `acceptance/checklist.md`），exit 0 | AC-02 | P0 |
| TC-03 | runtime stage=acceptance；`acceptance/checklist.md` **缺** §结论；调 `workflow_next` | stage **不**跳 done（停在 acceptance），exit 0 | AC-03 | P0 |
| TC-04 | runtime stage=testing；`test-report.md` 含 `结论：PASS` + `acceptance/checklist.md` 含 §结论；调 `workflow_next` | 连跳 testing → acceptance → done（verdict-driven 连跳保留），exit 0 | AC-04 | P0 |
| TC-05 | runtime stage=requirement_review（analyst 同角色 stage）；planning 产物缺；调 `workflow_next` | 跳 planning（**same_role 路径不受 work-done gate 影响**，保 bugfix-5 契约） | AC-04 | P0 |
| TC-06 | bugfix 模式 runtime stage=testing；`test-report.md` 缺；调 `workflow_next` | stage 跳 acceptance 后停下（bugfix 序列同样受 gate 保护） | AC-01 / AC-02 | P1 |
| TC-07 | `harness validate --contract stage-work-completion`，runtime stage=testing 且 `test-report.md` 缺 | exit 1 + stdout 列具体缺项（包含 `test-report.md`） | AC-05 | P1 |
| TC-08 | `_is_stage_work_done(stage="done", ...)` 或未知 stage / 解析 req-dir 失败 | 返回 True（保守降级，不阻塞 terminal / regression） | AC-04 | P2 |

合计 **8 用例**（4 verdict gate 正负 + 1 same-role 例外 + 1 bugfix 模式 + 1 lint 子命令 + 1 降级），> 需求要求的 ≥ 6。
AC 映射：AC-01（TC-01 / TC-06）/ AC-02（TC-02 / TC-06）/ AC-03（TC-03）/ AC-04（TC-04 / TC-05 / TC-08）/ AC-05（TC-07 + 全部 pytest 数 ≥ 6 满足）。

## 5. 验证方式

- `pytest tests/test_workflow_next_workdone_gate.py -v` → 8/8 PASS。
- `pytest tests/ -x` → 全量回归零退化，确认 bugfix-5 / bugfix-6 既有 `tests/test_workflow_next_*` 用例不破。
- `harness validate --contract stage-work-completion` → dogfood 自验：当前 req-45 testing / acceptance 未跑应 FAIL；executing / planning 已落应 PASS。
- `harness validate --contract all` → bugfix-5 / bugfix-6 既有契约保持 PASS。
- 手动 dogfood：`git stash` 模拟 testing 未产 `test-report.md` → `harness next` → 验 stage 停在 acceptance 不连跳 done。

## 6. 回滚方式

- 单文件本地回滚：`git checkout HEAD -- src/harness_workflow/workflow_helpers.py src/harness_workflow/validate_contract.py tests/test_workflow_next_workdone_gate.py`
- 不涉及 `runtime.yaml` schema / `role-model-map.yaml` schema / `stage_policies` 变更，**无数据迁移**。
- 回滚后退化为 bugfix-5 / bugfix-6 既有行为（连跳但不检查 work-done），手动 Edit `runtime.yaml` workaround 仍可用作兜底。

## scaffold mirror

经 grep 确认：
- `_is_stage_work_done` 新 helper 位于 `src/harness_workflow/workflow_helpers.py`，scaffold 仅复制 `.workflow/` 树，不含 `src/`。
- `validate_contract.py` 新分支同位于 src/，无 scaffold 副本。
- 不修改 `assets/scaffold_v2/.workflow/context/roles/analyst.md`（经 grep 确认 analyst.md 不引用本 helper）。

**结论**：无需 scaffold mirror。

## 契约 7（id + title 硬门禁）

- 本 plan.md / change.md / 新增 `tests/test_workflow_next_workdone_gate.py` docstring 中所有首次引用工作项 id 必须形如 `req-45（harness next over-chain bug 修复（紧急））` / `chg-01（verdict stage work-done gate + workflow_next 集成）` / `bugfix-5（同角色跨 stage 自动续跑硬门禁）` / `bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））` / `sug-38（harness next over-chain bug）` / `sug-46（sug-38 升 P0）`。
- 同段落后续可简写为裸 id；DAG / batched-report / 跨 chg 索引等密集展示场景每个 id 必带 ≤ 15 字描述（硬门禁六批量列举子条款 + 契约 7 反向豁免双向覆盖）。
- 测试文件 docstring 内的工作项引用同样适用。
- 本 plan.md 已遵守。
