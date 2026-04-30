# Plan — chg-02（trivial 准入判据 + 自动识别 hint）

## 1. Steps（按硬序排列）

### Step 1：改动类型分类 helper
- 在 `workflow_helpers.py` 新增 `classify_diff_change_types(diff_output: str) -> set[str]`：
  - 输入：`git diff --no-color` 的字符串输出；
  - 输出：改动类型集合（如 `{"typo", "doc"}`）；
  - 实现：
    - 按 `diff --git` 分块每文件；
    - 文件后缀 `.md` / `.txt` / `.rst` → `doc`；
    - 文件后缀 `.json` / `.yaml` / `.toml` 且改动行 `=` 右侧字面量替换 → `config_constant`；
    - 文件后缀 `.py` 且 `+# ` / `-# ` 行占多数 → `comment`；
    - 单 token 替换（`-foo + foe` 形态）→ `typo`；
    - 改动行全为 `-` 行（删行）且非测试文件 → `dead_code`；
    - 改动行命中 lint 关键词（`flake8` / `mypy` / `# noqa`）→ `lint`；
    - 字符串字面量改动（`+"..." -"..."`）→ `string`；
    - 其他 → `other`（一票否决）。
- 单测 `tests/test_classify_diff_types.py`：覆盖 8 类正例 + 1 反例（other）。

### Step 2：trivial 准入判据 helper
- 新增 `validate_trivial_eligibility(repo_path: Path) -> tuple[bool, str]`：
  - 步骤 1：跑 `git diff --shortstat` → 解析 `(files, insertions, deletions)`；
  - 步骤 2：若 `files == 0` → `(False, "no diff")`；
  - 步骤 3：若 `insertions + deletions > 10` → `(False, "改动量 {n} 行 > 10 行阈值")`；
  - 步骤 4：若非测试文件数 > 2 → `(False, "改动文件数 {m} > 2 阈值")`；
  - 步骤 5：跑 `git diff --no-color` → 调 `classify_diff_change_types`：
    - 若集合含 `other` → `(False, "改动类型含 other，未命中白名单")`；
    - 否则继续；
  - 步骤 6：影响面校验 — `git diff` grep `^\+(import |from .* import)` 命中 ≥ 1 → `(False, "新增 import")`；
  - 步骤 7：全部通过 → `(True, "trivial 候选 — {n} 行 / {m} 文件 / 类型 {types}")`。
- 单测 `tests/test_validate_trivial_eligibility.py`：覆盖 5 正例（typo / 单行 string / 单行 doc / 删 1 行 dead_code / 改 1 行 config_constant）+ 5 反例（11 行超阈值 / 3 文件超阈值 / 含 other 类型 / 新增 import / 空 diff）。

### Step 3：`harness bugfix` 入口 hint
- 在 `cli.py` 的 `bugfix` 子命令 handler 开头加：
  ```python
  if not args.force_full:
      ok, reason = validate_trivial_eligibility(repo_path)
      if ok:
          print(f"检测到改动量 = {n} 行 / {m} 文件 / 仅 {types} 类改动，建议改用 `harness trivial \"{title}\"` 通道（节省 ~80% 流程节拍）。")
          print("继续走 bugfix 输入 `--force-full` 抑制本提示。")
          print("trivial 通道自检：① 仅改 ≤ 10 行 / ② 不引入新依赖 / ③ 不改 API 签名")
  # 不阻塞，继续原有 bugfix 逻辑
  ```
- 加 `--force-full` flag。
- 单测 `tests/test_cli_bugfix_hint.py`：子进程跑 `harness bugfix "test"` 在 1 行改动 fixture 下断言 stdout 含 hint；加 `--force-full` 时 stdout 不含 hint。

### Step 4：`harness requirement` 入口 hint（同形态）
- 在 `cli.py` 的 `requirement` 子命令同样加 hint + `--force-full` flag；
- 单测 `tests/test_cli_requirement_hint.py`：同 bugfix。

### Step 5：硬门禁六 / 七 自检
- hint 文案中所有 id 引用（如 `req-49`）grep 自检带 ≤ 15 字描述；
- stdout 不出现 A/B/C 选项句式（hint 是单向建议，不诱导用户回选）。

## 2. 验证

### Unit 测试
- `tests/test_classify_diff_types.py`：9 用例；
- `tests/test_validate_trivial_eligibility.py`：10 用例（5 正例 + 5 反例）；
- `tests/test_cli_bugfix_hint.py`：4 用例（hint 出现 / `--force-full` 抑制 / 大改动不出 hint / 空 diff 不出 hint）；
- `tests/test_cli_requirement_hint.py`：4 用例。

### Manual 测试
- 在仓库中改一行 typo → `harness bugfix "test"` 检查 stdout；
- 改 30 行代码 → `harness bugfix "test"` 验证不出 hint。

### AC mapping
- AC-03 → Step 1 + Step 2 + tests/test_classify_diff_types.py + tests/test_validate_trivial_eligibility.py；
- AC-N2 → Step 3 + Step 4 + tests/test_cli_bugfix_hint.py + tests/test_cli_requirement_hint.py。

## 3. 硬序约束

- Step 1 → Step 2 → Step 3 → Step 4 → Step 5（线性硬序）；
- 本 chg 完成后才允许进入 chg-03；
- 本 chg 依赖 chg-01 已落地的 task_type 枚举（hint 文案需 `harness trivial` 命令存在才有意义）。

## 4. 测试用例设计

> regression_scope: targeted  # 改动局限于新增 helper + CLI 入口 hint 注入；不改既有 helper / 状态机
> 波及接口清单（git diff --name-only 自动生成 + 人工补全）：
> - src/harness_workflow/workflow_helpers.py（新增 classify_diff_change_types / validate_trivial_eligibility）
> - src/harness_workflow/cli.py（bugfix / requirement 子命令开头 hint 注入 + --force-full flag）
> - 间接波及：所有 CLI 调用 bugfix / requirement 的下游测试 fixture（stdout 断言可能受影响）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 | `classify_diff_change_types(typo_diff)` | `{"typo"}` | AC-03 | P0 |
| TC-02 | `classify_diff_change_types(doc_diff)` | `{"doc"}` | AC-03 | P0 |
| TC-03 | `classify_diff_change_types(complex_logic_diff)` | `{"other"}` | AC-03 | P0 |
| TC-04 | `validate_trivial_eligibility(tmpdir_with_1_line_typo)` | `(True, "...")` | AC-03 | P0 |
| TC-05 | `validate_trivial_eligibility(tmpdir_with_15_lines)` | `(False, "改动量 15 行 > 10 行阈值")` | AC-03 | P0 |
| TC-06 | `validate_trivial_eligibility(tmpdir_with_3_files)` | `(False, "改动文件数 3 > 2 阈值")` | AC-03 | P0 |
| TC-07 | `validate_trivial_eligibility(tmpdir_with_new_import)` | `(False, "新增 import")` | AC-03 | P0 |
| TC-08 | `validate_trivial_eligibility(tmpdir_with_empty_diff)` | `(False, "no diff")` | AC-03 | P0 |
| TC-09 | `validate_trivial_eligibility(tmpdir_with_complex_logic)` | `(False, "改动类型含 other...")` | AC-03 | P0 |
| TC-10（正例 5 类） | typo / string / comment / doc / config_constant 各 1 fixture | 全 `(True, _)` | AC-03 | P0 |
| TC-Dogfood-01 | tmpdir 子进程 1 行 typo + `harness bugfix "test"` | stdout 含 `建议改用 harness trivial` | AC-N2 | P0 |
| TC-Dogfood-02 | tmpdir 子进程 1 行 typo + `harness bugfix "test" --force-full` | stdout **不含** hint | AC-N2 | P0 |
| TC-Dogfood-03 | tmpdir 子进程 30 行改动 + `harness bugfix "test"` | stdout **不含** hint（不满足 trivial 阈值） | AC-N2 | P0 |
| TC-Dogfood-04 | tmpdir 子进程 1 行 typo + `harness requirement "test"` | stdout 含 hint | AC-N2 | P0 |
| TC-Dogfood-05 | hint 不阻塞断言：tmpdir + `harness bugfix "test"` 后 runtime.yaml task_type=bugfix（命令仍执行） | runtime task_type 正确写入 | AC-N2 | P0 |
| TC-11（反例） | hint 文案 grep `A[. ]\|B[. ]\|C[. ]` | 0 命中（不出 A/B/C 选项） | AC-09 | P1 |
| TC-12（反例） | hint 文案 grep 裸 `req-49\b` | 命中需带 ≤ 15 字描述 | AC-09 | P1 |

---

## 实施结果 ✅

- ✅ Step 1：classify_diff_change_types（8 类型白名单 + other 一票否决）
- ✅ Step 2：validate_trivial_eligibility（5 步组合判据：行数/文件数/类型/import）
- ✅ Step 3：harness_bugfix.py hint 注入 + --force-full 抑制
- ✅ Step 4：harness_requirement.py hint 注入 + --force-full 抑制
- ✅ Step 5：硬门禁六 / 七 自检（hint 文案无 A/B/C 选项，不阻塞）
- ✅ 单测：17 tests passed（test_trivial_admission.py）
