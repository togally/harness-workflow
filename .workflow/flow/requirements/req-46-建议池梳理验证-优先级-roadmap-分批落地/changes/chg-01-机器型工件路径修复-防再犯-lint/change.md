# Change

## 1. Title

机器型工件路径修复 + 防再犯 lint

## 2. Background

reg-01（analyst 机器型工件误落 artifacts/ 违反 req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C）） 关注点分离契约（req-46（建议池梳理验证 + 优先级 roadmap + 分批落地） 现场））confirmed → 路由 planning，4 维根因摘要：

- **直接原因**：req-46 现场 analyst 在 requirement_review / planning 两 stage 把 `session-memory.md` / `sug-audit.md` / `roadmap.md` 4 件机器型工件误落 `artifacts/main/requirements/req-46-.../{requirement-review,planning}/` 子目录，违反 repository-layout.md §1（artifacts/ 仅装对人产物）+ §2 白名单（4 件均不在白名单）+ §3（机器型权威落位 .workflow/flow/）。
- **机制原因（5 层缺保护）**：
  1. briefing 模板未注入 `expected_artifact_paths`，派发 analyst 时无显式落点指引；
  2. analyst.md / stage-role.md 契约 2/3/4 把路径细节"全下放"给 repository-layout.md，无"产出前对照 §3 路径表"操作层硬门禁；
  3. `artifact-placement` lint（bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） A3 已实现）只在 reviewer / done 兜底，未纳入 analyst 等 stage 退出门禁；
  4. lint 命中规则 `_MACHINE_TYPE_FILENAMES` 仅 17 项固定文件名，**漏命中** `sug-audit.md` / `roadmap.md` 等工作产出类，**误命中** §2 白名单内 raw `requirement.md` 副本；
  5. reviewer checklist 缺 artifact-placement 反向抽样条目（sug-35 已记录 pending 未落地）。
- **历史回溯**：req-41 立契约 → req-42 ~ req-45 全部正确落位（4 例正例）→ req-46 是反例首例，触发条件是"复杂度突破契约边界"（req-46 是首个在两 stage 都产出复杂中间工件的 req）；契约本身没坏，缺当复杂度上升时的强制对照硬门禁。
- **关联 sug**：sug-35（reviewer checklist 扩 artifact-placement / test-case-design-completeness 三类 lint 条目补全）直接相关，本 chg 必须含其落地翻转；sug-33（briefing-lint-testing-over-instructing）相邻问题，借势纳入 briefing 路径注入条款思考。

## 3. Requirement

- req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）

## 4. Scope

### Included

- **物理回归**：4 个机器型工件 `git mv` 从 `artifacts/main/requirements/req-46-.../` 回 `.workflow/flow/requirements/req-46-.../`，并 `rmdir` 清理空 stage 子目录。
- **briefing 模板硬门禁**：`harness-manager.md` §3.6 派发协议加 `expected_artifact_paths` 字段约定，派发任意 stage 角色时 briefing 必须显式列该 stage 工件期望落点路径。
- **角色文件硬门禁**：`analyst.md` 加"产出 stage 工件前对照 repository-layout.md §3 路径表"硬门禁；`stage-role.md` 契约 2/3 加 SOP 检查点（"路径自检"操作层步骤），契约文字从概念层落到操作层。
- **lint 升级**：`src/harness_workflow/validate_contract.py::check_artifact_placement` 升级——
  1. 新增"路径模式扫"：`artifacts/main/requirements/{req-id}-{slug}/` 下任何 stage-name 子目录（`requirement-review` / `planning` / `executing` / `testing` / `acceptance` / `done` / `regression`）→ FAIL；
  2. 新增白名单豁免：`artifacts/.../requirement.md` 是 §2 白名单合法项，修复误命中；
  3. 扩展 `_MACHINE_TYPE_FILENAMES` 含 `sug-audit.md` / `roadmap.md` 等工作产出类（或改为黑名单文件名外的"非白名单一律 FAIL"模式）。
- **stage 退出门禁接入**：`analyst.md` 退出条件加 `harness validate --contract artifact-placement` 必跑；`harness next` CLI 退出 gate 在 analyst 流转（req_review → planning / planning → ready_for_execution）触发该 lint。
- **reviewer checklist 扩展**：`review-checklist.md` 制品完整性章节加反向检查项 `artifact-placement 反向抽样（高）`，呼应 sug-35。
- **scaffold_v2 mirror 同步**：上述 `roles/` + `checklists/` 改动同步 `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/` + `.../checklists/`；同一 commit 内同步（硬门禁五）。
- **sug-35 状态翻转**：`sug-35` 状态由 `pending` → `archived`，frontmatter 加 `applied_at` / `applied_by_chg: chg-01`。

### Excluded

- req-42（archive 重定义：对人不挪 + 摘要废止） ~ req-45（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） 的 `artifacts/` / `.workflow/flow/archive/` 历史脏数据：spot-check 已确认无残留违规（4 例正确落位），不在本 chg 修复面。
- req-46 其他 sug 落地（chg-02 ~ chg-NN 按 roadmap.md 首批之 1/2/3 推进）：本 chg 是它们的前置项，本身不承载它们的工作。
- 跨 repo（如 Yh-platform）的 lint 推广：本 chg 仅修主仓 harness-workflow，跨 repo 同步由后续 sug / req 承担。
- legacy req-02 ~ req-40 的 `artifacts/` 历史结构：repository-layout.md §4 已豁免，禁止本 chg 触碰。

## 5. Acceptance

- **AC-1（物理回归）**：4 个机器型工件落 `.workflow/flow/requirements/req-46-.../{requirement-review,planning}/`，`artifacts/main/requirements/req-46-.../` 下无 `requirement-review/` / `planning/` 子目录残留，`artifacts/.../requirement.md`（§2 白名单 raw 副本）保留。
- **AC-2（lint 全绿）**：`python3 -m harness_workflow.cli validate --contract artifact-placement` exit 0（升级后 lint 全仓库扫无违规）。
- **AC-3（lint 真敏感）**：刻意构造新违规（如复制 `sug-audit.md` / `session-memory.md` 到 `artifacts/main/requirements/{某req}/某-stage/` 子目录），升级后的 lint 必须命中并报 FAIL。
- **AC-4（白名单不误伤）**：`artifacts/main/requirements/{req-id}-{slug}/requirement.md`（§2 白名单 raw 副本）不再被 lint 命中报 FAIL。
- **AC-5（stage 退出门禁接入）**：`analyst.md` 退出条件含 `harness validate --contract artifact-placement` 文字；新派发的 analyst subagent briefing JSON 含 `expected_artifact_paths` 字段；`harness next` 在 analyst 流转点触发该 lint。
- **AC-6（scaffold_v2 mirror 一致）**：`diff -rq .workflow/context/roles/ src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/` 与 `diff -rq .workflow/context/checklists/ src/harness_workflow/assets/scaffold_v2/.workflow/context/checklists/` 均无差异。
- **AC-7（sug-35 落地翻转）**：`review-checklist.md` 含 `artifact-placement 反向抽样（高）` 条目；`sug-35` frontmatter 字段 `status: archived` + `applied_by_chg: chg-01`，文件迁入 `.workflow/flow/archive/suggestions/`（按 sug 归档约定）。

## 6. Risks

- **风险 1（lint 误伤合规场景）**：lint 升级后路径模式扫可能误伤非 req 路径（如 `artifacts/main/bugfixes/` / `artifacts/main/suggestions/`）或合法 stage-name-like 子目录。**缓解**：先以 WARN 模式上线一轮（不阻塞 CI），验证两周无误伤后切 FAIL；同时白名单豁免 §2 列出的所有合法路径模式。
- **风险 2（升级 lint 自我命中导致工作流卡死）**：lint 在 Step 4 升级前若 Step 1（git mv）未先做，升级后 lint 会立即把 req-46 现场 4 件违规命中阻塞本 chg 自身推进。**缓解**：Step 1（git mv）必须严格在 Step 4（lint 升级）之前执行；DAG 在 plan.md §3 明确硬序约束。
- **风险 3（briefing 模板改动面广）**：`expected_artifact_paths` 字段改动影响所有 stage 派发，可能破坏现有派发链路。**缓解**：字段先以可选（optional）形态注入，subagent 端不强校验；后续 chg 评估是否升为必选。
- **风险 4（scaffold_v2 mirror 漂移）**：双写 `.workflow/` + `scaffold_v2/.workflow/` 易遗漏。**缓解**：本 chg 验证步骤 2.1 含 `diff -rq` 强制校验，AC-6 不绿不放行。

## 7. Dependencies

- **前置依赖**：无。本 chg 是 req-46 roadmap 之外的紧急前置项，不依赖任何其他 chg。
- **后续 chg 依赖**：chg-02（按 roadmap 首批之 1）/ chg-03（首批之 2）/ chg-NN（首批之 3）等 req-46 主线 chg 必须等本 chg 完成（acceptance PASS）后再启动；否则后续 chg 仍在违规面上工作，每生成一份机器型工件就多一份再误落风险。
