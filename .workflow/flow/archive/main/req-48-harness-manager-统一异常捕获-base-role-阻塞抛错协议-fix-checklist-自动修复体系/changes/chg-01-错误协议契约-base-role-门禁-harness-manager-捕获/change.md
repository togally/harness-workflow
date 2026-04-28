# Change — chg-01（错误协议契约 + base-role 抛错门禁 + harness-manager 捕获路由）

> 父需求：req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）
> 角色：analyst（opus），由 executing（sonnet）按 plan.md 落地
> 依赖：无前置 chg；本 chg 是契约底座

## 1. 目标

落地 HARNESS_BLOCK 错误协议契约（三层载体：stderr 文本 + 退出码 ≥ 64 + 状态文件 `.workflow/state/runtime-block.yaml`），并在 base-role.md / harness-manager.md 两份角色文件中分别加新硬门禁与新职责，使任意 stage 角色检测到 blocker 时能按统一协议抛错、由 harness-manager 统一捕获并路由。

本 chg **只动协议规约 + 角色文档 + 1 个 helper**，不写 fix-checklist 内容，不改 lint 输出。

## 2. 范围

### 2.1 包含

1. **新建 `.workflow/context/error-protocol.md`**：
   - HARNESS_BLOCK 三层载体 schema（stderr 文本格式 / exit code ≥ 64 字面表 / `runtime-block.yaml` 字段）；
   - error_type 命名规范（kebab-case，与 contract 名同字面：`artifact-placement` / `schema-audit` / `missing-document` / `user-write-protected-zones` / `build-cache-freshness` / `self-audit-drift` / 后续可扩）；
   - fix-checklist 命名规范（`.workflow/context/checklists/fix-{error-type}.md`）；
   - recovery_attempts 上限语义（同 type 连续 ≥ 3 次失败 → 升级用户）；
   - 错误结构字段：`error_type` / `fix_checklist_path` / `retry_context` / `severity`（ABORT/FAIL/WARN）/ `detected_by`（角色）/ `timestamp` / `recovery_attempts`。

2. **修改 `.workflow/context/roles/base-role.md`**：
   - 新增「**硬门禁八：任务阻塞错误抛出协议**」段落（与现有硬门禁一~七并列生效）；
   - 强制流程：检测 blocker → 1. update session-memory 「待处理捕获问题」+「default-pick 决策」段 → 2. update `runtime-block.yaml` → 3. 调 `raise_harness_block(...)` helper 抛错；
   - 与现有「通用准则·职责外问题记 session-memory」互补：blocker 是即时阻塞，记完即抛；职责外问题是非阻塞延后。

3. **修改 `.workflow/context/roles/harness-manager.md`**：
   - 新增 `### Step 3.7: 阻塞错误捕获与修复路由` 节（按现有 §3.6 派发协议复用）；
   - 流程：解析 error_type → 校验 fix_checklist 存在 → 派发 fix-subagent（按 default-pick HM-2=A）→ 修复完成后 update runtime-block + 重试原任务；
   - 升级条件：fix_checklist 不存在 / 同 type recovery_attempts ≥ 3 / 修复 subagent ABORT → 退化为 hint + 升级用户。

4. **新建 `src/harness_workflow/workflow_helpers.py::raise_harness_block(...)` helper**：
   - 函数签名：`raise_harness_block(error_type: str, fix_checklist_path: str, retry_context: dict, severity: str = "FAIL", detected_by: str = "", root: Path | None = None) -> NoReturn`；
   - 行为：写 `runtime-block.yaml` → 打印 stderr `HARNESS_BLOCK: {error_type}\nfix-checklist: {path}\n...` → `sys.exit(64 + severity_offset)`（FAIL=64 / ABORT=65 / WARN 不抛错只 print）；
   - 单测覆盖：3 case（FAIL / ABORT / WARN）+ runtime-block.yaml 字段断言。

5. **scaffold_v2 mirror 同步**（硬门禁五）：
   - 同 commit 内同步 `.workflow/context/error-protocol.md` / `roles/base-role.md` / `roles/harness-manager.md` 到 `src/harness_workflow/assets/scaffold_v2/.workflow/` 镜像。

6. **runtime-block.yaml schema 文档化**：
   - 字段定义在 `error-protocol.md` 节中给样例（不新建独立 schema 文件）；
   - 实际文件由 helper 在 `runtime` 目录下 lazy 创建，初始为空。

### 2.2 排除

- 不写任何 fix-checklist 文件内容（chg-02 范畴）；
- 不改任何现有 contract lint 输出（chg-02 范畴）；
- 不写 reviewer checklist 加项（chg-03 范畴）；
- 不做端到端 dogfood pytest（chg-03 范畴）。

## 3. 验收

- [ ] `.workflow/context/error-protocol.md` 存在、字段完整（包含 §6 核心字段 + §3 命名规范 + §recovery_attempts 上限）；
- [ ] `.workflow/context/roles/base-role.md` 含「硬门禁八」段落；
- [ ] `.workflow/context/roles/harness-manager.md` 含 `### Step 3.7` 节；
- [ ] `src/harness_workflow/workflow_helpers.py::raise_harness_block` 函数存在、可被 import；
- [ ] 3 文件同步到 scaffold_v2 mirror；
- [ ] 单测 ≥ 3 条 PASS；
- [ ] `harness validate --contract artifact-placement` exit 0；
- [ ] `harness validate --human-docs` exit 0。

对应 AC：AC-01 / AC-02 / AC-03 + AC-07（mirror 同步部分）。

## 4. 关联 sug

- 无（本 chg 是 req-48 新设计，不溯源到既有 sug）。
