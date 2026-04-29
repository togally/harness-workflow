---
req_id: req-50
stage: executing
ts: 2026-04-28T00:00:00+00:00
---

## chg 执行状态

| chg | title | 状态 |
|-----|-------|------|
| chg-01 | stage 整合 + next 单入口 | ✅ completed |
| chg-02 | done 去 sug 入池 | ✅ completed |
| chg-03 | 文档重写-核心机器型 | ✅ completed |
| chg-04 | 文档重写-验证交付 | ✅ completed |
| chg-05 | dogfood-reviewer 加项 | ✅ completed |

## chg-01 完成摘要

- WORKFLOW_SEQUENCE 改为 5 项（analysis / executing / testing / acceptance / done）
- cli.py --execute flag 废止
- workflow_helpers.py agent guidance 文本全面同步（stale 引用清理完毕）
- role-model-map.yaml + analyst.md + index.md + scaffold_v2 mirror 同步
- D5=B legacy 兼容机制保留（归档历史 req-02~req-49 不受影响）

## chg-03 完成摘要

- 10 个模板（中英双版）重写为 YAML frontmatter + 紧凑 markdown（D1=B）
- 删除全部「对人解释」段落，grep 禁止 header = 0 命中
- double-write：dev 路径 + package 路径同步
- render_template dogfood 验证通过（DATE 替换正确，无报错）

## chg-04 完成摘要

- 15 个模板（中英双版）重写为 YAML frontmatter + 紧凑 markdown（D1=B）
- 目标：diagnosis / regression-decision / regression-required-inputs / regression-analysis / regression / test-cases / test-plan / acceptance-checklist / requirement-completion（中英双版）
- 删除全部「对人解释」段落，grep 禁止 header = 0 命中
- double-write：dev 路径 + package 路径同步
- render_template dogfood 15 模板全部验证通过
- acceptance-checklist.md.tmpl 含 `## §结论` heading（CLI gate 兼容）

## 备注

全部 5 个 chg 已完成（chg-01 ~ chg-05）。chg-05 完成摘要见下方。

## chg-05 完成摘要

- reviewer.md + review-checklist.md 追加 3+4 段 lint 项 + scaffold mirror 同步
- validate_contract.py 新增 `_lint_llm_only_docs()` + llm-only-docs contract 分支
- cli.py `--contract choices` 追加 llm-only-docs
- tests/test_req50_dogfood.py：6 TC 共 27 测试用例全部 PASS
- 全量回归：33 failed（全部历史失败，chg-05 零新增 fail）

✅
