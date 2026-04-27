# Regression Analysis

## 1. Problem Assessment

**真实问题**（confirmed），非误判、非期望偏差、非用户误解。已通过 4 维根因取证证实违规事实存在 + 契约 / lint 都已就位但失效。

## 2. Evidence

### 2.1 契约文字证据

读 `.workflow/flow/repository-layout.md`：

- §1（行 17-25）三大子树语义：`artifacts/{branch}/` 类目"只装人可直接阅读、执行或签字的产物；**不**出现机器型文档。任意任务类型（req / bugfix / sug 等）均遵守此约束（bugfix-6 A4）"。
- §1.2（行 67-70）关键约束：`artifacts/main/requirements/{req-id}-{slug}/` 下"**无 changes/ 子目录**，对人文档全部平铺。... 只有对人文档（见 §2 白名单）允许存入"。
- §2（行 78-91）白名单仅含 9 类：raw `requirement.md` / `交付总结.md` / `决策汇总.md` / SQL / 部署文档 / 接入配置说明 / runbook / 手册 / 合同附件 / bugfix 交付总结 / sug 交付总结 / 其他对人产物。**`session-memory.md` / `sug-audit.md` / `roadmap.md` 均不在白名单**。
- §3（行 101-135）机器型权威落位：`session-memory.md` 落 `.workflow/flow/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/` 或 `.workflow/flow/requirements/{req-id}-{slug}/regressions/{reg-id}-{slug}/`。stage 级 session-memory（如 requirement-review / planning）虽未列表但按"机器型 → flow/" 通则归属。

### 2.2 lint 实证证据

执行 `python3 -m harness_workflow.cli validate --contract artifact-placement` 现场命中（仅取 req-46 部分）：

```
artifacts/ 下发现机器型文件：artifacts/main/requirements/req-46-.../requirement-review/session-memory.md
artifacts/ 下发现机器型文件：artifacts/main/requirements/req-46-.../planning/session-memory.md
```

（`sug-audit.md` / `roadmap.md` 文件名不在 `_MACHINE_TYPE_FILENAMES` frozenset 内，未被 lint 命中——见 §3.2 机制原因）。

lint 实现证据：`src/harness_workflow/validate_contract.py:493 check_artifact_placement`，bugfix-6 / A3 已落地。

### 2.3 角色文件证据

读 `.workflow/context/roles/analyst.md`：

- §硬门禁（行 23）声明 "harness validate 硬门禁：两 stage 交接前各执行一次 `harness validate --human-docs`，exit code ≠ 0 立即 ABORT"——只列 `--human-docs`，**不含** `--contract artifact-placement`。
- §退出条件（行 119-131）只列 `harness validate --human-docs` 与 `harness validate --contract test-case-design-completeness`，**不含** `harness validate --contract artifact-placement`。
- 全文未出现"产出工件前必读 repository-layout.md"硬门禁。

读 `.workflow/context/roles/stage-role.md` 契约 2 / 3 / 4：把路径细节"全部下放"给 `repository-layout.md`，本身**不含**可执行的"路径检查 SOP 步骤"——契约文字停留在概念层，缺少操作层硬门禁。

### 2.4 checklist 证据

读 `.workflow/context/checklists/review-checklist.md`：

- 制品完整性章节（行 71-97）只检查"flow 制品存在 + 命名规范"+"artifacts/requirements 同步性"，**没有反向检查项**："artifacts/ 下有无机器型文件误落"。
- 阶段速查表 requirement_review / planning 重点（行 105-117）也无 artifact-placement 抽样。
- sug-35（reviewer checklist 扩 artifact-placement / test-case-design-completeness 三类 lint 条目补全）已记录此空白，状态 pending（2026-04-26 入池），**未落地**。

### 2.5 历史回溯（spot-check）

执行 `ls artifacts/main/requirements/req-{42,43,44,45}-*/`：

- req-42 / req-43 / req-44 / req-45 artifacts/ 目录**只**含 `交付总结.md`，无 stage 子目录、无机器型文件。
- 即 req-41 立契约后，req-42 ~ req-45 **全部正确落位**；req-46 是**第一例反例**进入活跃 req（reg-01..05 + bugfix-2/3/6 archive 是 lint 实现前的历史脏数据，不是新违规）。

证明：契约和 lint 不是过宽或失效，是**没有被 stage 角色触发**——首例反例出现在 req-46。

## 3. Discussion Outcome

### 3.1 直接原因

analyst（**req-46 现场执行者**）的行为模式是 "**读了 stage-role.md 契约 2 / 3 / 4 但未应用到实操**"——更具体：

- analyst.md 未把 "产出 stage 工件前先读 repository-layout.md §3 / 写到指定路径" 作为**操作层 SOP 步骤**列入；
- 主 agent 派发 analyst 的 briefing **未显式列出该 stage 工件的期望落点路径**（briefing 模板没强约束）；
- analyst 凭"路径同构 / artifacts 平铺 / 与 changes/ 同级"的**模糊记忆**自由发挥，把 session-memory / 工作产出（sug-audit / roadmap）当作"对人摘要"丢到 artifacts/。

非"未读 repository-layout.md"——实际上 analyst.md / stage-role.md 都已**指引**读 repository-layout.md，但仅指引"了解契约存在"，未指引"产出前对照路径表写到正确位置"——读了 ≠ 应用。

### 3.2 机制原因（5 层缺保护）

| 层 | 现状 | 缺口 |
|----|------|------|
| 1. briefing 模板 | 派发 analyst 的 briefing JSON 含 `task_context_index`（建议加载清单）但**未注入 stage 工件期望落点路径** | 应在 briefing 显式列：`stage 期望产出路径 = .workflow/flow/requirements/{req-id}/{stage}/...` |
| 2. analyst.md / stage-role.md 角色文件 | 契约 2 / 3 / 4 把路径下放给 repository-layout.md，无"产出前先读 §3"硬门禁；analyst.md 退出条件只跑 `--human-docs` + `--contract test-case-design-completeness` | 应加硬门禁：每个 stage 工件产出前对照 §3 路径表确认落点；退出条件加 `--contract artifact-placement` |
| 3. validate / lint 触发面 | `artifact-placement` lint **已实现**（bugfix-6 / A3），但**只在 reviewer / done 兜底**，未被纳入 analyst 等 stage 的退出门禁 | 应把 lint 加到 analyst.md 退出条件、harness next 退出 gate、briefing 自检步骤 |
| 4. lint 命中规则 | `_MACHINE_TYPE_FILENAMES` 仅含 17 项固定文件名，**漏掉**工作产出类（如 `sug-audit.md` / `roadmap.md`），同时**误命中**白名单内的 raw `requirement.md` 副本 | 应改为基于路径模式（artifacts/main/requirements/{req-id}/{stage-name}/* → FAIL）+ 白名单豁免（artifacts/.../requirement.md 是 §2 白名单合法项） |
| 5. reviewer checklist | sug-35 已记录"reviewer checklist 扩 artifact-placement 抽样"待办，**未落地** | 应在 review-checklist.md "制品完整性"章节加反向检查项 |

### 3.3 历史回溯结论

- req-41（立契约）→ req-42 ~ req-45（4 例正确落位）→ req-46（反例首例）。
- 反例出现条件：req-46 是**第一个**在 requirement-review / planning 两 stage 都产出**复杂中间工件**（sug-audit / roadmap）的 req——前面 req-42 ~ req-45 的 stage 内只产出 session-memory，且全部正确落 `.workflow/flow/`。
- req-46 复杂度上升 → analyst 临时把 sug-audit / roadmap 当作"对人摘要" → 顺手把 session-memory 也并行写 artifacts/。即"复杂度突破契约边界"，契约本身没坏，但缺**当复杂度上升时强制对照 §3 路径表的硬门禁**。

### 3.4 关联 sug

- **sug-35**（reviewer checklist 扩 artifact-placement / test-case-design-completeness 三类 lint 条目补全）：直接相关。本 reg-01 是 sug-35 未落地的实证。chg-0 必须含"落地 sug-35 reviewer checklist 扩展"条目。
- **sug-33**（briefing-lint-testing-over-instructing）：briefing 注入条款的相邻问题，可借势纳入 chg-0 思考"briefing 模板是否应该统一加路径注入条款"。

### 3.5 与 req-46 主线的耦合

- req-46 已识别 41 条 sug、planning 阶段已分批为 chg-1 / chg-2 / chg-7 等首批（详见 `.workflow/flow/requirements/req-46-.../planning/roadmap.md` ——本身就在违规位置）。
- chg-0 是 **roadmap 之外** 的紧急前置项，因为：
  1. 不修则首批仍在违规面上工作（每生成一个 chg 就多一份机器型工件，潜在再误落）。
  2. chg-0 涉及 lint 规则、角色文件、scaffold_v2 mirror、briefing 模板四线，工作量不大但**前置依赖**最强。
  3. 用户已明确要求"在本次需求中优先修复"——属于 base-role 硬门禁四例外条款边界外（非数据丢失 / 不可回滚 / 合规），但用户主动要求 = 直接采纳，不走 default-pick。

## 4. Recommended Action

**confirmed → 路由 planning** → 转 chg-0（机器型工件路径修复 + 防再犯 lint）。

详见 `decision.md` 与 `session-memory.md` chg-0 草案段。
