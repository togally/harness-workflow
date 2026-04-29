---
id: chg-05
title: dogfood + reviewer 加项 + llm-only-docs lint 收口
requirement: req-50
created_at: 2026-04-29
operation_type: change
---

# Change

## 1. Title

dogfood + reviewer 加项收口（端到端验证 + 反复发硬门禁）

## 2. Goal

端到端在 tmpdir 跑全周期（用 chg-01 ~ chg-04 落地的 LLM-only 文档跑完 5-stage requirement + 5-stage bugfix），验证：(a) `analysis → executing → testing → acceptance → done` 5 stage 流转，零 `ready_for_execution`；(b) 所有产出文档采用新 LLM-only 模板；(c) done 阶段不主动入池。同步加 reviewer.md / review-checklist.md lint 项与新 contract `harness validate --contract llm-only-docs`，防再犯。

## 3. Requirement

- `req-50（现有流程优化：文档 LLM-only 重写 + stage 整合 + done 去 sug 入池 + next 单入口）`
- 关联 AC：AC-08 / AC-09 / AC-10

## 4. Scope

### Included

- 新增 `harness validate --contract llm-only-docs` lint：
  - 扫 `.claude/skills/harness/assets/templates/*.tmpl` 所有 .tmpl 文件。
  - 断言每个文件含 frontmatter `---` 块 + 必填字段 `id` / `title` / `created_at` / `operation_type`。
  - 断言文件 grep `^## .*(背景|历史|修订说明|用户原话|设计理念|演进)` 命中 = 0。
  - 断言连续非 bullet 行 ≤ 3 行（粗略检测「叙事性 prose」）。
  - 任一断言失败：exit 1 + 列违规文件清单。
- 新增 `tests/test_dogfood_req_full_cycle.py`：tmpdir 跑完整 req 5-stage 流程，断言 stage 历史 + 文档产出。
- 新增 `tests/test_dogfood_bugfix_full_cycle.py`：tmpdir 跑完整 bugfix 5-stage 流程，断言 stage 历史 + 文档产出。
- `.workflow/context/roles/reviewer.md`：增补 lint 项：
  - 「新加 / 修改文档模板必须 LLM-only（无背景 / 历史 / 修订说明 / 用户原话段；含 frontmatter 必填字段）」。
  - 「新加 stage 必须自检是否能与现有 stage 合并（同 role 同 model 强烈建议合并）」。
  - 「不得回退 chg-02 的 done 主动入池行为（除非用户显式拍板）」。
- `.workflow/context/checklists/review-checklist.md`：同步增补对应 checklist 项。
- `src/harness_workflow/validate_contract.py`：新增 `_lint_llm_only_docs(root) -> List[Violation]` 函数；`run_contract_cli` 分发到新 lint。
- `src/harness_workflow/cli.py`：`--contract` choices 列表加 `"llm-only-docs"`。

### Excluded

- 不动 chg-01 ~ chg-04 已落地的代码 / 模板。
- 不动现有 contract lint 实现（`artifact-placement` / `test-case-design-completeness` 等保持不变）。
- 不增加新 stage / 新命令。

## 5. Acceptance

- 覆盖 AC-08：dogfood 测试 `test_dogfood_req_full_cycle.py` PASS：tmpdir 跑完 5-stage requirement，runtime stage 历经 `analysis → executing → testing → acceptance → done`，零 `ready_for_execution`，单次 `harness next` 推进 `analysis → executing`（默认人工拍板模拟），所有产出文档（requirement.md / change.md / plan.md / session-memory.md / test-evidence.md / acceptance-report.md / 交付总结.md）含正确 frontmatter。
- 覆盖 AC-08：dogfood 测试 `test_dogfood_bugfix_full_cycle.py` PASS：tmpdir 跑完 bugfix 5-stage 流程（regression → executing → testing → acceptance → done），所有产出文档（bugfix.md / diagnosis.md / session-memory.md / test-evidence.md / bugfix-交付总结.md）含正确 frontmatter。
- 覆盖 AC-09：reviewer.md / review-checklist.md grep 含「LLM-only 文档」「新加 stage 必须自检合并」「不得回退 done 主动入池」三条 lint 项。
- 覆盖 AC-10：`harness validate --contract llm-only-docs` 在主仓库执行 exit 0；`harness validate --contract all` 含 llm-only-docs 项；其他三 contract（artifact-placement / test-case-design-completeness / human-docs）保持 exit 0。

## 6. Risks

- 风险：dogfood 测试在 CI 环境跑不通（路径 / 子进程 / Python 版本差异）。
  缓解：tmpdir 用 `tmp_path` pytest fixture；子进程命令用 `[sys.executable, '-m', 'harness_workflow.cli', ...]`；测试加 `pytest.mark.slow` 标记，CI 单独 job 跑。
- 风险：`llm-only-docs` lint 误报（如某模板正当地含「## 历史接入说明」段）。
  缓解：lint 仅检 `^## .*(背景|历史|修订说明|用户原话|设计理念|演进)` 且支持 `<!-- LLM-ONLY-LINT: skip -->` HTML 注释豁免；同步在新模板中明确不使用这些标题。
- 风险：reviewer 新 lint 项过宽，未来正常修改文档误判。
  缓解：lint 项明确写「新加 / 修改文档模板」，仅在 .tmpl 文件 diff 时触发；非 .tmpl 文件改动豁免。
