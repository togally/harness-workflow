# Change Plan

## 1. Development Steps

### Step 1：扩展 `list_done_requirements`

- 在 `workflow_helpers.py` 中为 `list_done_requirements` 增加 `bugfixes/` 扫描分支：
  - 扫 `.workflow/state/requirements/*.yaml` + `.workflow/state/bugfixes/*.yaml`。
  - stage == `done` 的条目都收入候选。
  - 返回结构包含 `kind: req` / `kind: bugfix` 标签。

### Step 2：`archive_requirement` 按 kind 分流

- 入口参数保持 id（如 `bugfix-6`）。
- 根据 id 前缀判定目标根目录：
  - `req-*` → `artifacts/{branch}/archive/requirements/`
  - `bugfix-*` → `artifacts/{branch}/archive/bugfixes/`
- 目录名沿用原工作目录的 slug（例如 `bugfix-6-xxx/`）。
- 归档完成后从 `active_requirements` 移除该 id，保存 runtime.yaml。

### Step 3：一次性 sweep 能力

- 新增 `scripts/sweep_active_bugfixes.py`（或 `harness archive --sweep-bugfixes` 子选项，视实现成本择一）：
  - 输入：`--targets bugfix-3,bugfix-4,bugfix-5,bugfix-6` 或默认扫 `active_requirements` 中所有 `bugfix-*`。
  - 对每个目标：
    - 读 yaml，stage 非 done 则打印警告并提示 `--force-done` 才处理。
    - 满足条件后调用 `archive_requirement`。
  - 默认 `--dry-run`；加 `--apply` 才真正写。

### Step 4：执行 sweep 本 change 范围内 bugfix-3/4/5/6

- 在 plan 执行阶段（executing 角色）按下列顺序实际执行：
  1. `python scripts/sweep_active_bugfixes.py --dry-run`，人工确认目标列表。
  2. 对 yaml stage 非 done 的 bugfix-3/4/5 显式补：`python scripts/sweep_active_bugfixes.py --targets bugfix-3,bugfix-4,bugfix-5 --force-done --apply`。
  3. `python scripts/sweep_active_bugfixes.py --targets bugfix-6 --apply`（chg-02 回填后应为 done 状态）。
- 完成后 `harness status` 验证 `active_requirements` 只剩 req-28。

### Step 5：新增/扩展测试

- 新增 `tests/test_archive_bugfix.py` 或扩展 `tests/test_archive_path.py`：
  - 在 tempdir 构造一个 stage=done 的 bugfix，调用 `archive_requirement` 后断言产物落到 `artifacts/main/archive/bugfixes/`。
  - 断言 `active_requirements` 不再含该 id。
  - 断言 `requirements/` 下的 req 归档路径不受影响（回归覆盖）。

## 2. Verification Steps

### 2.1 Unit tests / static checks

- `pytest tests/test_archive_bugfix.py tests/test_archive_path.py -v` 全绿。
- `grep -n "archive/bugfixes" src/harness_workflow/workflow_helpers.py` 可见分流逻辑。

### 2.2 Manual smoke / integration verification

- 在本仓库跑完 sweep 后：
  - `harness status` 的 `active_requirements` 只显示 `req-28`。
  - `ls artifacts/main/archive/bugfixes/` 能看到 `bugfix-3-*` / `bugfix-4-*` / `bugfix-5-*` / `bugfix-6-*` 四个目录。
  - `.workflow/state/bugfixes/*.yaml` 保持原位（归档不删 state 元数据，仅保留 runtime 中的 active 列表清理）。

### 2.3 AC Mapping

- AC-14 -> Step 1/2/3/4/5 + 2.1 + 2.2

## 3. Dependencies & Execution Order

- 依赖 chg-02 先合入：sweep 需要 chg-02 的回填脚本先给 bugfix-6 补齐 `operation_type` / `operation_target`，并确保 bugfix-6 yaml stage 已是 done（或 force-done）。
- 与 chg-04 / chg-05 / chg-06 之间无强依赖，可并行。
- 本 change 完成后再进入 chg-07（chg-07 的 smoke 会校验 archive 路径正确）。
