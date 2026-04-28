# Plan — chg-02（Fix Checklist 首批 3 个 + lint 输出加 fix-checklist 指针）

> 父需求：req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）
> 父 chg：chg-02（Fix Checklist 首批 3 个 + lint 输出加 fix-checklist 指针）
> 执行角色：executing（sonnet），按顺序逐步落地

## 1. Steps

> 硬序：A → B → C → D → E → F → G；不允许并行（C 改 lint 函数依赖 A/B 的 fix-checklist 路径常量，verbose flag 改造在 lint 改造同 commit）。

### Step A：写 `fix-artifact-placement.md`

- 路径：`.workflow/context/checklists/fix-artifact-placement.md`；
- 5 节模板：触发条件 / 修复步骤（编号化命令清单）/ 验证步骤 / 回退路径 / dogfood 样本；
- 修复步骤包含具体 shell 模板（grep 违规 → for-loop mv → cleanup empty dir → re-lint）；
- dogfood 样本引用本会话 PetMall 150 文件迁移路径（保留为示例，不依赖外部仓库存在）。

### Step B：写 `fix-schema-audit.md` + `fix-missing-document.md`

- 路径：`.workflow/context/checklists/fix-schema-audit.md` + `.workflow/context/checklists/fix-missing-document.md`；
- 同 §头部 + 5 节模板；
- fix-schema-audit 修复步骤含三分支决策（migrate / archive / 新建 yaml + 移内容）；
- fix-missing-document 修复步骤按 stage 决定缺什么（requirement_review / planning / executing / etc）。

### Step C：改造 `check_artifact_placement`

- 修改 `src/harness_workflow/validate_contract.py::check_artifact_placement(root: Path, verbose: bool = True) -> int`：
  - 加 `verbose` 参数；
  - PASS 分支：`if verbose: print("PASS: ...")`；
  - FAIL 分支：现有 print 保持 + 加一行 `print(f"fix-checklist: .workflow/context/checklists/fix-artifact-placement.md")` + 调 `raise_harness_block(...)`；
  - import：`from .workflow_helpers import raise_harness_block`。

### Step D：新建 `check_schema_audit` + `check_missing_document`

- 在 `validate_contract.py` 末尾追加两个函数；
- `check_schema_audit(root: Path, verbose: bool = True) -> int`：
  - 扫 `.workflow/state/requirements/req-XX/`（regex `^req-\d+$` 数字目录）+ `.workflow/state/bugfixes/bugfix-XX/`；
  - violations.append + FAIL 输出 + raise_harness_block；
- `check_missing_document(root: Path, verbose: bool = True) -> int`：
  - 读 runtime.yaml；
  - 按 stage 检测必需文件（详见 fix-missing-document.md §修复步骤的清单）；
  - FAIL 时 raise_harness_block；
- 在 `_DISPATCH_TABLE`（或主 main 函数 contract 路由）加两个 entry。

### Step E：CLI 入口加 `--contract schema-audit` + `--contract missing-document`

- 修改 `validate_contract.py::main`（或 cli.py 对应路由）；
- 验证：`harness validate --contract schema-audit` 能跑；`harness validate --contract missing-document` 能跑；
- 不改 `--contract artifact-placement` 既有 CLI 行为（向后兼容）。

### Step F：scaffold_v2 mirror 同步

- 同 commit 同步 3 个 fix-checklist 到 `src/harness_workflow/assets/scaffold_v2/.workflow/context/checklists/`；
- 不需要 mirror `validate_contract.py`（src/ 类）。

### Step G：单测落地

- 路径：`tests/test_fix_checklist_lint_output.py`（新增）；
- 覆盖 9 条用例（详见 §4）。

## 2. 验证

### 2.1 unit

- `pytest tests/test_fix_checklist_lint_output.py -v` 全 PASS（≥ 9 条）；
- 现有 pytest 不回归。

### 2.2 manual

- `harness validate --contract artifact-placement`（PASS 路径）→ 输出 `PASS: ...` + exit 0；
- 手动构造 violations（在 tmpdir 放 `artifacts/main/requirements/req-99-x/planning/session-memory.md`）→ 跑 contract → 看到 `HARNESS_BLOCK: artifact-placement` + `fix-checklist:` + exit 64；
- 检查 `.workflow/state/runtime-block.yaml` 字段完整。

### 2.3 AC mapping

| Step | 对应 AC |
|------|---------|
| A | AC-04（fix-artifact-placement.md 落地）|
| B | AC-04（fix-schema-audit / fix-missing-document.md 落地）|
| C | AC-05（artifact-placement contract 输出改造）|
| D | AC-05（schema-audit + missing-document contract 改造）|
| E | AC-05（CLI 路径）|
| F | AC-07（scaffold_v2 mirror 同步）|
| G | AC-04 / AC-05（单测覆盖）|

## 3. 硬序约束

- chg-02 必须晚于 chg-01：chg-02 的 lint 改造 `from .workflow_helpers import raise_harness_block`，chg-02 的 fix-checklist 头部引用 chg-01 的 error_type 字面表；
- chg-02 必须早于 chg-03：chg-03 的 dogfood pytest 要构造 lint FAIL → 触发 raise_harness_block → 派发 fix-subagent → 端到端验证，所有依赖 chg-02 的 3 个 contract 改造完整；
- 本 chg 内 A → B → C → D → E → F → G 严格硬序（写完 checklist 才能 hard-code 路径常量到 lint；CLI 入口在函数完整后再加；mirror 在功能完整后再做；单测最后兜底）。

## 4. 测试用例设计

> regression_scope: targeted
> 波及接口清单（git diff --name-only 预估 + 人工分析）：
> - `.workflow/context/checklists/fix-artifact-placement.md`（新建）
> - `.workflow/context/checklists/fix-schema-audit.md`（新建）
> - `.workflow/context/checklists/fix-missing-document.md`（新建）
> - `src/harness_workflow/validate_contract.py::check_artifact_placement`（修改：加 verbose + 调 raise_harness_block）
> - `src/harness_workflow/validate_contract.py::check_schema_audit`（新建）
> - `src/harness_workflow/validate_contract.py::check_missing_document`（新建）
> - `src/harness_workflow/validate_contract.py::main`（修改：CLI 路由 +2 contract）
> - `src/harness_workflow/assets/scaffold_v2/.workflow/context/checklists/fix-{artifact-placement,schema-audit,missing-document}.md`（mirror）
> - `src/harness_workflow/cli.py`（如 `--contract` flag 在 cli.py 处理则也改）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01-checklist-3 文件存在 | `ls .workflow/context/checklists/fix-*.md` | 3 文件均 exists；每文件含「## 触发条件 / ## 修复步骤 / ## 验证步骤 / ## 回退路径 / ## dogfood 样本」5 节 | AC-04 | P0 |
| TC-02-artifact-placement-FAIL-block | tmpdir 放 `artifacts/main/requirements/req-99-x/planning/session-memory.md` → 调 `check_artifact_placement(tmp, verbose=True)` | 返回 64；stdout 含 `HARNESS_BLOCK: artifact-placement` + `fix-checklist: .workflow/context/checklists/fix-artifact-placement.md`；`{tmp}/.workflow/state/runtime-block.yaml` 存在且字段完整 | AC-05 | P0 |
| TC-03-artifact-placement-PASS-verbose-True | tmpdir 干净 → 调 `check_artifact_placement(tmp, verbose=True)` | 返回 0；stdout 含 `PASS: artifact-placement lint` | AC-05 | P0 |
| TC-04-artifact-placement-PASS-verbose-False | tmpdir 干净 → 调 `check_artifact_placement(tmp, verbose=False)` | 返回 0；stdout 为空（无 PASS 字串）| AC-05（verbose flag）| P0 |
| TC-05-schema-audit-FAIL | tmpdir 放 `.workflow/state/requirements/req-99/some.yaml` → 调 `check_schema_audit(tmp, verbose=True)` | 返回 64；stdout 含 `HARNESS_BLOCK: schema-audit` + `fix-checklist: ...fix-schema-audit.md` | AC-05 | P0 |
| TC-06-schema-audit-PASS | tmpdir 仅含 `req-99-x.yaml`（非数字目录）→ 调 contract | 返回 0；PASS 输出 | AC-05 | P0 |
| TC-07-missing-document-FAIL | tmpdir 含 runtime.yaml `stage=planning, current_requirement=req-99` 但 `flow/requirements/req-99-x/changes/` 为空 → 调 `check_missing_document(tmp, verbose=True)` | 返回 64；stdout 含 `HARNESS_BLOCK: missing-document` + `fix-checklist: ...fix-missing-document.md`；retry_context 含 `missing` 字段 | AC-05 | P0 |
| TC-08-missing-document-PASS | tmpdir 含完整 chg 子目录 + 模板文件 → 调 contract | 返回 0；PASS 输出 | AC-05 | P0 |
| TC-09-CLI-schema-audit | dogfood 子进程：`subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'validate', '--contract', 'schema-audit'], cwd=tmp, capture_output=True)` | exit 0（如 tmp 无违规）；stderr 不含 unexpected error | AC-05（CLI 路径）| P0 |
| TC-10-CLI-missing-document | 同 TC-09 但 contract=missing-document | exit 0；CLI 不报 `unknown contract` | AC-05 | P0 |
| TC-11-mirror-checklist 同步 | `diff` 三对 fix-*.md 文件 | 输出为空 | AC-07 | P0 |
| TC-12-反例-未知 contract | `harness validate --contract bogus-name` | exit ≠ 0 + stderr 含 `unknown contract` | AC-05（边界）| P1 |
| TC-Dogfood-13-end-to-end-artifact-placement | tmpdir fixture（构造 violation 工件）→ 子进程跑 `harness validate --contract artifact-placement` → assert exit code = 64 + stdout 含 `HARNESS_BLOCK: artifact-placement` + assert `{tmp}/.workflow/state/runtime-block.yaml` 字段完整（error_type / fix_checklist_path / severity / recovery_attempts） | exit 64；runtime-block.yaml schema 完整；feedback.jsonl 事件 ≥ 1（如 contract 落点接通 feedback hook，未接通则免该断言）| AC-05（dogfood TC 必填）| P0 |

> dogfood TC 必填字段（TC-13）：
> - tmpdir fixture：`tmp_path`
> - 子进程命令：`subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'validate', '--contract', 'artifact-placement'], cwd=tmp_path, capture_output=True, text=True)`
> - stdout 断言：含 `HARNESS_BLOCK: artifact-placement` + `fix-checklist:` 行
> - runtime stage 断言：本 chg 不直接动 runtime.yaml stage，故断言 `runtime-block.yaml` 存在 + `error_type=artifact-placement`（替代）
> - feedback.jsonl 事件数：本 chg 不直接产生 feedback 事件（lint 失败不写 feedback），故该字段标 N/A 但 plan 中显式声明
> - 对应 AC：AC-05
> - 优先级：P0
