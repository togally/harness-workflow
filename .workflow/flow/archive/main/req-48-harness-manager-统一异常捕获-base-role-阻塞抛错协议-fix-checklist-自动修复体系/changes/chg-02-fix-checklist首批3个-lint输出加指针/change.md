# Change — chg-02（Fix Checklist 首批 3 个 + lint 输出加 fix-checklist 指针）

> 父需求：req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）
> 角色：analyst（opus），由 executing（sonnet）按 plan.md 落地
> 依赖：chg-01（错误协议契约 + base-role 抛错门禁 + harness-manager 捕获路由）必须先完成（要 import `raise_harness_block` + 引用 error_type 字面表）

## 1. 目标

把 chg-01 的协议底座变成可消费的工程主菜：
1. 写 3 个 fix-checklist（artifact-placement / schema-audit / missing-document）；
2. 改造 3 个 contract lint 函数（`check_artifact_placement` / `check_schema_audit` 新建 / `check_missing_document` 新建）的 FAIL/ABORT 输出，调 `raise_harness_block` 标准化抛错并加 `fix-checklist:` 指针；
3. 加 `verbose` flag 控制详细输出，避免 `harness next` 内部 gate 静默 PASS 时仍打长串；
4. 单测覆盖 3 个 contract 改造 + 3 个 fix-checklist 文件存在。

## 2. 范围

### 2.1 包含

#### 2.1.1 fix-checklist 写作（落 `.workflow/context/checklists/`）

1. **`fix-artifact-placement.md`**：
   - §触发条件：`check_artifact_placement` FAIL（artifacts/ 下机器型文件 / stage-name 子目录残留）；
   - §修复步骤：(a) grep 违规清单 → (b) for each 违规：用 `_resolve_target_path` 计算应落点（`.workflow/flow/requirements/{req-id}-{slug}/...`）→ (c) `mkdir -p target_parent && mv source target` → (d) cleanup empty stage-name 子目录 → (e) re-lint verify；
   - §验证步骤：`harness validate --contract artifact-placement` exit 0；
   - §回退路径：mv 冲突时（target 已存在）→ 写 session-memory 「待处理捕获问题」+ ABORT 给用户；
   - §dogfood 样本：本会话中 PetMall 150 文件迁移成功路径（路径模式 + 1 条具体 mv 命令样例）。

2. **`fix-schema-audit.md`**：
   - §触发条件：检测到 `.workflow/state/requirements/req-XX/` 旧目录形态（schema-audit lint 命中）；
   - §修复步骤：(a) 列出 `req-XX/` 旧目录清单 → (b) for each：检查同名 yaml 是否已存在或已归档 → (c) 三分支：`harness migrate requirements`（CLI 已支持）/ `mv` 到 `archive/` / 新建 yaml + 移动内容 → (d) re-lint verify；
   - §验证步骤：`harness validate --contract schema-audit` exit 0；
   - §回退路径：找不到对应 req title 时 → 用目录名作 fallback title + ABORT 给用户人工修订；
   - §dogfood 样本：req-46 / chg-01 已验证的迁移路径示例。

3. **`fix-missing-document.md`**：
   - §触发条件：当前 stage 必需产物缺失（如 planning 阶段缺 change.md / plan.md / session-memory.md / chg 子目录）；
   - §修复步骤：(a) 读 runtime.yaml 拿 stage → (b) 按 stage 决定缺什么：
     - `requirement_review` 缺 `requirement.md` → 创建骨架 + 5 节模板；
     - `planning` 缺 `change.md` / `plan.md` → 按 chg-id 创建子目录 + 模板；
     - 任意 stage 缺 `session-memory.md` → 创建空骨架（10 节模板）；
   - (c) 验证 `harness status` 正常；
   - §验证步骤：`harness validate --contract missing-document` exit 0 + `harness status` 不报缺失；
   - §回退路径：如缺失文件需要业务输入（如 requirement.md 的「目标」字段）→ 仅创建骨架并标记 `<TODO: by analyst>` 占位，retry 后由 analyst 补全；
   - §dogfood 样本：req-48 自身首次 planning 时 chg 子目录缺失场景（如本 req 三个 chg 目录创建步骤）。

#### 2.1.2 lint 输出改造（修改 `src/harness_workflow/validate_contract.py`）

1. **`check_artifact_placement` 改造**：
   - FAIL 分支末尾调 `raise_harness_block("artifact-placement", ".workflow/context/checklists/fix-artifact-placement.md", retry_context={"violations": violations, "root": str(root)}, severity="FAIL", detected_by="check_artifact_placement", root=root)`；
   - 同时保留现有 hint 字段为人工 fallback；加 `fix-checklist: .workflow/context/checklists/fix-artifact-placement.md` 一行；
   - 不改 PASS 分支输出。

2. **`check_schema_audit`（新建）**：
   - 扫 `.workflow/state/requirements/req-XX/`（数字目录形态）+ `.workflow/state/bugfixes/bugfix-XX/`（如有同形态）→ 命中即 violations.append；
   - FAIL 时调 `raise_harness_block("schema-audit", "fix-schema-audit.md", ...)` + 输出 `fix-checklist:` 指针；
   - 加入 `_DISPATCH_TABLE`（contract 名 → 函数 map）；
   - 加 `--contract schema-audit` CLI 路径。

3. **`check_missing_document`（新建）**：
   - 读 runtime.yaml 拿 current_requirement / stage / chg-id → 按 stage 列必需文件清单 → 检测缺失；
   - FAIL 时调 `raise_harness_block("missing-document", "fix-missing-document.md", retry_context={"missing": missing, "stage": stage, "req_id": req_id})`；
   - 加 `--contract missing-document` CLI 路径。

#### 2.1.3 verbose flag 控制

- 在 3 个 contract 函数加 `verbose: bool = True` 参数；
- `harness next` 内部 gate 调用时传 `verbose=False`：PASS 时不打印（避免 stdout 噪声）；只 FAIL 时打印 + 抛 HARNESS_BLOCK；
- CLI 直调（`harness validate --contract X`）默认 `verbose=True`；
- 改造 `_DISPATCH_TABLE` / `validate_contract.py::main` 的入口函数签名。

#### 2.1.4 scaffold_v2 mirror 同步

- 同 commit 同步 `.workflow/context/checklists/fix-{artifact-placement,schema-audit,missing-document}.md` 三文件到 scaffold_v2 mirror（注：checklists 目录在硬门禁五例外白名单，但本 req 是新增 contract 配套 fix-checklist，应纳入 mirror 以确保 `harness install` 新装项目可用）。

### 2.2 排除

- 不动其余 5 个 contract（user-write-protected-zones / build-cache-freshness / role-stage-continuity / test-case-design-completeness / triggers）—— 留尾 chg-03 的 roadmap 输出；
- 不写 reviewer checklist 加项（chg-03 范畴）；
- 不做端到端 dogfood pytest（chg-03 范畴，本 chg 仅做 contract 函数级单测）。

## 3. 验收

- [ ] `.workflow/context/checklists/fix-{artifact-placement,schema-audit,missing-document}.md` 三文件存在 + 5 节齐全（触发条件 / 修复步骤 / 验证步骤 / 回退路径 / dogfood 样本）；
- [ ] `check_artifact_placement` FAIL 输出含 `HARNESS_BLOCK: artifact-placement` + `fix-checklist:` 行 + 调用 `raise_harness_block`；
- [ ] `check_schema_audit` 函数存在 + CLI 路径 `harness validate --contract schema-audit` 可执行；
- [ ] `check_missing_document` 函数存在 + CLI 路径 `harness validate --contract missing-document` 可执行；
- [ ] verbose=False 时 PASS 不打印（断言 stdout 空）；verbose=True 时 PASS 打印 `PASS: ...`；
- [ ] 单测 ≥ 9 条 PASS（详见 plan §4）；
- [ ] 3 fix-checklist 同步到 scaffold_v2 mirror；
- [ ] `harness validate --contract artifact-placement` exit 0；
- [ ] `harness validate --human-docs` exit 0。

对应 AC：AC-04（fix-checklist 套件首批）/ AC-05（lint 输出改造首批 3 个）+ AC-07（mirror 同步部分）。

## 4. 关联 sug

- 无（本 chg 是 req-48 工程主菜，新设计）；
- 但 fix-artifact-placement.md 的 dogfood 样本会引用 req-46 / chg-01（机器型工件路径修复 + 防再犯 lint）的成功迁移路径。
