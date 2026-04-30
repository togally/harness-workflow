# Plan — chg-04（trivial 测试降级 + trivial-guard 兜底护栏）

## 1. Steps（按硬序排列）

### Step 1：trivial-guard CLI 实现
- 在 `cli.py` 的 `validate` 子命令加 `--trivial-guard` flag；
- 在 `validate_trivial_guard(repo_path: Path) -> tuple[bool, list[str]]` helper（`workflow_helpers.py`）：
  - 跑 `git diff --shortstat` → 解析行数 / 文件数 → 阈值校验；
  - 跑 `subprocess.run(["pytest", "-q"])` → 验证 exit 0；
  - grep `^\+(import |from .* import)` → 验证无新增 import；
  - 跑 `harness validate --contract all` → 验证 exit 0；
  - 收集所有失败原因到 list；
  - 返回 `(all_passed: bool, failures: list[str])`。
- 单测 `tests/test_validate_trivial_guard.py`：6 用例（全通过 / 行数超 / 文件数超 / pytest 红 / 新增 import / contract lint 红）。

### Step 2：harness next 自动跑 trivial-guard
- 修改 `cli.py` 的 `harness next` 流转逻辑：
  - 在 stage = executing → done 流转点检查：若 task_type=trivial OR 当前 chg trivial=true：
    - 调 `validate_trivial_guard(repo_path)`；
    - 失败 → runtime stage 回切 executing + task_type 升级为 bugfix（保留升级痕迹 `upgraded_from: trivial`）+ echo 升级提示句；
    - 成功 → 流转到 done。
- 单测 `tests/test_harness_next_trivial_guard.py`：4 用例（trivial 通过 → done / trivial 超阈值 → 升级 bugfix / chg 级 trivial 升级 / 标准任务跳过 trivial-guard）。

### Step 3：trivial → bugfix 升级 helper
- 新增 `migrate_trivial_to_bugfix(req_dir: Path)`：
  - 读取 trivial-spec.md 3 段；
  - 拷贝到新建 bugfix.md（标准 bugfix 模板）；
  - 不删除 trivial-spec.md（保留审计痕迹）；
  - 更新 runtime.yaml task_type=bugfix + upgraded_from=trivial；
- 单测 `tests/test_migrate_trivial_to_bugfix.py`：3 用例（迁移成功 + runtime 字段 + 原文件保留）。

### Step 4：testing.md 加 §trivial 模式段
- 编辑 `.workflow/context/experience/evaluation/testing.md` 末尾加：
  ```markdown
  ## §trivial 模式（req-49 chg-04）

  trivial 通道无 testing stage（TRIVIAL_SEQUENCE = [trivial_define, executing, done]），由 trivial-guard 在 executing → done 流转点兜底：
  - 仅要求新增 1 个 unit test 断言 fix 行为；
  - 全量 pytest 不挂；
  - 跳过 13 TC 设计 / 5 合规扫描 / acceptance 评分。
  - pytest 红 → trivial-guard 自动升级到 bugfix 通道（再走标准 testing）。
  ```
- grep 自检命中。

### Step 5：done.md 加 §trivial 模式段 + 模板落地
- 编辑 `.workflow/context/roles/done.md` 加 §trivial 模式段：
  ```markdown
  ## §trivial 模式（req-49 chg-04）

  当 task_type=trivial（且未触发 trivial-guard 升级）时，done 阶段精简版：
  - 跳过六层回顾（无 planning / testing / acceptance 数据可回顾）；
  - 仅产出 ≤ 200 字 `交付总结.md`（3 段：问题 / 修复 / 验证 各 ≤ 60 字）；
  - 经验沉淀轻量版：仅记录 trivial 通道使用心得（≤ 50 字），不强制写 experience/。
  - State 层 usage-log entries 数校验保留（base-role 硬门禁）。
  ```
- 创建模板 `.workflow/flow/requirements/_templates/trivial-交付总结.md`；
- scaffold_v2 mirror 同步；
- 单测 `tests/test_done_trivial_mode.py`：3 用例（产出 ≤ 200 字 + 落位正确 + 跳六层回顾标识）。

### Step 6：硬门禁六 / 七 / 契约 7 自检
- 升级提示句 grep 自检带 ≤ 15 字描述；
- stdout 不出现 A/B/C 选项句式；
- 升级提示句必含「本阶段已结束。」语义等价句式（trivial executing 完成后）。

## 2. 验证

### Unit 测试
- `tests/test_validate_trivial_guard.py`：6 用例；
- `tests/test_harness_next_trivial_guard.py`：4 用例；
- `tests/test_migrate_trivial_to_bugfix.py`：3 用例；
- `tests/test_done_trivial_mode.py`：3 用例。

### Manual 测试
- 创建 trivial 任务 → 改 1 行代码 + 加 1 unit test → `harness next` 流转到 done；
- 创建 trivial 任务 → 改 15 行代码（破阈值）→ `harness next` → 验证升级到 bugfix。

### AC mapping
- AC-04 → Step 1 + Step 2 + Step 3 + tests/test_validate_trivial_guard.py + tests/test_harness_next_trivial_guard.py；
- AC-05 → Step 5 + tests/test_done_trivial_mode.py；
- AC-N4 → Step 1 + Step 4 + Step 5 + tests/test_validate_trivial_guard.py（pytest 校验分支）。

## 3. 硬序约束

- Step 1 → Step 2 → Step 3 → Step 4 → Step 5 → Step 6（线性硬序）；
- 本 chg 完成后才允许进入 chg-05；
- 本 chg 依赖 chg-01 / chg-02 / chg-03 全部已落地。

## 4. 测试用例设计

> regression_scope: full  # 改动跨 harness next 核心流转逻辑 + done 角色行为 + runtime schema 字段（upgraded_from），触发 full 回归
> 波及接口清单（git diff --name-only 自动生成 + 人工补全）：
> - src/harness_workflow/workflow_helpers.py（新增 validate_trivial_guard / migrate_trivial_to_bugfix）
> - src/harness_workflow/cli.py（validate --trivial-guard flag + harness next 流转分支扩 trivial-guard）
> - .workflow/context/experience/evaluation/testing.md（加 §trivial 模式段）
> - .workflow/context/roles/done.md（加 §trivial 模式段）
> - .workflow/flow/requirements/_templates/trivial-交付总结.md（新增）
> - scaffold_v2 mirror 同步
> - 间接波及：所有调用 harness next 的下游测试（确保 task_type ≠ trivial 时不跑 trivial-guard）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 | `validate_trivial_guard(tmpdir_clean_1_line_fix)` | `(True, [])` | AC-04 / AC-N4 | P0 |
| TC-02 | `validate_trivial_guard(tmpdir_15_lines)` | `(False, ["改动量 15 行 > 10 行阈值"])` | AC-04 | P0 |
| TC-03 | `validate_trivial_guard(tmpdir_pytest_failing)` | `(False, ["pytest exit 1"])` | AC-04 / AC-N4 | P0 |
| TC-04 | `validate_trivial_guard(tmpdir_new_import)` | `(False, ["新增 import"])` | AC-04 | P0 |
| TC-05 | `validate_trivial_guard(tmpdir_contract_red)` | `(False, ["contract lint 红"])` | AC-04 | P0 |
| TC-06 | `validate_trivial_guard(tmpdir_3_files)` | `(False, ["改动文件数 3 > 2 阈值"])` | AC-04 | P0 |
| TC-Dogfood-01 | tmpdir trivial 任务 + 1 行 fix + 1 unit test + `harness next` | runtime stage 流转到 done | AC-04 / AC-N4 | P0 |
| TC-Dogfood-02 | tmpdir trivial 任务 + 15 行改动 + `harness next` | runtime stage 回切 executing + task_type=bugfix + stdout 含升级提示句 + upgraded_from=trivial | AC-04 | P0 |
| TC-Dogfood-03 | tmpdir bugfix 内 chg-01 trivial=true + 改动超阈值 + `harness next` | chg-01 trivial=false（升级）+ runtime stage 回切 executing | AC-04 / AC-N1 | P0 |
| TC-Dogfood-04 | tmpdir trivial 任务 done 阶段 | `交付总结.md` 存在 + wc -c ≤ 200 字 + 落 artifacts/.../交付总结.md | AC-05 | P0 |
| TC-07 | `migrate_trivial_to_bugfix(tmpdir)` | bugfix.md 创建 + trivial-spec.md 保留 + runtime task_type=bugfix + upgraded_from=trivial | AC-04 | P0 |
| TC-08 | `harness next` 在 task_type=req（非 trivial）时 | 不调 validate_trivial_guard（跳过分支） | AC-04 | P0 |
| TC-09 | grep `evaluation/testing.md` 含 §trivial 模式段 | 命中 ≥ 1 | AC-N4 | P1 |
| TC-10 | grep `done.md` 含 §trivial 模式段 | 命中 ≥ 1 | AC-05 | P1 |
| TC-11 | 升级提示句 grep 必含「本阶段已结束。」或语义等价 | 命中 ≥ 1 | AC-09 | P1 |
| TC-12（反例） | trivial 任务 done 阶段产出 6 段交付总结 | wc -c > 200 字 → lint 警告 | AC-05 | P1 |
| TC-13（反例） | trivial-guard pytest 红时 stdout 出现 A/B/C 选项 | 0 命中（不诱导用户回选） | AC-09 | P1 |
