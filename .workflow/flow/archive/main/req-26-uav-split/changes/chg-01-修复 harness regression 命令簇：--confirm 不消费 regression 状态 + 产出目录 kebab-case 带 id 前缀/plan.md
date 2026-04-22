# Change Plan

## 1. Development Steps

### Step 1：定位 regression CLI 代码与状态落盘位置

- 读 `src/harness_workflow/cli/` 下 regression 子命令实现，定位 `--confirm` 与目录创建逻辑。
- 读 `src/harness_workflow/state/` 下 regression 状态读写函数（`current_regression` / `regression_stage` 等字段的 setter）。
- 读 `.workflow/state/runtime.yaml` 中 regression 相关字段当前形态，作为回归基线。
- 涉及文件（预期，需在执行阶段确认精确路径）：
  - `src/harness_workflow/cli/regression.py`（或等价模块）
  - `src/harness_workflow/state/regression_state.py`（或状态读写统一入口）
  - `.workflow/state/runtime.yaml`（运行时只读验证，不直接改）

### Step 2：改 `--confirm` 不消费 regression 状态

- 将 `--confirm` 分支从"消费 regression 标记（清 current_regression / 删状态）"改为"仅推进 regression_stage 字段（例如置为 `confirmed`）"。
- 抽取常量，明确 regression_stage 允许的取值（`pending` / `confirmed` / `testing` / `resolved`），集中维护。
- 保留 `--testing` 的入口条件：只要 `current_regression` 不为空、`regression_stage` 不为 `resolved`，就可进入 testing 分支。

### Step 3：改 regression 产出目录命名

- 抽取命名规范辅助函数 `slugify_regression_dir(issue, reg_id)`：
  - 小写化英文字母；
  - 空格 → `-`；
  - 中文保留原字符；
  - 非法路径字符（`/ \ : * ? " < > |` 等）过滤；
  - 前缀 `reg-{id}-` 由 state 分配的下一个序号保证。
- 替换 `harness regression "<issue>"` 中创建工作区目录处的路径构造逻辑。
- 同步修 `.workflow/flow/regressions/` 下子目录创建（如有）。

### Step 4：补/扩回归用例

- 在 `tests/` 下找到现有 regression CLI 的测试模块（命名类似 `test_regression_cli.py`），补：
  - `test_confirm_preserves_regression_state`：
    1. `harness regression "demo issue"` 创建 regression；
    2. `harness regression --confirm demo-issue` 确认；
    3. 断言 `current_regression` 字段未被清空；
    4. `harness regression --testing` 能进入测试分支，不报"no active regression"。
  - `test_regression_dir_uses_kebab_case_with_id_prefix`：
    1. `harness regression "issue with spaces"`；
    2. 断言产出目录路径匹配正则 `^reg-\d+-issue-with-spaces$`；
    3. 断言目录中无空格。
- 若项目采用 pytest，用 `tmp_path` fixture 隔离仓库根路径，避免污染真实 `.workflow/`。

### Step 5：文档与经验沉淀

- 更新 `src/harness_workflow/assets/scaffold_v2/` 下若存在与 regression 目录命名相关的模板说明，同步约束。
- 在 `.workflow/context/experience/roles/regression.md`（或 CLI 工具经验文件）补"confirm 仅推进不消费""目录命名规则"两条经验。

## 2. Verification Steps

### 2.1 单元测试

- 在仓库根运行项目的测试套件（预期是 `pytest`，具体命令待 executing 阶段从 `pyproject.toml` 或 `README` 确认）：
  - 新增 2 条用例全部通过；
  - 原有 regression CLI 用例零回归。

### 2.2 手工 smoke（在沙盒仓库）

1. `harness regression "some weird issue"` → 检查产出目录 `reg-XX-some-weird-issue/`；
2. `harness regression --confirm some-weird-issue`；
3. `cat .workflow/state/runtime.yaml | grep -E 'current_regression|regression_stage'` → `current_regression` 仍有值，`regression_stage: confirmed`；
4. `harness regression --testing` → 进入 testing 分支，无报错。

### 2.3 AC 映射

- AC-01：Step 2 + 2.2 步骤 2-4 共同证明；
- AC-04：Step 3 + 2.2 步骤 1 共同证明。

## 3. 依赖与执行顺序

- 本 change 与 chg-02、chg-03、chg-04、chg-05 彼此独立，可并行实施；
- chg-06（端到端 smoke）依赖本 change 合入。
