# Change Plan

## 1. Development Steps

### Step 1：审计 runtime.yaml 读写路径

- 在 `src/harness_workflow/` 下搜索所有读/写 `runtime.yaml` 的位置（`grep -rn runtime.yaml`、`grep -rn state_root`），列出旁路直写点。
- 确认 `save_requirement_runtime` / `load_requirement_runtime`（或等价函数）是唯一权威入口；若存在旁路，统一收敛到该入口。

### Step 2：扩展 runtime schema 兼容字段

- 在 `save_requirement_runtime` / `load_requirement_runtime` 中：保留 dict 中既有的 `operation_type` 与 `operation_target`（不因字段白名单丢弃），默认值为空字符串。
- 保证 YAML 序列化后字段顺序稳定可读（`operation_type` / `operation_target` 紧跟在 `current_regression` 之后）。

### Step 3：`create_bugfix` 写字段

- 在 `create_bugfix` 的末尾，读出 current runtime → set `operation_type = "bugfix"` 与 `operation_target = "<bugfix-id>"` → 保存。
- 同时确保 `current_requirement` 切换为新 bugfix id，`active_requirements` 追加该 id。

### Step 4：stage 推进同步 bugfix yaml

- 在 `harness next` 的推进路径中（通常由 `advance_stage` 或等价函数负责）：
  - 若当前 `operation_type == "bugfix"`，除更新 runtime.yaml 外，还需把 new stage 同步写入 `.workflow/state/bugfixes/<id>.yaml`。
  - 若读入 bugfix yaml 不存在，则新建；已存在则只 patch stage 字段。

### Step 5：一次性回填脚本

- 新增 `scripts/backfill_bugfix_runtime.py`：
  - 读 `.workflow/state/runtime.yaml` 的 `current_requirement`。
  - 如果该 id 以 `bugfix-` 前缀开头且 `operation_type`/`operation_target` 为空，set 两字段并保存。
  - 打印回填结果，支持 `--dry-run`。

### Step 6：新增测试 `tests/test_bugfix_runtime.py`

- 覆盖 3 条断言：
  - (a) 在 tempdir 中 `create_bugfix("demo")` 后，runtime.yaml 的 `operation_type == "bugfix"` 且 `operation_target == "bugfix-01"` 类值。
  - (b) 读 → 写 → 再读，字段完整保留。
  - (c) 模拟 stage 推进到 `planning`，读 `.workflow/state/bugfixes/bugfix-01.yaml`，stage 字段已同步。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `pytest tests/test_bugfix_runtime.py -v` 全绿。
- `grep -n "operation_type" src/harness_workflow/workflow_helpers.py` 能同时看到 save / load / create_bugfix 三处引用。
- `grep -rn "runtime.yaml" src/harness_workflow/` 除唯一入口外无其他直写。

### 2.2 Manual smoke / integration verification

- 在 tempdir 初始化 harness 仓库 → `harness bugfix "smoke"` → 查 runtime.yaml 有 `operation_type`/`operation_target`；`harness next` 一次后字段仍在；`.workflow/state/bugfixes/bugfix-01.yaml` 的 stage 与 runtime.yaml 一致。
- 运行 `python scripts/backfill_bugfix_runtime.py --dry-run`，对缺字段的历史 bugfix 能识别出来但不写入。

### 2.3 AC Mapping

- AC-12 -> Step 2/3/4/6 + 2.1 + 2.2

## 3. Dependencies & Execution Order

- 依赖 chg-01 先合入（同一文件 `workflow_helpers.py` 修改，减少 merge 冲突）。
- chg-03 依赖本 change：chg-03 的 bugfix sweep 需要 bugfix yaml 的 stage 与 runtime 一致才能被视为 done；回填脚本也需先跑。
