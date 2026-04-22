# Change Plan

## 1. Development Steps

### Step 1：定位 next / ff CLI 入口与状态写入函数

- 读 `src/harness_workflow/cli/next.py`、`src/harness_workflow/cli/ff.py`（或等价模块），定位 stage 推进核心函数。
- 读 `src/harness_workflow/state/requirements.py`：找到 `write_requirement_state(id, stage, status)` 或等价函数；如不存在则抽一个。
- 盘点当前 `.workflow/state/requirements/{id}.yaml` 的 schema 字段名（`stage` vs `status` 取值、有无 `updated_at`）。

### Step 2：实现"runtime + stage yaml"双写

- 在 `advance_stage(target_stage)` 的函数末尾追加：
  1. 更新 runtime.yaml 的 `stage` 字段；
  2. 更新对应 `requirements/{id}.yaml` 的 `stage` / `status`；
  3. 任何一步失败 → 抛异常并回滚前一步。
- 抽象 `_sync_stage_state(id, new_stage)` 辅助函数，集中处理"双写 + 回滚"逻辑，供 `next` / `ff` 共用。
- 若存在 `updated_at` 字段，顺便刷新时间戳。
- 涉及文件（预期）：
  - `src/harness_workflow/cli/next.py`
  - `src/harness_workflow/cli/ff.py`
  - `src/harness_workflow/state/runtime.py`
  - `src/harness_workflow/state/requirements.py`

### Step 3：覆盖 ff 多步推进场景

- `harness ff` 内部循环调用 `advance_stage`，确保每一步都触发 `_sync_stage_state`。
- 中途如遇异常，停在失败 stage，已写入的中间状态保留（不全量回滚，避免让 ff 行为变反直觉；具体策略以代码注释记录）。

### Step 4：覆盖 regression 状态同步（与 chg-01 协调）

- 如 chg-01 已经把 `regression_stage` 抽为常量，本 change 在 `_sync_regression_stage(id, new_reg_stage)` 中复用；
- regression 不等同 requirement 的 stage，落盘位置可能在 `.workflow/state/regressions/{reg-id}.yaml`，需与 chg-01 约定同一个写入函数。

### Step 5：单元测试

- `tests/test_next_syncs_stage_yaml.py`（新增）：
  - `test_next_writes_requirement_yaml_stage`；
  - `test_ff_multi_step_each_writes_yaml`；
  - `test_next_failure_rolls_back_runtime`（模拟 stage yaml 写入失败）。
- 用 `tmp_path` 搭临时 `.workflow/state/` 结构，跑 CLI 的 programmatic entrypoint（避免 shell 调用不稳）。

### Step 6：端到端回归用例（AC-03 明示）

- `tests/test_full_lifecycle.py`（新增或并入 smoke 用例）：
  1. `harness requirement "demo"` → 新 requirement；
  2. 多次 `harness next` 推进至 `done`；
  3. `harness archive` 无需人工干预成功；
  4. 过程中不直接改任何 yaml；
  5. 断言 `.workflow/state/requirements/{id}.yaml` 在每一步后 `stage` 字段正确。

## 2. Verification Steps

### 2.1 单元测试 + 集成用例

- 运行 pytest，新增单测与集成用例全部通过。

### 2.2 手工 smoke（沙盒仓库）

1. `harness requirement "smoke demo"`；
2. 循环 `harness next` 直到 `done`；
3. 对每一步 `cat .workflow/state/requirements/{id}.yaml | grep stage` → 字段值与 `harness status` 输出一致；
4. `harness archive` 一次成功。

### 2.3 AC 映射

- AC-03 第一条（自动写回）：Step 2 + 2.2 步骤 3；
- AC-03 第二条（完整链路无需手工干预）：Step 6 + 2.2 步骤 4。

## 3. 依赖与执行顺序

- 独立 change，与 chg-01 / 02 / 04 / 05 可并行；
- 回归用例若需 regression 场景，建议 chg-01 先合入以免本 change 的用例误伤。
