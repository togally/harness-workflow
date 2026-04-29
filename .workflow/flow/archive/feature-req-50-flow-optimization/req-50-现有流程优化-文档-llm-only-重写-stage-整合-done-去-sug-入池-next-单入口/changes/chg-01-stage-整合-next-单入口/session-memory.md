---
chg_id: chg-01
title: stage 整合 + next 单入口
status: completed
ts: 2026-04-28T00:00:00+00:00
---

## 改动文件清单

**src/**
- `src/harness_workflow/workflow_helpers.py` — WORKFLOW_SEQUENCE 改写、agent guidance 文本同步、stale 引用清理
- `src/harness_workflow/cli.py` — `--execute` flag 废止
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/index.md` — scaffold mirror 同步
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/role-model-map.yaml` — scaffold mirror 同步
- `src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/analyst.md` — scaffold mirror 同步

**.workflow/context/**
- `.workflow/context/index.md` — Stage 出口决策表更新（删 requirement_review / planning / ready_for_execution 行，新增 analysis 行）
- `.workflow/context/role-model-map.yaml` — analyst.stages 改 ["analysis"]，stage_policies 新增 analysis，legacy alias 段保留
- `.workflow/context/roles/analyst.md` — 覆盖 stage 改 [analysis]，退出条件合并为单段

## 核心变更

- `WORKFLOW_SEQUENCE` 由 7 项改为 5 项：`["analysis", "executing", "testing", "acceptance", "done"]`
- `cli.py` 删除 `--execute` flag 注册及相关分支（`harness next --execute` 不再生效）
- `workflow_helpers.py` agent guidance 文本全面同步：harness-next / constraint / context-window 三类文本内 `ready_for_execution` / `requirement_review` 引用改为 `analysis`
- `role-model-map.yaml` + `analyst.md` + `index.md`：analyst 覆盖 stage 由两 stage 改为单一 analysis；stage_policies 新增 analysis（exit_decision: user）
- D5=B 兼容机制保留：`_normalize_legacy_stage`，legacy stage 名在 workflow_next 路径 WARN 并迁移，归档历史 yaml 不动

## 测试

暂无新增 unit test；单测与 dogfood 集成留待 chg-05 覆盖（TC-01 ~ TC-Dogfood-02，见 plan.md）。

## 硬序约束完成情况

- ✅ Step 1：workflow_helpers.py WORKFLOW_SEQUENCE + workflow_next + _NO_BRIEFING_STAGES 改写
- ✅ Step 2：role-model-map.yaml analyst.stages / stage_policies 更新
- ✅ Step 3：cli.py --execute flag 移除
- ⬜ Step 4：ff_auto.py analysis→executing ack 逻辑（后续 chg 覆盖或自动跟随）
- ✅ Step 5：context/index.md + analyst.md + role-model-map.yaml 同步更新
- ✅ Step 6：scaffold_v2 mirror 同步（index.md / role-model-map.yaml / analyst.md）
- ⬜ Step 7：.workflow/flow/stages.md 流转规则文档更新（待后续 chg-03/chg-04）

✅
