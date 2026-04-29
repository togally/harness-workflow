---
id: chg-01
title: stage 整合（req_review + planning → analysis） + 删 ready_for_execution + next 单入口
requirement: req-50
operation_type: plan
---

# Change Plan

## 1. Development Steps

### Step 1：workflow_helpers.py sequence 改写

- 修改 `WORKFLOW_SEQUENCE = ["analysis", "executing", "testing", "acceptance", "done"]`（原 7 项 → 5 项）。
- `workflow_next` 函数：删除 `if current_stage == "ready_for_execution" and not execute: raise SystemExit(...)` 分支。
- `_NO_BRIEFING_STAGES`：删除 `"ready_for_execution"` 元素。
- `_get_role_for_stage` / `_load_role_stage_map` 兼容：legacy stage 名（`requirement_review` / `planning` / `ready_for_execution`）读到时 stderr WARN「stage X is legacy, mapped to analysis/skipped」不 raise，保持归档历史回放可用。

### Step 2：role-model-map.yaml 更新

- `roles.analyst.stages` 改为 `["analysis"]`（原 `["requirement_review", "planning"]`）。
- `stage_policies` 删 `requirement_review` / `planning` / `ready_for_execution` 三 key；新增：
  ```yaml
  analysis:
    exit_decision: user      # 默认人工拍板（D3 = A），ff 模式自动跳
  ```
- legacy alias 段保留 `requirement-review` / `planning` 已有定义但 alias_of 改为 `analyst` 不变（兼容历史归档 grep）。

### Step 3：cli.py --execute flag 移除

- `next_parser.add_argument("--execute", ...)` 整行删除。
- `if args.command == "next":` 分支：删除 `if args.execute: cmd_args.append("--execute")` 两行。
- 删除文档字符串 / docstring 中含 `--execute` 的提示句（grep 全文）。

### Step 4：ff_auto.py sequence 更新

- ff sequence 引用 `WORKFLOW_SEQUENCE` 自动跟随更新（无硬编码则 no-op）。
- `analysis → executing` 流转点 ack 逻辑：识别 `stage_policies.analysis.exit_decision == "user"` 时 ff 自动 ack，按 `auto_accept` 参数走 low/all/interactive 路径。

### Step 5：context/index.md + stage-role.md + analyst.md + harness-manager.md 同步更新

- `index.md` Stage 出口决策表：删 `requirement_review` / `planning` / `ready_for_execution` 行，新增 `analysis | user | analyst 完成需求澄清 + chg 拆分后用户拍板` 行。
- `stage-role.md` 流转点豁免子条款：`requirement_review → planning` 改为「analysis stage 内 Part A → Part B 子步骤切换」（不需特殊豁免，因不再跨 stage）。
- `analyst.md` 角色定义：「覆盖 stage：[analysis]」；SOP Part A → Part B 结构保留但说明「同 stage 内两阶段，无 stage 切换」；退出条件合并为「analysis 退出条件」单段。
- `harness-manager.md`：派发 / 流转 stage 名引用更新；删除 `--execute` 提示句。

### Step 6：runtime.yaml legacy stage 兼容（本 req 自身）

- 本 req-50 当前 `stage: requirement_review`；chg-01 落地后由 `harness next` 自然推进时，CLI 检测到 legacy stage 名，改写为 `analysis`（一次性迁移）。
- helper `_normalize_legacy_stage(runtime) -> runtime`：读 runtime 时若 `stage in {"requirement_review", "planning"}` → 改为 `analysis`（写回 runtime.yaml）；`stage == "ready_for_execution"` → 改为 `executing`（write WARN 到 stderr）；归档 yaml 不动。

### Step 7：stages.md 流转规则文档更新

- `.workflow/flow/stages.md`：删除 `requirement_review` / `planning` / `ready_for_execution` 流转规则段；新增 `analysis` 段（含 Part A / Part B 子步骤说明 + 退出条件合并版）。

## 2. Verification Steps

### 2.1 单元测试 / 静态核对

- `grep -n "ready_for_execution" src/harness_workflow/*.py` 命中 = 0（除 `_normalize_legacy_stage` legacy 兼容标识 / docstring 历史说明）。
- `grep -n "WORKFLOW_SEQUENCE" src/` → assert 等于 `["analysis", "executing", "testing", "acceptance", "done"]`。
- `grep -n "next --execute\|--execute" src/ docs/ README.md` → 主路径 0 命中（legacy 兼容路径例外）。
- `python -c "from harness_workflow.workflow_helpers import WORKFLOW_SEQUENCE; assert WORKFLOW_SEQUENCE == ['analysis','executing','testing','acceptance','done']"`。
- pytest 现有 test 套全绿；新增 test_workflow_next_no_ready_for_execution.py 覆盖 legacy stage 自动迁移。

### 2.2 手工 smoke / 集成验证

- tmpdir 跑 `harness install` → `harness requirement "smoke req"` → 检查 runtime.yaml `stage: analysis`。
- 手工 `harness next --execute` 应报 `unknown flag` 错误。
- 手工 `harness next` 在 `stage: analysis` 推进到 `stage: executing`（user 拍板模拟）。
- ff 模式：`harness ff --auto --auto-accept all` 跑通 `analysis → executing → testing → acceptance` 不卡住。

### 2.3 AC 映射

- AC-03 → Step 1 + Step 2 + 2.1 grep 断言。
- AC-04 → Step 1 + Step 2 + 2.1 grep `ready_for_execution`。
- AC-06 → Step 3 + 2.2 手工 smoke `--execute` 报错。
- AC-07 → Step 2 + Step 4 + 2.2 ff 模式 smoke。

## 3. 依赖与执行顺序

- 本 chg 是 chg-02 ~ chg-05 的语义底座（stage 名 `analysis` 必须先确定，chg-03 / chg-04 文档模板才能正确引用）。
- 内部硬序：Step 1 → Step 2 → Step 3 → Step 4 → Step 5 → Step 6 → Step 7（Step 1 改 sequence 必须最先，Step 6 是收口迁移）。
- 不依赖任何外部 chg。

## 4. 测试用例设计

> regression_scope: full  # 改 `full` 触发：本 chg 改 `WORKFLOW_SEQUENCE`（核心 helper 入口分发逻辑）+ runtime stage 名（状态格式）+ CLI flag 注册（CLI 入口）三类破坏面广点
> 波及接口清单：
> - `src/harness_workflow/workflow_helpers.py::WORKFLOW_SEQUENCE`（常量）
> - `src/harness_workflow/workflow_helpers.py::workflow_next`（函数）
> - `src/harness_workflow/workflow_helpers.py::_NO_BRIEFING_STAGES`（常量）
> - `src/harness_workflow/workflow_helpers.py::_get_role_for_stage`（函数，legacy 兼容）
> - `src/harness_workflow/workflow_helpers.py::_normalize_legacy_stage`（新增 helper）
> - `src/harness_workflow/cli.py::build_parser`（next_parser 注册）
> - `src/harness_workflow/cli.py::main`（next 分支）
> - `src/harness_workflow/ff_auto.py::workflow_ff_auto`（auto-advance 链路）
> - `.workflow/context/role-model-map.yaml::stage_policies`（schema）
> - `.workflow/context/role-model-map.yaml::roles.analyst.stages`（schema）
> - `.workflow/context/index.md::Stage 出口决策表`（文档镜像）
> - `.workflow/context/roles/analyst.md::覆盖 stage` 字段
> - `.workflow/context/roles/harness-manager.md::派发说明`
> - `.workflow/context/roles/stage-role.md::流转点豁免子条款`
> - `.workflow/flow/stages.md`

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|---|---|---|---|---|
| TC-01 | `from workflow_helpers import WORKFLOW_SEQUENCE` 后断言长度 | 长度 = 5 且首项 == "analysis" | AC-03 | P0 |
| TC-02 | grep `ready_for_execution` 在 `src/harness_workflow/` 主路径（排除 legacy 兼容标识与 docstring 历史） | 命中 = 0 | AC-04 | P0 |
| TC-03 | `harness next --execute` 在 tmpdir 执行 | 退出码非 0 + stderr 含 `unknown flag` 或 `unrecognized arguments` | AC-06 | P0 |
| TC-04 | `stage_policies.analysis.exit_decision` 读 yaml | 值等于 `"user"` | AC-07 | P0 |
| TC-05 | runtime.yaml `stage: requirement_review`（legacy）经 `_normalize_legacy_stage` 处理 | 写回后 `stage: analysis`，stderr WARN 一行 | AC-03 + AC-11 | P0 |
| TC-06 | runtime.yaml `stage: ready_for_execution`（legacy）经 `_normalize_legacy_stage` 处理 | 写回后 `stage: executing`，stderr WARN 一行 | AC-04 + AC-11 | P0 |
| TC-Dogfood-01 | tmpdir 完整 5-stage 流程：`harness install` → `harness requirement "TC dogfood"` → `harness next` × N → `stage: done` | runtime stage 历经 `analysis → executing → testing → acceptance → done`；`feedback.jsonl` 至少 4 个 `stage_advanced` 事件；零 `ready_for_execution` 出现 | AC-03 + AC-04 + AC-06 + AC-07 + AC-08 | P0 |
| TC-Dogfood-02 | tmpdir ff 模式：`harness install` → `harness requirement "ff dogfood"` → `harness ff --auto --auto-accept all` | runtime stage 自动推进到 `acceptance`（user 拍板点全 ack）；零 `ready_for_execution` | AC-07 + AC-08 | P0 |
| TC-07 | 归档历史 req-46 yaml 含 `stage_timestamps` 旧字段 | `harness archive` / `harness status` 不 raise；旧字段原样保留 | AC-11 | P1 |
| TC-08 | `harness next` 在 `stage: planning`（legacy 历史归档回放） | 检测到 legacy stage 后 stderr WARN，自动迁移到 `analysis` 并继续推进 | AC-11 | P1 |

**dogfood 必填字段（TC-Dogfood-01）**：

- 用例名：TC-Dogfood-01
- tmpdir fixture：`tmp_path` pytest fixture
- 子进程命令：`subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'next'], cwd=tmp_path, capture_output=True)`
- stdout 断言：含 `stage advanced to`
- runtime stage 断言：`yaml.safe_load((tmp_path / '.workflow/state/runtime.yaml').read_text())['stage']` 经 5 次 next 后等于 `"done"`
- `feedback.jsonl` 事件数断言：≥ 4 条 `stage_advanced` 事件
- 对应 AC：AC-03 + AC-04 + AC-06 + AC-07 + AC-08
- 优先级：P0
