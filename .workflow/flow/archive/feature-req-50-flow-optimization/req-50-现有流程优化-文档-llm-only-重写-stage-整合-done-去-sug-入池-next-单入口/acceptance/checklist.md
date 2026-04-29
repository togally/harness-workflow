---
id: req-50
title: 现有流程优化：文档 LLM-only 重写 + stage 整合 + done 去 sug 入池 + next 单入口
stage: acceptance
created_at: 2026-04-28
operation_type: acceptance-checklist
verdict: PASS
---

# Acceptance Checklist — req-50（现有流程优化）

## AC 校验矩阵

| AC | 关联 chg | 验收口径 | 结论 | 证据 |
|----|---------|---------|------|------|
| AC-01 | chg-03（核心机器型文档重写）+ chg-04（验证交付文档重写） | 12+ 模板无禁止 header（背景/历史/修订说明/用户原话） | ✅ PASS | `harness validate --contract llm-only-docs` exit 0；grep 模板全集命中 = 0 |
| AC-02 | chg-03 + chg-04 | frontmatter 含 id/title/created_at/operation_type；行数 ≤ 原 50% | ✅ PASS | 核心模板 28–33 行（精简形态）；frontmatter 验证 dogfood TC-05 PASS；llm-only-docs lint PASS |
| AC-03 | chg-01（stage 整合 + next 单入口） | WORKFLOW_SEQUENCE = ['analysis','executing','testing','acceptance','done'] | ✅ PASS | `python3 -c "from harness_workflow.workflow_helpers import WORKFLOW_SEQUENCE; print(WORKFLOW_SEQUENCE)"` 输出符合；test-report.md TC-01 PASS |
| AC-04 | chg-01 | WORKFLOW_SEQUENCE 不含 ready_for_execution；stage_policies 无 ready_for_execution（除 legacy 兼容段） | ✅ PASS | dogfood TC-01 PASS；role-model-map.yaml stage_policies 主序列无 ready_for_execution key；test-report.md TC-02 PASS |
| AC-05 | chg-02（done 去 sug 入池） | done.md Step 6 无 sug 入池；退出条件无"改进建议已提取"；done 不创建 sug 文件 | ✅ PASS | done.md Step 6 = "输出回顾报告"（无"建议转 suggest 池"）；退出条件无"改进建议已提取"；test-report.md TC-06/TC-07 PASS |
| AC-06 | chg-01 | cli.py 移除 --execute flag；`harness next --execute` 报 unknown flag | ✅ PASS | `python3 -m harness_workflow.cli next --execute` exit=2 + "unrecognized arguments: --execute"；cli.py 无 add_argument("--execute") |
| AC-07 | chg-01 | stage_policies.analysis.exit_decision = user；ff 模式自动跳 | ✅ PASS | role-model-map.yaml analysis.exit_decision = user；dogfood TC-03 test_no_execute_flag_needed PASS |
| AC-08 | chg-05（dogfood + reviewer 加项） | 端到端 dogfood 5-stage 全流程 PASS；新模板正确渲染 | ✅ PASS | tests/test_req50_dogfood.py 27 passed；TC01/TC02/TC03/TC04/TC05/TC06 全覆盖 |
| AC-09 | chg-05 | reviewer.md + review-checklist.md 含 LLM-only lint / 新加 stage 自检合并 / 不得回退 done 入池 3 条 | ✅ PASS | reviewer.md 含 4 处 LLM-only 引用；review-checklist.md 含 5 处；dogfood TC-06 9 用例全 PASS |
| AC-10 | chg-05 | `harness validate --human-docs` exit 0；`--contract artifact-placement` exit 0；`--contract test-case-design-completeness` exit 0；`--contract llm-only-docs` exit 0 | ⚠️ 部分 PASS | artifact-placement exit 0 ✅；llm-only-docs exit 0 ✅；test-case-design-completeness exit 1（req-41/bugfix-5 pre-existing，与 req-50 无关）；human-docs exit 1（D-11=B 留痕放行：raw_artifact ✓，交付总结.md 待 done 阶段产出） |
| AC-11 | chg-03 + chg-04 | req-02~req-49 归档文档未被改写；新模板仅对 req-id≥50 生效 | ✅ PASS | git diff HEAD 历史 req 路径 = 0 行；dogfood TC-02 legacy compat PASS |

## AC-10 说明

- `test-case-design-completeness` exit 1：所有失败项均在 req-41（机器型工件回 flow）+ bugfix-5（同角色跨 stage 硬门禁）中——这两组文件在 req-50 之前已存在且 req-50 未改动，属于 pre-existing；类 B 分类与 test-report.md §分类一致。
- `human-docs` exit 1：D-11=B 历史决策（req-46 roadmap.md §7 D-11）：raw_artifact(requirement.md) ✓，交付总结.md 待 done 阶段产出，acceptance 阶段留痕放行，不阻塞。

## 结论

**PASS。**

AC-01 ~ AC-09 / AC-11 全部 PASS；AC-10 部分 PASS（2 项 pre-existing，非 req-50 引入，D-11=B 留痕放行）。
req-50（现有流程优化）5 chg 全部落地经 executing + testing 验证，无类 C 真 regression，验收通过。
