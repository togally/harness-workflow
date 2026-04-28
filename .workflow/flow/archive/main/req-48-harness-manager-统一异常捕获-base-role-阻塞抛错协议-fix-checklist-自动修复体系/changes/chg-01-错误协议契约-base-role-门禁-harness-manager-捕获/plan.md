# Plan — chg-01（错误协议契约 + base-role 抛错门禁 + harness-manager 捕获路由）

> 父需求：req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）
> 父 chg：chg-01（错误协议契约 + base-role 抛错门禁 + harness-manager 捕获路由）
> 执行角色：executing（sonnet），按顺序逐步落地

## 1. Steps

> 硬序：A → B → C → D → E → F；不允许并行（C 依赖 A 协议字段稳定，E 依赖 D helper 可 import）。

### Step A：起草 `.workflow/context/error-protocol.md`

- 路径：`.workflow/context/error-protocol.md`
- 章节骨架：
  - §1 目的与范围
  - §2 三层载体形式（stderr / exit code / runtime-block.yaml）
  - §3 error_type 命名规范 + 已知 type 字面表（≥ 6 个）
  - §4 错误结构字段表（error_type / fix_checklist_path / retry_context / severity / detected_by / timestamp / recovery_attempts）
  - §5 runtime-block.yaml schema + 样例
  - §6 harness-manager 捕获语义 + 重试边界（recovery_attempts ≥ 3 升级）
  - §7 fix-checklist 命名规范（`fix-{error-type}.md`）
- 字数 ≤ 1.5 屏，可读性优先。

### Step B：修改 `.workflow/context/roles/base-role.md` 加硬门禁八

- 在「硬门禁清单」总览段加一行 `- 硬门禁八：任务阻塞错误抛出协议（req-48 / chg-01）`；
- 在硬门禁七之后新增 `## 硬门禁八：任务阻塞错误抛出协议（req-48（harness-manager 统一异常捕获...） / chg-01（错误协议契约 + base-role + harness-manager））` 段落；
- 段内含：触发场景（contract FAIL / 必需文档缺失 / 旧目录残留 等）+ 强制三步流程（session-memory 留痕 → runtime-block.yaml 写入 → 调 helper）+ 与硬门禁四 default-pick / 通用准则「职责外问题」的边界划分。

### Step C：修改 `.workflow/context/roles/harness-manager.md` 加 Step 3.7

- 在 `### Step 3.6 派发 Subagent` 段之后新增 `### Step 3.7: 阻塞错误捕获与修复路由（req-48 / chg-01）`；
- 段内含：捕获时机（subagent 返回 exit code ≥ 64 / runtime-block.yaml 非空）→ 解析 error_type → 校验 fix_checklist 存在 → 复用 §3.6 派发协议派发 fix-subagent（model 取自 role-model-map fix-subagent 默认 sonnet，找不到回落 default sonnet）→ 修复完成后 clear runtime-block.yaml + 重试原任务；
- 升级条件：fix_checklist 不存在 / recovery_attempts ≥ 3 / fix-subagent ABORT → 改打 hint + 升级用户。

### Step D：实现 `raise_harness_block` helper

- 路径：`src/harness_workflow/workflow_helpers.py`（追加在文件末尾或合适位置）；
- 签名：`def raise_harness_block(error_type: str, fix_checklist_path: str, retry_context: dict, severity: str = "FAIL", detected_by: str = "", root: Path | None = None) -> int:`
  - 注：返回 int 而非 NoReturn 以便 contract lint 函数调用后继续执行（lint 内部按 return code 决定 exit code，由 CLI 入口统一 exit）；severity=ABORT 时仍 return 65 让上层决定；
- 行为：
  - 写 `{root}/.workflow/state/runtime-block.yaml`（含全字段 + ISO timestamp + recovery_attempts +1 if exists else 1）；
  - 打印 stderr 三行：`HARNESS_BLOCK: {error_type}` / `fix-checklist: {path}` / `severity: {severity}`；
  - 返回 `64`（FAIL）或 `65`（ABORT）；WARN 时返回 `0` 但仍写状态文件（供观测）；
- 复用：load/save_simple_yaml（已存在）。

### Step E：scaffold_v2 mirror 同步

- 同 commit 内 `cp` 三文件到 `src/harness_workflow/assets/scaffold_v2/.workflow/context/`：
  - `error-protocol.md`（新增）
  - `roles/base-role.md`（修改）
  - `roles/harness-manager.md`（修改）
- 不需要 mirror `runtime-block.yaml`（state 类，硬门禁五例外白名单）；
- 不需要 mirror `workflow_helpers.py`（src/ 类，非 .workflow/ 子树）。

### Step F：单测落地

- 路径：`tests/test_raise_harness_block.py`（新增）
- 用例 ≥ 3 条（详见 §4）。

## 2. 验证

### 2.1 unit

- `pytest tests/test_raise_harness_block.py -v` 全 PASS（≥ 3 条）；
- 现有 pytest 不回归（runs_per_session 不超时）。

### 2.2 manual

- `python -c "from harness_workflow.workflow_helpers import raise_harness_block; ..."` 能 import 成功；
- 手动构造样例：`raise_harness_block("artifact-placement", ".workflow/context/checklists/fix-artifact-placement.md", {"task": "test"}, "FAIL", "executing", root=Path("/tmp/foo"))` 后 grep `runtime-block.yaml` 字段存在。

### 2.3 AC mapping

| Step | 对应 AC |
|------|---------|
| A | AC-01（error-protocol.md 协议契约落地）|
| B | AC-02（base-role.md 新硬门禁）|
| C | AC-03（harness-manager.md 新职责）|
| D | AC-01（helper 是协议落地的工程实现）|
| E | AC-07（scaffold_v2 mirror 同步）|
| F | AC-01 / AC-02 / AC-03（单测覆盖三个产物）|

## 3. 硬序约束

- chg-01 必须先于 chg-02：chg-02 的 fix-checklist 文件在 §头部 frontmatter 中要引用 error-protocol.md §3 的 error_type 字面表；chg-02 的 lint 输出改造要 `from workflow_helpers import raise_harness_block`；
- chg-01 必须先于 chg-03：chg-03 的 dogfood pytest 用例需要 helper + 协议契约 + 角色文档全部到位才能 e2e 跑通；
- 本 chg 内 Step A → B → C → D → E → F 严格硬序（C/B 文档稳定后再写 helper；helper 完成后再 mirror；mirror 完成后单测验收，避免漂移）。

## 4. 测试用例设计

> regression_scope: targeted
> 波及接口清单（git diff --name-only 预估 + 人工分析）：
> - `.workflow/context/error-protocol.md`（新建）
> - `.workflow/context/roles/base-role.md`（修改：硬门禁八段落）
> - `.workflow/context/roles/harness-manager.md`（修改：Step 3.7 段落）
> - `src/harness_workflow/workflow_helpers.py::raise_harness_block`（新建函数）
> - `src/harness_workflow/assets/scaffold_v2/.workflow/context/error-protocol.md`（mirror）
> - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md`（mirror）
> - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md`（mirror）
> - `.workflow/state/runtime-block.yaml`（新建运行时状态文件，由 helper 写入）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01-helper-FAIL | `raise_harness_block("artifact-placement", "fix-x.md", {"task":"t"}, "FAIL", "executing", root=tmp)` | 返回 64；`runtime-block.yaml` 含 error_type=artifact-placement / severity=FAIL / recovery_attempts=1；stderr 含 `HARNESS_BLOCK: artifact-placement` 三行 | AC-01 | P0 |
| TC-02-helper-ABORT | severity=ABORT 调用，其他同 TC-01 | 返回 65；`runtime-block.yaml` severity=ABORT；stderr 含 `severity: ABORT` | AC-01 | P0 |
| TC-03-helper-WARN | severity=WARN 调用 | 返回 0；`runtime-block.yaml` 仍写入 severity=WARN；stderr 三行存在 | AC-01 | P0 |
| TC-04-helper-累计-attempts | 同 root + 同 error_type 调用 2 次 | 第 2 次 `runtime-block.yaml` recovery_attempts=2 | AC-01 / AC-03（重试边界）| P0 |
| TC-05-error-protocol-md 字段完整 | `cat error-protocol.md` | 含 §1~§7 章节 + ≥ 6 个 known error_type 字面 | AC-01 | P0 |
| TC-06-base-role 硬门禁八存在 | grep `硬门禁八：任务阻塞错误抛出协议` base-role.md | 命中 ≥ 1 次（总览段 + 详细段）| AC-02 | P0 |
| TC-07-harness-manager Step 3.7 存在 | grep `Step 3.7` harness-manager.md | 命中 ≥ 1 次；段内含「fix-checklist」「recovery_attempts」关键词 | AC-03 | P0 |
| TC-08-反例-helper-未知 severity | severity="UNKNOWN" 调用 | 抛 `ValueError` 含 "severity must be FAIL/ABORT/WARN" | AC-01（边界）| P1 |
| TC-09-mirror diff 一致 | `diff .workflow/context/error-protocol.md src/harness_workflow/assets/scaffold_v2/.workflow/context/error-protocol.md` | 输出为空 | AC-07 | P0 |
| TC-10-base-role 硬门禁八 mirror | `diff .workflow/context/roles/base-role.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md` | 输出为空 | AC-07 | P0 |
| TC-11-harness-manager Step 3.7 mirror | `diff .workflow/context/roles/harness-manager.md src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md` | 输出为空 | AC-07 | P0 |
| TC-12-helper-runtime-block-字段-schema | TC-01 后读 yaml | 字段集合等于 {error_type, fix_checklist_path, retry_context, severity, detected_by, timestamp, recovery_attempts} | AC-01（schema 完整性）| P1 |

> 备注：本 chg 不涉及 CLI 入口（无 `harness next` / `harness install` 等子命令调用 helper），故无强制 dogfood TC；end-to-end dogfood 在 chg-03 落地。
