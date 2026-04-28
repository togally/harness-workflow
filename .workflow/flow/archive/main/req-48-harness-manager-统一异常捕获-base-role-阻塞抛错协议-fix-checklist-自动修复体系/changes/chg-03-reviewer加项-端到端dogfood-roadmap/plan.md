# Plan — chg-03（reviewer 加项 + 端到端 dogfood + roadmap）

> 父需求：req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）
> 父 chg：chg-03（reviewer 加项 + 端到端 dogfood + roadmap）
> 执行角色：executing（sonnet），按顺序逐步落地

## 1. Steps

> 硬序：A → B → C → D → E；不允许并行（dogfood pytest 必须 reviewer 文档先稳定，roadmap 内容骨架在 dogfood 跑绿后定调）。

### Step A：修改 `.workflow/context/checklists/review-checklist.md`

- 在「六层检查框架·第一层 Context」末尾新增高优先级条目：
  ```
  - [ ] **抛错协议配套（高）**（req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）/ chg-03（reviewer 加项 + 端到端 dogfood + roadmap））：本 stage 新加任何 contract（validate_contract.py 的 check_*）必须配套 .workflow/context/checklists/fix-{error-type}.md；新加任何硬门禁（base-role.md 新段落）必须引用 error-protocol.md 的 HARNESS_BLOCK 协议；缺失视为 FAIL。
  ```
- 在「阶段速查表·done 阶段重点」末尾追加：
  ```
  - [ ] **抛错协议配套抽样（高）**（req-48 / chg-03）：grep `validate_contract.py` 新增 def check_* 函数，逐一核对 fix-*.md 是否存在；grep base-role.md 新增「硬门禁 N」段落，核对 error-protocol.md 引用。
  ```

### Step B：修改 `.workflow/context/roles/reviewer.md`

- 检查 `.workflow/context/roles/reviewer.md` 是否存在；
- 若存在：在 SOP「执行」段加引用本 checklist 项；不重写整文件；
- 若不存在或缺失：在 session-memory.md「待处理捕获问题」记录，并以最小补丁形式补「reviewer 应执行 review-checklist.md 全部条目」；
- 不做大幅重构。

### Step C：写 `tests/test_block_protocol_e2e.py`

- 路径：`tests/test_block_protocol_e2e.py`；
- 3 用例（详见 §4 TC-Dogfood-01/02/03）；
- 复用现有 fixture 模式（参考 `tests/test_workflow_next_subprocess.py`）；
- 每用例闭环：FAIL → assert HARNESS_BLOCK → 模拟 fix → 复跑 → assert PASS。

### Step D：scaffold_v2 mirror 同步

- 同 commit 同步 `.workflow/context/checklists/review-checklist.md`（修改） + `.workflow/context/roles/reviewer.md`（如修改）到 scaffold_v2 mirror。

### Step E：roadmap 内容骨架定调（落本 plan.md §5）

- 在本 plan.md §5 留痕 roadmap 骨架（done 阶段六层回顾时 cp 出 `.workflow/flow/requirements/req-48-{slug}/done/roadmap.md`）：
  - 留尾 3 fix-checklist：`fix-user-write-protected-zones.md`（高优先级）/ `fix-build-cache-freshness.md`（中）/ `fix-self-audit-drift.md`（中）；
  - 留尾 5 contract 改造：`role-stage-continuity`（中）/ `test-case-design-completeness`（中）/ `triggers`（低）/ `testing-no-destructive-git`（中）/ `deployment-sync`（低）；
  - 建议路径：req-49（user-write-protected-zones + build-cache-freshness + self-audit-drift 三个 fix-checklist + 各自 lint 改造） / 5 sug 入池（每条 contract 改造一条 sug，挂到对应 fix-checklist 项下）；
  - 不在本 chg 创建 sug 文件本体（done 阶段执行）。

## 2. 验证

### 2.1 unit

- `pytest tests/test_block_protocol_e2e.py -v` 全 PASS（3 用例）；
- `pytest tests/` 全量不回归。

### 2.2 manual

- `grep "抛错协议配套" .workflow/context/checklists/review-checklist.md` 命中；
- `harness validate --contract artifact-placement` exit 0；
- `harness validate --human-docs` exit 0；
- 子进程跑 dogfood 用例 1 完整流程 PASS（FAIL → fix → PASS）。

### 2.3 AC mapping

| Step | 对应 AC |
|------|---------|
| A | AC-06（review-checklist.md 加项）|
| B | AC-06（reviewer.md 强调）|
| C | AC-06（端到端 dogfood pytest 自证）|
| D | AC-07（scaffold_v2 mirror 同步）|
| E | AC-08（分批落地与续尾 roadmap）|

## 3. 硬序约束

- chg-03 必须晚于 chg-01 + chg-02：dogfood pytest 要构造 lint FAIL → 触发 raise_harness_block → 派发 fix-subagent → 端到端验证，所有依赖：
  - chg-01：error-protocol.md 协议契约 + raise_harness_block helper + base-role 硬门禁八 + harness-manager Step 3.7；
  - chg-02：3 个 fix-checklist 文件 + 3 个 contract 改造 + verbose flag；
- 本 chg 内 A → B → C → D → E 严格硬序（reviewer 文档稳定后才能 grep 抽样；dogfood pytest 跑绿后再定调 roadmap，避免 roadmap 内容受 dogfood 暴露的新问题影响）。

## 4. 测试用例设计

> regression_scope: targeted
> 波及接口清单（git diff --name-only 预估 + 人工分析）：
> - `.workflow/context/checklists/review-checklist.md`（修改：新增 2 条条目）
> - `.workflow/context/roles/reviewer.md`（修改：SOP 强调 + 本 checklist 引用，按现状增量）
> - `tests/test_block_protocol_e2e.py`（新建）
> - `src/harness_workflow/assets/scaffold_v2/.workflow/context/checklists/review-checklist.md`（mirror）
> - `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/reviewer.md`（mirror，如修改）
> - 间接波及：`src/harness_workflow/validate_contract.py`（dogfood 调用，不改）+ `src/harness_workflow/workflow_helpers.py::raise_harness_block`（dogfood 调用，不改）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01-review-checklist 加项存在 | `grep "抛错协议配套" .workflow/context/checklists/review-checklist.md` | 命中 ≥ 2 次（六层框架 + 阶段速查表）；引用 `req-48 / chg-03` | AC-06 | P0 |
| TC-02-reviewer-md 引用 | `grep -i "review-checklist" .workflow/context/roles/reviewer.md`（如 reviewer.md 存在）| 命中 ≥ 1 次；如 reviewer.md 不存在则跳过此 TC（标 N/A 在 session-memory）| AC-06 | P1 |
| TC-Dogfood-03-artifact-placement-闭环 | tmpdir fixture 安装最小 .workflow/ 骨架；构造 `artifacts/main/requirements/req-99-x/planning/session-memory.md` 违规工件；子进程 1 跑 `harness validate --contract artifact-placement`；按 fix-artifact-placement.md 步骤模拟 mv（mv 到 .workflow/flow/requirements/req-99-x/planning/）；子进程 2 复跑 contract | 子进程 1 exit=64 + stdout 含 `HARNESS_BLOCK: artifact-placement` + `fix-checklist: .workflow/context/checklists/fix-artifact-placement.md`；`{tmp}/.workflow/state/runtime-block.yaml` 字段完整（error_type / severity=FAIL / recovery_attempts=1）；子进程 2 exit=0 + stdout 含 `PASS` | AC-06 / AC-05 | P0 |
| TC-Dogfood-04-schema-audit-闭环 | tmpdir 构造 `.workflow/state/requirements/req-99/foo.yaml`；子进程 1 跑 `harness validate --contract schema-audit`；按 fix-schema-audit.md 步骤模拟 mv 到 archive 或迁 yaml；子进程 2 复跑 | 子进程 1 exit=64 + stdout `HARNESS_BLOCK: schema-audit` + `fix-checklist: ...fix-schema-audit.md`；子进程 2 exit=0 + PASS | AC-06 / AC-05 | P0 |
| TC-Dogfood-05-missing-document-闭环 | tmpdir 构造 runtime.yaml `stage=planning, current_requirement=req-99` + `flow/requirements/req-99-x/changes/` 空目录；子进程 1 跑 `harness validate --contract missing-document`；按 fix-missing-document.md 步骤模拟创建 chg 子目录 + change.md + plan.md 骨架；子进程 2 复跑 | 子进程 1 exit=64 + stdout `HARNESS_BLOCK: missing-document` + `fix-checklist: ...fix-missing-document.md`；retry_context 含 `missing` 字段；子进程 2 exit=0 + PASS | AC-06 / AC-05 | P0 |
| TC-06-runtime-block-累计-attempts | tmpdir 内 TC-Dogfood-03 跑两次（不 fix）| 第二次 `runtime-block.yaml` recovery_attempts=2 | AC-01 / AC-06（验证累计语义）| P1 |
| TC-07-mirror-review-checklist 同步 | `diff .workflow/context/checklists/review-checklist.md src/harness_workflow/assets/scaffold_v2/.workflow/context/checklists/review-checklist.md` | 输出为空 | AC-07 | P0 |
| TC-08-roadmap 骨架留痕 | grep `留尾` 本 plan.md §5 | 命中 ≥ 1 次；含 3 fix-checklist + 5 contract 字面 | AC-08 | P0 |

> dogfood TC 必填字段（TC-Dogfood-03/04/05 共享填法）：
> - tmpdir fixture：`tmp_path` 或现有 `tmp_harness_repo` fixture
> - 子进程命令：`subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'validate', '--contract', '<name>'], cwd=tmp_path, capture_output=True, text=True)`
> - stdout 断言：含 `HARNESS_BLOCK: <name>` + `fix-checklist: .workflow/context/checklists/fix-<name>.md`
> - runtime stage 断言：替代为 `runtime-block.yaml` 字段断言（`error_type=<name>` / `severity=FAIL` / `recovery_attempts=1`）
> - feedback.jsonl 事件数：本 chg 的 dogfood 不直接接通 feedback hook（lint 失败不写 feedback），但闭环修复时如经过 `harness next` 路径会触发 feedback；本 chg 闭环走 `harness validate --contract`，不强制 feedback，标 N/A 但 plan 显式声明
> - 对应 AC：AC-06 / AC-05
> - 优先级：P0

## 5. roadmap 骨架（chg-03 定调，done 阶段 cp 到 roadmap.md）

### 5.1 留尾 fix-checklist（3 个）

| 名称 | 优先级 | 触发条件（来自 PetMall / uav 实证）| 建议归属 |
|------|--------|--------------------------------|----------|
| `fix-user-write-protected-zones.md` | 高 | `check_user_write_protected_zones` ABORT — 用户写到 artifacts/ 下保护区 | req-49（首批）|
| `fix-build-cache-freshness.md` | 中 | `check_build_cache_freshness` WARN — `build/` 缓存过期或污染 | req-49（首批）|
| `fix-self-audit-drift.md` | 中 | `check_role_stage_continuity` 类自审漂移（角色表 / map.yaml / md 三镜像不一致）| req-49（首批）|

### 5.2 留尾 contract 改造（5 个，配 fix-checklist 时同时改造）

| contract 名 | 优先级 | 当前状态 | 建议归属 |
|------------|--------|----------|----------|
| `role-stage-continuity` | 中 | 已存在但 FAIL 仅打 hint | req-49（与 fix-self-audit-drift 配套）|
| `test-case-design-completeness` | 中 | 已存在但 FAIL 仅 print | sug-pool（独立小 chg）|
| `triggers` | 低 | 已存在 | sug-pool |
| `testing-no-destructive-git` | 中 | 已存在 | sug-pool |
| `deployment-sync` | 低 | 已存在 | sug-pool |

### 5.3 落地节奏

- **req-49**：3 fix-checklist + 2 配套 contract 改造（user-write-protected-zones / build-cache-freshness / role-stage-continuity）；
- **sug-pool**：3 sug（test-case-design-completeness / triggers / testing-no-destructive-git / deployment-sync 各一条），按低 / 中优先级排队，碎片化时间渐进落；
- **节奏选择理由**：req-46 / req-47 同款"首批 K + 留尾"模式已用户验证可用，避免单 req 超载、reviewer 压力大；按优先级渐进落，5 sug 在后续 req 完成时顺手 cherry-pick 即可。
