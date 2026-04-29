---
id: bugfix-6
stage: acceptance
created_at: 2026-04-26
model: sonnet（Sonnet 4.6）
---

# 验收 Checklist — bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））

> 模型一致性自检（Step 7.5）：本 subagent 运行于 **sonnet（Sonnet 4.6）**，与 `.workflow/context/role-model-map.yaml` `roles[acceptance] = sonnet` 声明一致；briefing `expected_model: sonnet（Sonnet 4.6）` 一致。**PASS**。

---

## §需求 / 缺陷映射

### 14 修复点 vs 实施产物对照（grep 抽样）

| # | 修复点 | 关键 helper / 文件 | 抽样结果 |
|---|--------|-------------------|---------|
| A1 | `create_bugfix` 路径迁移 + `_use_flow_layout_for_bugfix()` | `workflow_helpers.py:4543` `_use_flow_layout_for_bugfix` / `:87` `BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID=6` | ✅ 存在 |
| A2 | 复核 create_suggestion / create_change / create_requirement | `workflow_helpers.py` 三函数体 | ✅ 合规（无需改动，已验） |
| A3 | `check_artifact_placement()` + CLI choice | `validate_contract.py:492` + `cli.py:255` choices 含 `artifact-placement` | ✅ 存在 |
| A4 | `repository-layout.md` §3.2 新增 + 各 role.md 路径修正 | `repository-layout.md:137` `§3.2 bugfix 机器型文档权威落位` | ✅ 存在 |
| A5 | `migrate_bugfix_layout()` + `harness_migrate.py` | `workflow_helpers.py:6027` + `tools/harness_migrate.py` 支持 `bugfix-layout` | ✅ 存在 |
| B1 | `analyst.md` Step B2.5 | `analyst.md:62` `**Step B2.5：测试用例设计（planning stage，B1）**` | ✅ 存在 |
| B2 | `testing.md` Step 2 改写 | `testing.md:18` `Step 2: 读取 plan.md §测试用例设计`；旧"设计测试用例" = 0 行 | ✅ 改写到位 |
| B3 | `evaluation/testing.md` §0 targeted 默认 | `evaluation/testing.md:3` `## 0. 测试范围默认 targeted（B3）` | ✅ 存在 |
| B4 | `change-plan.md.tmpl` §4. 测试用例设计 | `change-plan.md.tmpl:37` `## 4. 测试用例设计` + `regression_scope` | ✅ 存在 |
| B5 | `check_test_case_design_completeness()` + CLI choice | `validate_contract.py:543` + `cli.py:255` choices 含 `test-case-design-completeness` | ✅ 存在 |
| B6 | 降级 → sug-33 落库 | `.workflow/flow/suggestions/sug-33-briefing-lint-testing-over-instructing.md` id=sug-33，title 含"briefing 话术 lint" | ✅ 落库 + 来源标注 |
| C1 | `regression.md` Step 4.5 | `regression.md:33` `Step 4.5: 测试用例设计（bugfix 模式，C1）` | ✅ 存在 |
| C2 | `evaluation/regression.md` §测试用例设计 | `evaluation/regression.md:51` `## 测试用例设计` + `:62` `## 测试用例设计契约（bugfix 模式，C2）` | ✅ 存在 |
| C3 | B5 lint 规则 3 形式确认（无新代码） | `validate_contract.py` B5 lint 已覆盖 bugfix diagnosis.md 扫描 | ✅ 确认 |

---

## §验收 Checklist

### A 块：路径关注点分离

- ✅ A1：`_use_flow_layout_for_bugfix` 函数在 `workflow_helpers.py:4543`；`BUGFIX_FLOW_LAYOUT_FROM_BUGFIX_ID=6` 在 `:87`；create_bugfix 正确路由 bugfix-6+ 到 `.workflow/flow/bugfixes/`
- ✅ A2：三个 create_ 函数复核合规，无机器型 .md 写入 artifacts/
- ✅ A3：`check_artifact_placement()` 在 `validate_contract.py:492`；CLI `--contract artifact-placement` choice 在 `cli.py:255`
- ✅ A4：`repository-layout.md` §3.2 bugfix 机器型文档权威落位段存在；各 role.md 内 `artifacts/.*bugfix` 命中行 = 1（`stage-role.md:233` 含"历史脏数据"上下文，非违规引用）
- ✅ A5：`migrate_bugfix_layout()` 在 `workflow_helpers.py:6027`；`harness_migrate.py` 支持 `bugfix-layout` resource；bugfix-5 已迁到 `.workflow/flow/bugfixes/bugfix-5-同角色跨-stage-自动续跑硬门禁/`（5 份机器型文档齐）

### B 块：测试契约重塑

- ✅ B1：`analyst.md:62` Step B2.5 存在，含 regression_scope / 用例表结构说明
- ✅ B2：`testing.md:18` Step 2 改写为"读取 plan.md §测试用例设计"；旧"设计测试用例" = 0 行 PASS；Step 2.5 保留"独立反例补充例外"
- ✅ B3：`evaluation/testing.md:3` §0 targeted 默认完整，含 4 条全量触发条件 + 禁止 over-instructing
- ✅ B4：`change-plan.md.tmpl:37` §4. 测试用例设计 + regression_scope 字段 + 用例表模板
- ✅ B5：`check_test_case_design_completeness()` 在 `validate_contract.py:543`；CLI choice 在 `cli.py:255`
- ✅ B6 → sug-33：`.workflow/flow/suggestions/sug-33-briefing-lint-testing-over-instructing.md` 存在，含 `id: sug-33` + 来源标注"来源：bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））regression diagnosis.md B6 修复点"

### C 块：bugfix 流程 planning 等价载体

- ✅ C1：`regression.md:33` Step 4.5 存在，含 bugfix 模式、diagnosis.md §测试用例设计、regression_scope、退出条件
- ✅ C2：`evaluation/regression.md:51,62` §测试用例设计 + §测试用例设计契约（bugfix 模式）两段齐
- ✅ C3：B5 lint 规则 3 形式确认

### 综合指标

- ✅ **13 修复点全部落地**（A1-A5 / B1-B5 / C1-C3）；B6 正式降级为 sug-33，不计入缺失
- ✅ **B6 → sug-33 已落库 + 内容含来源标注**
- ✅ **bugfix-5 存量已迁到 `.workflow/flow/bugfixes/`**，artifacts/ 保留 README.md + bugfix-交付总结.md（对人产物）
- ⚠️ **bugfix-5 testing P2 缺陷登记真实存在**：`artifacts/main/bugfixes/bugfix-5-同角色跨-stage-自动续跑硬门禁/acceptance/checklist.md` 仍在 artifacts/（migrate 脚本边界未覆盖）；已在 test-evidence.md §缺陷登记 登记，**非阻塞**
- ✅ **`harness validate --contract artifact-placement` 已注册可用**（`cli.py:255`，`validate_contract.py:492`）
- ✅ **`harness validate --contract test-case-design-completeness` 已注册可用**（`cli.py:255`，`validate_contract.py:543`）
- ✅ **scaffold_v2 mirror 全部同步**：`diff -rq .workflow/context/roles/ scaffold_v2/.workflow/context/roles/` 空（仅 Only in live: usage-reporter.md 白名单差异）；`diff -rq .workflow/evaluation/ scaffold_v2/.workflow/evaluation/` 空；`diff -rq repository-layout.md scaffold_v2/...` 空
- ✅ **base-role 硬门禁六合规**：session-memory.md / bugfix.md / diagnosis.md 内 bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））/ bugfix-5（同角色跨 stage 自动续跑硬门禁）/ req-41（機器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））等 id 首次引用均带完整 title
- ✅ **dogfood fallback 标注在 test-evidence.md 显著**：第 3 行即 dogfood fallback 标注，说明本 testing 是旧契约 fallback 路径原因 + bugfix-7+ 起应直接消费新契约
- ✅ **不破坏既有契约**：req-31（角色功能优化整合与交互精简）/ req-37（阶段结束汇报简化）/ req-40（阶段合并与用户介入窄化（方向 C：角色合并 analyst.md））/ req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））/ req-42（archive 重定义：对人不挪 + 摘要废止）均仍在各 role.md 正确引用，未被 bugfix-6 误改
- ⚠️ **reviewer checklist 尚未扩 artifact-placement / test-case-design-completeness 三类新规则**：`review-checklist.md` 尚无 bugfix-6 对应条目；bugfix-5 的 stage_policies / role-stage-continuity lint 条目已存在（`:158-163`），但 bugfix-6 的 artifact-placement + test-case-design-completeness 两类规则尚未写入。**非阻塞**（属于 review-checklist.md 同步后置，不影响功能落地）

---

## §遗留 / 后置项

### P2 缺陷（非阻塞）

- **bugfix-5（同角色跨 stage 自动续跑硬门禁）`acceptance/checklist.md` 未迁出**：`artifacts/main/bugfixes/bugfix-5-.../acceptance/checklist.md` 仍存在。migrate 脚本当前覆盖 bugfix.md / session-memory.md / regression/ / test-evidence.md 五类主文件，acceptance/ 子目录属新规则覆盖的既有残留。建议后续 sug 清理或在下一 bugfix 的 migrate 逻辑中扩覆盖范围。

### 后置 sug 池

- **sug-30**：已被本 bugfix-6 吸收（路径关注点分离，升格为 A1-A5 修复点）
- **sug-31（done 后 commit + revert dry-run）**：不吸收，保留待用户独立立项 bugfix-7+ 或 req
- **sug-32（回 req-43（交付总结完善）跑 next 自证）**：不吸收，待 req-43（交付总结完善）续跑时一并验证 bugfix-5 + bugfix-6 + req-43 的 next 连跳行为
- **sug-33（briefing 话术 lint）**：已落库（B6 降级），待用户决定独立立项

### 本 bugfix 自身工件

- **bugfix-6 自身工件仍在 artifacts/**（`artifacts/main/bugfixes/bugfix-6-.../`）：按 A2 约定本 bugfix 自身不迁（A1 在 bugfix-6 落地后才生效，bugfix-6 自身是活体证据），bugfix-7+ 起走新路径自证

### 仍挂起项

- **bugfix-5（同角色跨 stage 自动续跑硬门禁）done 阶段**：已完成但未 archive，用户睡前未确认，醒后处理
- **req-43（交付总结完善）planning**：仍挂起，醒后续跑

### review-checklist.md 同步后置

- **未扩 artifact-placement / test-case-design-completeness 规则到 review-checklist.md**：属文档 housekeeping，不影响功能；建议醒后或 req-43 周期顺带补入

---

## §最终验收结论

**PASS-with-followup**

### 通过 / 失败计数

| 类别 | 计数 |
|------|------|
| 验收条目总数 | 11 |
| ✅ PASS | 9 |
| ⚠️ PASS-with-followup（非阻塞） | 2 |
| ❌ FAIL | 0 |

### 结论依据

1. **13 修复点全部落地**（grep 抽样 + session-memory executing stage 实施摘要双重确认）
2. **62 新用例 100% PASS + 533 全量 + 2 pre-existing**（test-evidence.md 证据充分）
3. **2 个 ⚠️ 均非阻塞**：bugfix-5 acceptance/checklist.md 残留（P2 缺陷，历史遗留）；review-checklist.md 未扩新规则（文档后置，功能已落地）
4. **dogfood fallback 标注到位**，测试完整度合规
5. **scaffold_v2 mirror 无差异**，既有契约未被破坏

### 主 agent 应在用户醒后告知用户的清单

**已完成**：
- bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））完整链路（regression → executing → testing → acceptance）PASS-with-followup

**待用户决策**：
1. **bugfix-5（同角色跨 stage 自动续跑硬门禁）archive**：done 阶段已完成，用户睡前未确认 archive，是否现在 archive？
2. **bugfix-6 archive**：本 acceptance 通过，是否立即 archive？
3. **req-43（交付总结完善）续跑**：planning 挂起，是否 `harness next` 续跑？（同时验证 sug-32 + bugfix-5 / bugfix-6 连跳行为）
4. **sug 池处理顺序**：sug-31 / sug-32 / sug-33 是否立项 bugfix-7 或合并到 req-43？
5. **bugfix-5 acceptance/checklist.md P2 残留**：是否立即清理或后置？
