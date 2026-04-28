# Requirement

## 1. Title

harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系

## 2. Goal

把现有"contract lint 命中 → 仅打 hint / 列违规清单 → 用户手动修复"的半截链路，闭环成"stage 角色 → 标准化抛错 → harness-manager 捕获 → 按 fix-checklist 自动修复 → 重试原任务"。

**核心痛点**（PetMall / uav 实证，req-46 系列暴露）：

- `schema-audit` 命中旧目录 → 只 hint，用户手工迁移；
- `artifact-placement lint FAIL` → 列 150 个违规文件名让用户 mv；
- `user-write-protected-zones ABORT` → 仅 hint "放 artifacts/ 下"；
- `build-cache-freshness WARN` → 仅 hint "rm -rf build/"；
- `requirement.md` / `change.md` / `plan.md` / `session-memory.md` / flow workspace 缺失 → 角色 ABORT 但无统一恢复路径。

设计抽象：所有"提示无工具"反模式收敛到统一异常处理范式：

```
[stage 角色] 检测 blocker
   → 1. session-memory + runtime state 留痕
   → 2. 抛 HARNESS_BLOCK <error-type>（含 fix-checklist 指针）

[harness-manager] 捕获错误
   → 3. 解析 error-type
   → 4. 读 .workflow/context/checklists/fix-{type}.md
   → 5. 派发修复 subagent（或主 agent 自执行）按 checklist 跑
   → 6. 修复完成 → 重试原任务；反复失败 → 升级用户决策
```

## 3. Scope

### 3.1 包含（六大落地点）

1. **base-role.md 新硬门禁**：「任务阻塞错误抛出协议」——检测 blocker → 更新 session-memory + runtime state → 标准化错误抛出（含 error-type / fix-checklist 指针 / 重试上下文）。
2. **harness-manager.md 新职责**：「阻塞错误捕获与修复路由」——解析 error-type → 读对应 fix-checklist → 派发修复 subagent / 主 agent 自执行 / 升级用户。
3. **错误标准化格式契约**：新增 `.workflow/context/error-protocol.md`，定义 `HARNESS_BLOCK: <type>` 协议（载体形式见 §4 验收标准）。
4. **Fix Checklists 套件**（首批 3 个 + 留尾 3 个）：
   - 首批（chg-02 落地）：`fix-artifact-placement.md` / `fix-schema-audit.md` / `fix-missing-document.md`
   - 留尾（独立 chg / 后续 req）：`fix-user-write-protected-zones.md` / `fix-build-cache-freshness.md` / `fix-self-audit-drift.md`
5. **Lint 输出改造**：现有所有 contract（artifact-placement / user-write-protected-zones / build-cache-freshness / schema-audit / role-stage-continuity / test-case-design-completeness 等）的 FAIL/WARN/ABORT 输出统一加 `fix-checklist:` 指针字段；首批仅改造已写 fix-checklist 的 3 个 contract，其余按"无 checklist 时降级为现有 hint"兼容。
6. **Reviewer checklist 加项 + 自检**：新加 contract 必须配套 fix-checklist（防止再出现"提示无工具"反模式）；reviewer 阶段 grep 校验。

### 3.2 排除

- **不**在本 req 内重构现有 contract lint 检测逻辑（仅加输出字段 + 接入捕获）；
- **不**做跨 repo 远程修复 / 网络下载行为；
- **不**强制改造非 lint 类的 ABORT（如 git 操作失败、单测失败）；这些走 regression 路径，不在本 req 范围；
- **不**对 PetMall / uav / Yh-platform 等 user repo 历史脏数据做反向回填（仅在 user repo 下次 install / next 时由新机制接管）。

## 4. Acceptance Criteria

### AC-01：error-protocol.md 协议契约落地

- `.workflow/context/error-protocol.md` 文件存在，定义：
  - `HARNESS_BLOCK: <type>` 错误的载体形式（**default-pick C-1 = 三层混合**：stderr 文本协议 + 退出码 ≥ 64 + 状态文件 `.workflow/state/runtime-block.yaml` 落点；详见 §4 default-pick 决策）；
  - 错误结构字段：`error_type` / `fix_checklist_path` / `retry_context` / `severity`（ABORT/FAIL/WARN）/ `detected_by`（角色）/ `timestamp`；
  - 已知 error-type 字面表（artifact-placement / schema-audit / user-write-protected-zones / build-cache-freshness / missing-document / self-audit-drift / 后续可扩）；
  - harness-manager 捕获语义 + 重试边界（连续 3 次同 type 失败 → 升级用户）。

### AC-02：base-role.md 新硬门禁

- 新增「**硬门禁八：任务阻塞错误抛出协议**」段落；
- 强制规则：stage 角色检测 blocker → 必须先 update session-memory 与 runtime-block 状态文件 → 再抛 HARNESS_BLOCK；
- 与既有硬门禁一~七并列生效，不替代；
- 与 base-role 通用准则"职责外问题记 session-memory"互补：blocker 是即时阻塞，记完即抛错；职责外问题是非阻塞延后。

### AC-03：harness-manager.md 新职责

- 新增 `### Step 3.7: 阻塞错误捕获与修复路由`（或同语义节）；
- 强制流程：解析 error_type → 校验 fix_checklist 存在 → 按"权限矩阵 default-pick HM-2 = A 自动修复（修复 subagent / 主 agent 自执行均可）"路由 → 修复完成后 update runtime-block → 重试原任务；
- 升级条件：fix_checklist 不存在 / 同 type 重试 ≥ 3 次 / 修复 subagent ABORT → 改打"修复指引 + 升级用户"模式；
- 派发修复 subagent 时按现有 §3.6 派发协议（briefing + context_chain + model + record_subagent_usage）。

### AC-04：fix-checklist 套件首批

- `.workflow/context/checklists/fix-{artifact-placement,schema-audit,missing-document}.md` 三个文件存在；
- 每个 checklist 包含：
  - **触发条件**：哪个 contract / 错误形态触发；
  - **修复步骤**：可执行命令 / 文件操作清单（如 `git mv` / `mkdir -p` / 模板复制）；
  - **验证步骤**：修复后跑哪个 `harness validate --contract <name>` 验绿；
  - **回退路径**：修复失败时如何 ABORT 给用户（含 session-memory 留痕模板）；
  - **dogfood 样本**：至少给 1 条 PetMall / uav 实例化路径示例。

### AC-05：lint 输出改造（首批 3 个 contract）

- `validate_contract.py` 中 `check_artifact_placement` / `_audit_legacy_schema_folder` / `check_missing_document`（若新增）的 FAIL/ABORT 输出新增一行：
  ```
  fix-checklist: .workflow/context/checklists/fix-{type}.md
  ```
- 输出形态保持与现有 hint 兼容（hint 字段保留作为人工 fallback）；
- 现有不属首批 3 个的 contract 不强制改造，留尾 chg 按需补。

### AC-06：reviewer checklist 加项 + 端到端自证

- `.workflow/context/checklists/review-checklist.md` 增一条：「新加 contract 必须配套 `fix-{type}.md` 否则 FAIL」；
- 端到端自证：构造一个故意违反 artifact-placement 的工件 → 跑 `harness next` → 观察 harness-manager 捕获 → 按 fix-checklist 自动迁移 → lint 转绿 → 任务继续；
- pytest 增 ≥ 1 条 dogfood 用例覆盖该端到端路径（按 dogfood TC 必填字段执行）。

### AC-07：scaffold_v2 mirror 同步

- 全部新增 / 修改的 `.workflow/context/error-protocol.md` / `roles/base-role.md` / `roles/harness-manager.md` / `checklists/*.md` 同步到 `src/harness_workflow/assets/scaffold_v2/.workflow/` 下镜像；
- 同 commit 完成（hardness-manager 硬门禁五保护面）；
- `harness install` 在新装项目中能直接生效。

### AC-08：分批落地与续尾

- 首批 chg（≤ 3）覆盖 §3.1 的 1 + 2 + 3 + 4（仅首批 3 个 fix-checklist）+ 5（仅 3 个 contract 改造）+ 6（reviewer 加项 + 端到端 dogfood）；
- 留尾（3 个 fix-checklist + 其余 contract 改造）拆为后续 req 或 sug 池，本 req 的 done 阶段输出 roadmap.md 留痕（按 req-46 同款"首批 K + 留尾"模式）。

## 5. Split Rules

### 5.1 chg 拆分粒度（**default-pick S-1 = A，3 chg**）

| chg-id | 标题（≤ 15 字简短描述） | 范围 | 验收 |
|--------|----------------------|------|------|
| chg-01 | 错误协议契约 + base-role + harness-manager | 落地 §3.1 第 1 + 2 + 3 项；只规约 / 协议层不动 lint | AC-01 / AC-02 / AC-03 + AC-07 mirror 同步 |
| chg-02 | Fix Checklist 套件首批（3 个）+ lint 输出加指针 | 落地 §3.1 第 4（首批 3 个）+ 第 5（首批 3 个 contract 改造） | AC-04 / AC-05 + AC-07 mirror 同步 |
| chg-03 | reviewer 加项 + 端到端 dogfood + roadmap | 落地 §3.1 第 6 + AC-08 留尾 roadmap 输出 | AC-06 / AC-08 + AC-07 mirror 同步 |

### 5.2 拆分原则

- **chg-01 是契约底座**：只动 `.md` 协议规约 + `roles/` 文档 + `error-protocol.md`，不写 Python 代码；reviewer 易审。
- **chg-02 是工程主菜**：fix-checklist 文件 + `validate_contract.py` lint 输出改造 + 必要的 helper（如 `format_fail_with_fix_checklist`）；先把 `artifact-placement` / `schema-audit` / `missing-document` 三个最高频痛点端到端跑通。
- **chg-03 是反馈闭环**：reviewer 加项防再犯 + 1 条 dogfood pytest 验证整链路，并产出 roadmap.md 留尾给后续 req（其余 3 个 fix-checklist + 其余 contract 改造）。
- 三个 chg 之间存在依赖：chg-02 依赖 chg-01 的协议契约，chg-03 依赖 chg-02 的 fix-checklist 实例。
- 每个 chg 完成形成独立可发版交付：chg-01 落地后即使 chg-02/03 未做，base-role 已具备阻塞抛错能力（仅 harness-manager 端按 default 走"无 fix-checklist 降级为 hint"路径）。

### 5.3 dogfood TC 必填

- chg-02 + chg-03 均涉及 CLI 入口（`harness next` / `harness validate --contract`），plan.md §4 必须含 ≥ 1 条 dogfood TC（tmpdir / 子进程 / stdout 断言 / runtime stage 断言 / `feedback.jsonl` 事件数）。

### 5.4 留尾建议（roadmap.md 输出，本 req done 阶段）

- 留尾 3 个 fix-checklist：`fix-user-write-protected-zones.md` / `fix-build-cache-freshness.md` / `fix-self-audit-drift.md`；
- 留尾 contract 改造：`role-stage-continuity` / `test-case-design-completeness` / `triggers` / `testing-no-destructive-git` / `deployment-sync` 共 5 个；
- 建议作为 req-49 / req-50 单独落，或拆 sug 池按优先级渐进。

---

> **路径自检（chg-01 of req-46 落地）**：本 requirement.md 落 `.workflow/flow/requirements/req-48-{slug}/requirement.md`（机器型工件回 flow/requirements，禁落 `artifacts/main/requirements/{req-48-slug}/`）。
>
> **harness validate** 退出条件：
> - `harness validate --contract artifact-placement` exit 0；
> - `harness validate --human-docs` exit 0（按 D-11=B 留痕放行模式）。
