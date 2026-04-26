# Regression Diagnosis — bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））

> 本 bugfix 为**融合 bugfix**，打包用户连续提出的 3 件未决工作流契约问题（A / B / C）+ 1 件附带决策（D）。
> 本 diagnosis 按 3+1 事项块独立形式化诊断，每块输出现象 / 预期 / 根因 / 影响面 / 判断 / 路由；末尾汇总附带决策 D。
> 当前 bugfix-6 的 layout（`artifacts/main/bugfixes/bugfix-6-...../{bugfix.md, session-memory.md, regression/diagnosis.md, regression/required-inputs.md, test-evidence.md}`）即事项 A 的活体证据——本 diagnosis 自身落位违规。
>
> 模型自检：本 subagent 运行于 opus（Opus 4.7 / 1M context），与 `.workflow/context/role-model-map.yaml` `roles[regression] = opus` 声明一致。

---

## 事项 A：对人 / 机器型工件路径关注点分离强化

### 现象

- 用户原话（2026-04-25 夜）："请再次核查所有的工作流，保证对于所有的任务对人文档均在 artifacts 中，且 artifacts 中禁止放非对人文档，sql 等制品产出算对人。所有的流程文档均归 .flow 文件夹管理。"
- 用户进一步澄清："sql 等制品产出算对人"——artifacts/ 不只放交付总结类文档，**所有最终产出物**（sql / 报告 / PDF / 图表 / 对外发布）都算对人；只有"工作流过程文档"（session-memory / diagnosis / test-evidence / bugfix.md / change.md / plan.md / checklist.md 等 agent 间协作的机器型/中间型）才在 `.workflow/flow/`。
- 实证：当前 bugfix-6 自身的目录树即违规——`artifacts/main/bugfixes/bugfix-6-工作流契约统一加固-对人机器分离-测试契约重塑/` 下混放：
  - `bugfix.md`（机器型，等价于 requirement.md）
  - `session-memory.md`（机器型）
  - `regression/diagnosis.md`（机器型，本文件本身）
  - `regression/required-inputs.md`（机器型）
  - `test-evidence.md`（机器型）
- 0 份对人产物。

### 预期（契约层文档原文引用）

- `.workflow/flow/repository-layout.md` §1（行 19-25）：三大子树语义总览——`artifacts/{branch}/` "对人可读签字执行产物。只装人可直接阅读、执行或签字的产物；**不**出现机器型文档。"
- `.workflow/flow/repository-layout.md` §3（行 99-131）：req 级 / chg 级 / regression 级机器型文档"权威路径（req-41+ flow 新位）" = `.workflow/flow/requirements/{req-id}-{slug}/...`。
- `.workflow/flow/repository-layout.md` §4 禁止行为（行 187-191）："禁止把机器型文档写入 `artifacts/` 下任何路径（req-41+ 严格执行）。"
- 现有 req 路径（req-41 / req-42 / req-43）已遵守：`requirement.md` 落 `.workflow/flow/requirements/{req-id}-{slug}/requirement.md`，`artifacts/` 仅留对人产物（done 阶段写 `交付总结.md`）。

### 根因分析

- **L1 现象层**：bugfix-6 的所有 5 份机器型文档落 `artifacts/` 下，0 份对人产物，artifacts/ 与 `.workflow/flow/` 双轨混淆。
- **L2 行为层**：CLI helper `create_bugfix`（`src/harness_workflow/workflow_helpers.py:4540-4626`）硬编码 `bugfix_dir = root / "artifacts" / branch / "bugfixes" / dir_name`，把 bugfix.md / session-memory.md / regression/diagnosis.md / regression/required-inputs.md / test-evidence.md 全部 write_if_missing 到该 artifacts 路径下。
- **根本根因**：req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））/ chg-02（CLI 路径迁移 flow layout）只把"关注点分离"契约施加到 **requirement 路径**：`create_requirement` 走 `_use_flow_layout(req_id)` 三分支（flow / flat / legacy），机器型文档落 `.workflow/flow/`；但**未对 bugfix 路径做对应改造**，`create_bugfix` 至今仍走 req-38 之前的 legacy 全 artifacts/ 行为。req-42（archive 重定义：对人不挪 + 摘要废止）契约同样仅约束 req archive，未触达 bugfix 周期。`harness_suggest.py` / `harness_change.py` 路径需复核（change 已挂在 req 树下，应继承 req 的 layout 选择；suggest 直接落 `.workflow/flow/suggestions/`，本身不落 artifacts/，但 done 阶段产生的 sug 可能违规需复核）。
- **结构根因**：契约定义层（`repository-layout.md`）只覆盖 requirement 树，没有"任务类型无关"的硬门禁；新增任务类型（bugfix / sug-direct / 任意未来类型）时，契约不会自动覆盖，依赖每次手动同步——这是**契约可扩展性缺陷**，本 bugfix 必须把契约升级为"任意任务类型"通用约束。

### 影响面

- 5 份历史 bugfix 工件全部错位（bugfix-1 ~ bugfix-5）+ 当前 bugfix-6 自身：6 个 bugfix 周期、≈ 30+ 份机器型文档落在 artifacts/ 下，不符合关注点分离契约。
- 用户 "artifacts 应只装对人" 的认知与实际仓库状态长期相悖，影响外部审阅者 / PM / 运维对仓库结构的信任。
- 目前没有 lint 拦截"artifacts/ 含机器型文件"或".workflow/flow/ 含对人最终产物"，违规可无声引入。
- sug-30（bugfix 路径关注点分离）已在 bugfix-5 done 阶段登记，本 bugfix 升格吸收 sug-30 + 扩展契约面到任意任务类型。

### 判断

- **confirmed / 真实问题**：契约层与实现层不一致，且契约层本身覆盖面不足。

### 路由

- → executing。具体修复方案在 bugfix.md §修复方案 事项 A 块（A1 ~ A5）。

---

## 事项 B：测试契约重塑（planning 设计用例 + testing 仅执行）

### 现象

- 用户原话 1（2026-04-25 夜）："如果是全量，那么加一个逻辑，在计划阶段需要设计好测试用例，测试阶段的 subagent 直接对测试用例负责就行了。计划阶段的测试用例设计需要覆盖所有的本次工作波及范围接口。"
- 用户原话 2："testing 二次全过（10 用例全 PASS / 0 缺陷 / 471 全量回归）我们现在的测试流程都是在做所有功能的全量回归吗？"
- 实证（已查实）：
  - `.workflow/context/roles/testing.md` Step 2（行 18-22）："设计测试用例"——testing 自己基于 AC 设计用例。
  - 同文件 Step 2.5（行 23-27）："编写单元测试代码"——testing 自己写测试代码。
  - 同文件 Step 2.75（行 29-33）：合规扫描默认范围 = `git diff --name-only`（targeted），但实际 bugfix-5 周期 testing subagent 跑了 `pytest tests/`（374 → 471 用例全量），原因是主 agent 在 briefing 文本里写 `pytest tests/ -x` 全量。
  - `.workflow/evaluation/testing.md` 章节 1（行 39-43）：默认扫描范围 = `git diff` 命中文件（default-pick P-5 = A，保守范围），契约本身不要求全量。

### 预期（契约层文档原文引用）

- 用户期望"测试用例设计权责前移到 planning 阶段"：planning（analyst 角色，覆盖 stages = [requirement_review, planning]）的 plan.md 必须含 §测试用例设计章节，覆盖所有波及接口的 AC 用例（用例名 / 输入 / 期望 / AC 链接 / 优先级）。
- 用户期望 testing subagent "直接对测试用例负责" = 读取 plan.md §测试用例设计 → 实现为可执行单测代码 → 执行 → 记录通过/失败，不再独立设计主线（保留独立反例补充权）。
- 用户期望默认 targeted、全量回归仅在 acceptance / done 阶段或 planning 显式标记需要时才跑。

### 根因分析

- **L1 现象层**：testing subagent 跑了 471 全量用例，超出契约要求（契约只要求 targeted）。
- **L2 行为层**：主 agent（harness-manager）在 briefing 文本里 over-instructing 让 testing 跑 `pytest tests/ -x` 全量；testing.md SOP 同时定义 "Step 2 设计 + Step 2.5 编写"，testing 责任过重，AC 覆盖一致性靠 testing 当场推断，质量不稳定。
- **根本根因**：**测试用例设计权责错配**——AC 出自 requirement.md / change.md（analyst 写），最了解波及范围 / 接口边界的也是 analyst；让 testing 重新基于 AC "再设计一遍用例" 是责任倒挂，且 testing subagent（sonnet 模型）不擅长全局推断"波及接口"。把"测试用例设计"前移到 planning（analyst / opus 模型）才是对模型能力 + 责任来源的正确分配。
- **结构根因**：现有测试契约把"设计 + 执行"耦合在 testing 单一 stage，没有 planning → testing 的契约接口（plan.md §测试用例设计）；导致测试用例的"覆盖完整性"无法在 planning 阶段被审阅 + 拍板，质量门禁后置到 testing 才能被发现。

### 影响面

- 每次 bugfix / req 周期 testing 都可能被主 agent 派发跑全量回归（471+ 用例），CI 时间膨胀、token 浪费；或反之 testing 独立设计的用例覆盖不全，acceptance 才暴露缺陷（已在 bugfix-5 周期发现"AC 覆盖度依赖 testing 当场推断"风险）。
- 影响所有 ≥ req-id 41 / 所有未来 bugfix 周期。
- analyst.md / testing.md / planning.md（legacy alias）/ requirement-review.md（legacy alias）/ evaluation/testing.md / change-plan.md 模板 + scaffold_v2 mirror 全部需要联动改。

### 判断

- **confirmed / 真实问题**（"全量回归是否每次都跑"是症状，"测试用例设计权责前移"是用户给出的根本契约重塑方案）。

### 路由

- → executing。具体修复方案在 bugfix.md §修复方案 事项 B 块（B1 ~ B6）。

---

## 事项 C：bugfix 流程是否走 planning（bugfix 流程现无 planning 阶段）

### 现象

- 事项 B 把测试用例设计前移到 planning，但 **bugfix 流程跳过 requirement_review + planning** 直接走 regression → executing → testing → acceptance → done（见 `.workflow/context/role-model-map.yaml` `stage_policies` + harness_bugfix CLI 实现）—— bugfix 没有 planning 阶段，"测试用例设计"无处落地。

### 预期

- bugfix 周期短（通常 < 1 天），不应引入新阶段（如 planning-lite）让流程膨胀。
- bugfix 的 regression 阶段已经做"根因分析 + 修复方案"——最了解波及范围的就是 regression subagent 自己。
- 测试用例设计应作为 regression 阶段的自然延伸落地，testing subagent 直接消费。

### 根因分析

- **L1 现象层**：事项 B 的契约前提（plan.md §测试用例设计）在 bugfix 流程中无对应载体。
- **L2 行为层**：bugfix 流程的 `stage_policies` 不含 planning（regression 直接 verdict → executing），diagnosis.md 模板只含问题描述 / 根因 / 路由方向，无测试用例设计章节。
- **根本根因**：bugfix 流程是 req 流程的"快速版精简映射"，省去 requirement_review + planning 是历史正确选择（用户认可），但事项 B 的"测试用例设计"前移引入了"无 planning 即无测试设计载体"的契约空洞。

### 影响面

- 若不修复，事项 B 落地后 bugfix 流程的 testing subagent 无 planning 单可读，回退到独立设计 = 与事项 B 契约打架。
- 影响所有未来 bugfix 周期（含本 bugfix-6 自身的 testing 阶段执行）。

### 判断

- **confirmed / 真实问题**（事项 B 引入的契约空洞，需在同一 bugfix 内补齐）。

### 路由 + default-pick

- → executing。
- **default-pick D-B1（推荐）**：bugfix 流程的 **regression 阶段** 担纲 planning 等价职责——`regression/diagnosis.md` 在 §修复方案末尾 **新增 §测试用例设计** 章节（同 plan.md §测试用例设计 结构：用例名 / 输入 / 期望 / AC / 优先级），testing 直接消费。
- **理由**：bugfix 周期短、regression 已经做根因 + 修复方案分析（最了解波及范围），加测试用例设计是自然延伸，避免引入新阶段；同时与事项 B 的 plan.md §测试用例设计 结构对齐，testing.md SOP "读取 plan.md §测试用例设计 → 实现为单测 → 执行 → 记录" 在 bugfix 模式下回退到 "读取 diagnosis.md §测试用例设计"。
- **替代方案 D-B2（已弃）**：在 bugfix 流程中新增 planning-lite 阶段。弃用理由：违反"bugfix 短平快"原则、stage_policies 复杂化、用户未认可。
- 具体修复方案在 bugfix.md §修复方案 事项 C 块（C1 ~ C3）。

---

## §事项 D 附带决策（sug-31 / sug-32 处理）

### sug-31（done 后 commit + revert dry-run 自动化）

- **default-pick = 不吸收**。
- **理由**：本 bugfix scope 已涵盖 3 件契约重塑（A / B / C，预计 ≤ 12 修复点），commit + revert dry-run 自动化属于另一类 CI / 钩子工程（涉及 git hooks / pre-commit / GitHub Action），与本 bugfix 关注点分离 + 测试契约重塑无技术耦合，应独立成 bugfix-7+ 或 req。
- **后续动作**：保留 sug-31 在 `.workflow/flow/suggestions/` 待用户决定独立立项。

### sug-32（回 req-43（交付总结完善） 跑 next 端到端验证连跳自证）

- **default-pick = 不吸收**。
- **理由**：sug-32 是 bugfix-5（同角色跨 stage 自动续跑硬门禁） 的验证后置项，与本 bugfix scope（关注点分离 + 测试契约）无技术关联；保留 sug-32 待 bugfix-6 完成后由用户决定 req-43（交付总结完善） 续跑时一并处理（届时同时验证 bugfix-5 + bugfix-6 + req-43 的 next 连跳行为，更高 ROI）。
- **后续动作**：保留 sug-32 在 `.workflow/flow/suggestions/` 待用户决定。

---

## 综合结论

- 事项 A / B / C 均判 confirmed，路由 → executing；事项 D 不吸收（保留 sug-31 / sug-32 待独立处理）。
- 全部修复方案细节（精确到文件路径 + 改什么）见同目录 `bugfix.md` §修复方案。
- 用户已睡：所有 default-pick（D-B1 等）不阻塞推进，主 agent 按本 diagnosis 路由即可推进 executing。

---

## 测试用例设计

> regression_scope: targeted
> 波及接口清单（git diff --name-only 自动生成 + 人工补全）：
> - src/harness_workflow/workflow_helpers.py（A1/A2/A5：create_bugfix / migrate_bugfix_layout）
> - src/harness_workflow/validate_contract.py（A3/B5/C3：artifact-placement / test-case-design-completeness）
> - src/harness_workflow/cli.py（A3/B5：--contract choices 扩展）
> - src/harness_workflow/tools/harness_migrate.py（A5：bugfix-layout resource）
> - .workflow/context/roles/analyst.md（B1：Step B2.5）
> - .workflow/context/roles/testing.md（B2：Step 2 / Step 2.5 改写）
> - .workflow/evaluation/testing.md（B3：§0 targeted 默认）
> - .workflow/context/roles/regression.md（C1：Step 4.5）
> - .workflow/evaluation/regression.md（C2：§测试用例设计 模板）
> - src/harness_workflow/assets/skill/assets/templates/change-plan.md.tmpl（B4）
> - src/harness_workflow/assets/skill/assets/templates/change-plan.md.en.tmpl（B4）
> - .workflow/flow/repository-layout.md（A4：§3.2 bugfix 落位）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 create_bugfix flow layout | `create_bugfix(root, "test", "bugfix-7")` | `.workflow/flow/bugfixes/bugfix-7-*/` 含 5 份机器型文档 | A1 | P0 |
| TC-02 create_bugfix artifacts placeholder | 同上 | `artifacts/main/bugfixes/bugfix-7-*/README.md` 存在，无机器型 .md | A1 | P0 |
| TC-03 _use_flow_layout_for_bugfix | `bugfix-6` → True；`bugfix-5` → False | 布尔值正确 | A1 | P0 |
| TC-04 migrate_bugfix_layout dry-run | `migrate_bugfix_layout(root, dry_run=True)` | 文件未移动，rc=0 | A5 | P0 |
| TC-05 migrate_bugfix_layout execute | `migrate_bugfix_layout(root)` on bugfix-2 | 机器型文档迁到 flow/，artifacts/ 留 README | A5 | P0 |
| TC-06 migrate skips bugfix-6+ | bugfix-6 in artifacts/ | 不迁移，flow/ 无 bugfix-6 | A5 | P0 |
| TC-07 artifact-placement FAIL | artifacts/ 含 bugfix.md | rc=1，输出违规路径 | A3 | P0 |
| TC-08 artifact-placement PASS | artifacts/ 仅含 README.md | rc=0 | A3 | P0 |
| TC-09 plan.md 缺 §测试用例设计 → FAIL | plan.md 无 §4 | rc=1 | B5 | P0 |
| TC-10 plan.md 含完整用例 → PASS | plan.md 含表格数据行 | rc=0 | B5 | P0 |
| TC-11 diagnosis.md 缺 §测试用例设计 → FAIL | flow/bugfixes/*/regression/diagnosis.md 无 §测试用例设计 | rc=1 | B5/C3 | P0 |
| TC-12 diagnosis.md 含完整用例 → PASS | 含表格数据行 | rc=0 | B5/C3 | P0 |
| TC-13 analyst.md Step B2.5 存在 | grep analyst.md | 含 B2.5 + regression_scope | B1 | P1 |
| TC-14 testing.md Step 2 改写 | grep testing.md | 无"设计测试用例"，有"读取 plan.md §测试用例设计" | B2 | P1 |
| TC-15 evaluation/testing.md §0 存在 | grep testing.md | 含 targeted + 全量触发条件 + 禁止 | B3 | P1 |
| TC-16 change-plan.md.tmpl §4 章节 | grep tmpl | 含 §4. 测试用例设计 + regression_scope + 表格 | B4 | P1 |
| TC-17 regression.md Step 4.5 存在 | grep regression.md | 含 Step 4.5 + bugfix 模式 | C1 | P1 |
| TC-18 evaluation/regression.md §测试用例设计 | grep | 含 §测试用例设计 + 必填 + test-case-design-completeness | C2 | P1 |
