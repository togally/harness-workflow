---
id: bugfix-6
title: 工作流契约统一加固（对人机器分离 + 测试契约重塑）
created_at: 2026-04-26
bugfix_link: ./bugfix.md
diagnosis_link: ./regression/diagnosis.md
test_evidence_link: ./test-evidence.md
acceptance_link: ./acceptance/checklist.md
---

# bugfix 交付总结：bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））

## bugfix 是什么

融合 bugfix，一次性收口用户 2026-04-25 夜连续提出的 3+1 件未决工作流契约问题：对人/机器型工件路径关注点分离强化（事项 A，吸收 sug-30（bugfix 路径关注点分离）+ 扩契约面到任意任务类型）+ 测试契约重塑（事项 B，把测试用例设计权责前移到 planning，testing 仅执行）+ bugfix 流程的 planning 等价载体补齐（事项 C，diagnosis.md 担纲）+ 附带决策（事项 D，sug-31（done 后 commit + revert dry-run）/ sug-32（回 req-43（交付总结完善）跑 next 自证）不吸收）。详见 [bugfix.md](./bugfix.md)。

## 修了什么

13 修复点（B6 降级为 sug-33（briefing 话术 lint），实际落地 13）按 A/B/C 块汇总：

- **事项 A 块（路径关注点分离，5 点）**：A1 `create_bugfix` 路径迁移到 `.workflow/flow/bugfixes/`（关键文件：`workflow_helpers.py:create_bugfix`）；A2 复核 `create_suggestion / create_change / create_requirement` 合规无须改；A3 新增 `harness validate --contract artifact-placement` lint（关键文件：`validate_contract.py:check_artifact_placement` + `cli.py:255`）；A4 `repository-layout.md §3.2` + 各 role.md 路径表述修正；A5 `harness migrate bugfix-layout` 子命令 + bugfix-1~5 存量迁移（关键文件：`workflow_helpers.py:migrate_bugfix_layout` + `tools/harness_migrate.py`）。
- **事项 B 块（测试契约重塑，5 点 + B6 降级为 sug-33）**：B1 `analyst.md Step B2.5` 测试用例设计前移到 planning；B2 `testing.md Step 2/2.5` 改写为"读取 plan.md §测试用例设计 → 实现单测"；B3 `evaluation/testing.md §0` targeted 默认 + 4 条全量触发条件；B4 `change-plan.md.tmpl §4` 测试用例设计章节 + 双语 mirror；B5 `harness validate --contract test-case-design-completeness` lint（关键文件：`validate_contract.py:check_test_case_design_completeness`）；**B6 → sug-33（briefing 话术 lint：拦截 testing 全量回归 over-instructing）**。
- **事项 C 块（bugfix 流程 planning 等价载体，3 点）**：C1 `regression.md Step 4.5` 测试用例设计（bugfix 模式）；C2 `evaluation/regression.md §测试用例设计契约`；C3 B5 lint 规则 3 双向覆盖 plan.md + bugfix diagnosis.md（无新代码）。

## 修复验证

- **62 新用例 100% PASS**：test_bugfix_layout_v2.py (12) + test_validate_artifact_placement.py (9) + test_test_case_design_in_planning.py (14) + test_validate_test_case_design_completeness.py (11) + test_regression_test_case_design.py (16) = 62/62。
- **全量回归 533 PASS**：仅 2 条 pre-existing failure（`test_smoke_req28` / `test_smoke_req29`，与 bugfix-6 无关）。
- **scaffold_v2 mirror diff = 0**：`.workflow/context/roles/` + `.workflow/evaluation/` + `repository-layout.md` 全部同步。
- **acceptance 11 条 checklist**：9 PASS / 2 ⚠️ followup / 0 FAIL → **PASS-with-followup**。
- **dogfood fallback 标注**：本 bugfix 自身是"测试契约重塑"主体，testing 阶段读取的 diagnosis.md §测试用例设计 是 executing 后补加的（旧契约空缺活体证据），test-evidence.md 第 3 行显著标注 fallback 来源；bugfix-7+ 起应直接消费新契约，不再 fallback。
- **P2 缺陷登记（非阻塞）**：bugfix-5（同角色跨 stage 自动续跑硬门禁） `acceptance/checklist.md` 仍在 `artifacts/main/bugfixes/bugfix-5-.../acceptance/checklist.md`（migrate 脚本当前覆盖 bugfix.md / session-memory.md / regression/ / test-evidence.md 五类主文件，acceptance/ 子目录是新规则覆盖既有残留）。已登记 sug 后续清理。

## 后续建议

- **新增入池 sug**：sug-34（bugfix-5 acceptance/checklist.md 残留迁移，对应 P2 缺陷）/ sug-35（reviewer checklist 扩 artifact-placement / test-case-design-completeness 三类 lint 条目补全）/ sug-36（legacy `.workflow/flow/archive` 与 `artifacts/main/archive/` 双源整合，CLI archive 提示的 `harness migrate archive` 后续）。
- **既有保留 sug**：sug-31（done 后 commit + revert dry-run）/ sug-32（回 req-43（交付总结完善）跑 next 自证）/ sug-33（briefing 话术 lint：拦截 testing 全量回归 over-instructing），用户醒后决定立项 bugfix-7+ 或合并到 req-43（交付总结完善）。
- **5 个用户醒后 followup**：(1) bugfix-5（同角色跨 stage 自动续跑硬门禁）archive；(2) bugfix-6 archive；(3) req-43（交付总结完善）planning 续跑（同时验证 sug-32 + bugfix-5/6 连跳）；(4) sug-31/32/33 处理顺序；(5) bugfix-5 P2 残留清理（sug-34 跟进）。

## 效率与成本

> 数据完整性提示：本 bugfix 周期 `.workflow/state/sessions/{bugfix-id}/usage-log.yaml` **不存在**（sug-25（record_subagent_usage 派发链路真实接通）尚未落地，bugfix 周期未挂 usage 采集 hook）。各子字段按 done.md 规则标 `⚠️ 无数据`，禁止编造。

### 总耗时

- `⚠️ 无数据`（runtime.yaml `stage_entered_at = 2026-04-26T09:37:48` 仅记 done 进入时刻，未留 regression / executing / testing / acceptance 各 stage 进入时间戳；bugfix 流程不写 stage_timestamps 字段）。

### 总 token

| input | output | cache_read | cache_creation | total |
|-------|--------|------------|----------------|-------|
| ⚠️ 无数据 | ⚠️ 无数据 | ⚠️ 无数据 | ⚠️ 无数据 | ⚠️ 无数据 |

### 各阶段耗时分布

| stage | entered_at | duration_s |
|-------|-----------|-----------|
| regression | ⚠️ 无数据 | ⚠️ 无数据 |
| executing | ⚠️ 无数据 | ⚠️ 无数据 |
| testing | ⚠️ 无数据 | ⚠️ 无数据 |
| acceptance | ⚠️ 无数据 | ⚠️ 无数据 |
| done | 2026-04-26T09:37:48+00:00 | ⚠️ 无数据 |

### 各阶段 token 分布

| role | model | total_tokens | tool_uses |
|------|-------|-------------|-----------|
| regression | opus | ⚠️ 无数据 | ⚠️ 无数据 |
| executing | sonnet | ⚠️ 无数据 | ⚠️ 无数据 |
| testing | sonnet | ⚠️ 无数据 | ⚠️ 无数据 |
| acceptance | sonnet | ⚠️ 无数据 | ⚠️ 无数据 |
| done | opus | ⚠️ 无数据 | ⚠️ 无数据 |

> 派发次数 = 5（regression / executing / testing / acceptance / done），usage entries = 0，缺采容差 = 5；待 sug-25 落地后 bugfix-7+ 起可补齐。
