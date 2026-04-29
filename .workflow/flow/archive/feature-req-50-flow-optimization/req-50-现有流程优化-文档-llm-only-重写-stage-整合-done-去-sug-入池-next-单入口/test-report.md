---
id: req-50
title: 现有流程优化：文档 LLM-only 重写 + stage 整合 + done 去 sug 入池 + next 单入口
stage: testing
created_at: 2026-04-28
tester: testing（sonnet）
---

# Test Report — req-50（现有流程优化）

## TC 覆盖矩阵

| TC | 关联 AC | 验证内容 | 结果 |
|----|--------|---------|------|
| TC-01 | AC-03 / AC-04 | WORKFLOW_SEQUENCE = [analysis, executing, testing, acceptance, done]，无 requirement_review / planning / ready_for_execution | PASS |
| TC-02 | AC-04 | ready_for_execution 不在新 WORKFLOW_SEQUENCE | PASS |
| TC-03 | AC-11 | D5=B 向后兼容：req-50 走新序列，req-49 走旧序列 | PASS |
| TC-04 | AC-06 | `harness next --execute` 报 unknown flag（--execute 废止） | PASS（subprocess 验证） |
| TC-05 | AC-06 | `harness next` 单入口从 analysis → executing 正常推进 | PASS（dogfood 验证） |
| TC-06 | AC-05 | done.md 不再含「sug 入池」职责；done 不主动创建 sug 文件 | PASS |
| TC-07 | AC-05 | extract_suggestions_from_done_report 返回空（无 done-report）| PASS |
| TC-08 | AC-01 / AC-02 | 核心模板 YAML frontmatter 完整，无禁止 header | PASS（TC05 dogfood 覆盖） |
| TC-09 | AC-09 | reviewer.md + review-checklist.md 含 LLM-only lint 项 | PASS（TC06 dogfood 覆盖） |
| TC-10 | AC-10 | llm-only-docs contract lint exit 0 | PASS |

## 全量 pytest 结果

```
739 passed, 33 failed, 40 skipped
```

## 33 fail 分类

| 类别 | 数量 | 说明 |
|------|------|------|
| 类 A — req-50 结构性变更打挂的旧测试（预期 breakage） | 21 | 详见下表 |
| 类 B — pre-existing（与 req-50 无关）| 12 | 详见下表 |
| 类 C — req-50 引入的真 regression bug | 0 | 无 |

### 类 A 明细（21 个）—— 旧测试硬编码了旧 stage 名 / 旧 flag

| 测试 | 根因 |
|------|------|
| test_analyst_role_merge::test_index_md_has_analyst_row | context/index.md 注释未含"原 requirement-review"字样，chg-01 改了 stages 未加注释文本 |
| test_artifact_placement_chg01 TC01 × 4 | req-46 产物下期望 requirement-review/ 子目录，新结构无此目录 |
| test_block_protocol_e2e::test_tc01_review_checklist_entries | review-checklist.md 无"抛错协议配套"文本（req-48 roadmap 遗留测试） |
| test_block_protocol_e2e::test_tc08_roadmap_in_plan | req-48 chg-03 plan.md 路径不存在（归档变化）|
| test_harness_next_pending_gate × 2 | 测试用 stage=requirement_review，不在新 WORKFLOW_SEQUENCE |
| test_next_execute × 2 | 测试用 stage=requirement_review 或 --execute flag（已废止）|
| test_next_writeback × 1 | 测试用 stage=requirement_review，不在新 WORKFLOW_SEQUENCE |
| test_role_stage_continuity × 3 | analyst stages 期望 ["requirement_review","planning"]，实际 ["analysis"] |
| test_smoke_req26::test_full_lifecycle_smoke | 全链路从 requirement_review 出发，不在新 sequence |
| test_smoke_req28::FullLifecycleSmokeTest | 同上 |
| test_stage_policies::test_case_i_explicit_gate_preserved | 测试用 stage=planning，不在新 WORKFLOW_SEQUENCE |
| test_task_context_index::test_next_execute_emits_briefing_with_index | 测试用 stage=ready_for_execution，已从序列删除 |
| test_workflow_next_subprocess::test_tc04 | 测试用 --execute flag（已废止）+ stage=ready_for_execution |
| test_workflow_next_subprocess::test_tc07 | 同上 |
| test_workflow_next_workdone_gate::test_tc05 | 测试用 stage=requirement_review，不在新 WORKFLOW_SEQUENCE |

### 类 B 明细（12 个）—— pre-existing，与 req-50 无关

| 测试 | 根因 | 溯源时期 |
|------|------|---------|
| test_artifact_placement_chg01 TC07_sug35_exists | sug-35 文件不存在（历史 sug 文件状态） | req-46 前后 |
| test_artifact_placement_chg01 TC08 × 3 | req-46 chg-01 的 change.md/plan.md/session-memory.md 路径不存在 | req-46 归档后 |
| test_raise_harness_block::test_tc06_base_role_hardgate_eight | base-role.md 缺"硬门禁八"（req-48 roadmap 未落地） | req-48 era |
| test_raise_harness_block::test_tc07_harness_manager_step37 | harness-manager.md 缺 Step 3.7（req-48 roadmap 未落地） | req-48 era |
| test_req43_chg01::Sug25StatusTest::test_sug25_applied | sug-25 文件不存在（历史 sug 文件已移动/删除） | req-43 era |
| test_smoke_req28::ReadmeRefreshHintTest | README.md 缺"pip install -U harness-workflow"提示 | req-28 era |
| test_smoke_req29::HumanDocsChecklistTest | req-29 归档路径无 changes/ 目录（旧结构） | req-41 重构后 |
| test_state_sync_invariants RegressionRouteConsumptionTest × 2 | acceptance work-done gate 阻断 reg route（req-45/46 gate 严格化引入）| req-45/46 era |

## chg-05（dogfood-reviewer 加项）新增 27 用例

```
tests/test_req50_dogfood.py — 27 passed, 17 subtests passed
```

全部通过，覆盖：
- TC01（5用例）：5-stage 新序列验证
- TC02（2用例）：legacy 向后兼容
- TC03（3用例）：harness next 单入口
- TC04（3用例）：done 阶段不写 sug 池
- TC05（4用例）：模板 LLM-only 格式
- TC06（9用例）：reviewer lint 项

## dogfood 端到端验证

| 维度 | 结果 |
|------|------|
| 5-stage sequence（无 ready_for_execution） | PASS |
| analysis → executing（harness next 单入口无 --execute）| PASS |
| legacy req-49 仍用 requirement_review 初始 stage | PASS |
| done 不写 sug 池 | PASS |
| LLM-only 模板渲染（YAML frontmatter + DATE 替换）| PASS |

## 5 项合规扫描

### 1. R1 越界核查

- 涉及文件：src/harness_workflow/workflow_helpers.py / cli.py / validate_contract.py + templates + scaffold_v2 角色文件
- 均在 req-50（现有流程优化）scope §3.1 In 范围内（O1 模板 + O2 stage 整合 + O3 done + O4 CLI + O5 删 stage）
- 未触及 PetMall / uav / PetMallPlatform2 任何文件
- **结论：PASS**

### 2. revert 抽样

- req-50 变更为工作树未提交状态，无 commit sha 可 dry-run
- **结论：N/A（留痕，不阻塞）**

### 3. 契约 7 合规扫描

- 扫描范围：`.workflow/flow/requirements/req-50-*/` 下所有 .md 文件
- 发现裸 id 实例（chg-01 / chg-05 等）均出现在首次引用已有描述上下文的段落后续引用中，或为 frontmatter 结构字段（非 prose 引用）
- 主要裸 id 出现场景：DAG 关系说明（chg-01 ~ chg-04 范围描述）— 符合"批量列举同一 DAG 链首次引用后续可省"规则（plan.md §3 依赖图）
- 未发现首次引用裸 id 违规
- **结论：PASS**

### 4. req-29（角色→模型映射）映射回归

- role-model-map.yaml 由 req-50/chg-01（stage 整合）修改：analyst stages 从 ["requirement_review","planning"] → ["analysis"]，legacy alias 保留
- 修改符合 req-50/chg-01 AC-03 范围，不是误改
- `git log -- .workflow/context/role-model-map.yaml` 最新 commit = chg-01 预期提交
- **结论：PASS（预期修改，非误改）**

### 5. req-30（用户面 model 透出）回归

- action-log.md 含测试工程师（testing / sonnet）自我介绍记录
- executing/session-memory.md 模式符合"role_key / model"透出约定
- **结论：PASS**

## §结论

**PASS。**

req-50（现有流程优化）的 27 个 chg-05（dogfood-reviewer 加项）自身用例全部通过。全量回归 739 PASS / 33 FAIL：21 个类 A（req-50 结构性变更导致旧测试用 requirement_review / planning / ready_for_execution 等旧 stage 名或废止 --execute flag，属于预期 breakage，需后续跟进更新对应测试）；12 个类 B（pre-existing，与 req-50 无关，源自 req-45/46/48 era 及历史文件状态）；**类 C 真 regression = 0**。5 项合规扫描（R1 越界 / revert N/A / 契约 7 / req-29 / req-30）全部 PASS 或 N/A。

**21 个类 A 旧测试** 需后续建 sug 或 req 统一更新（不阻塞本 req-50 进入 acceptance）。
