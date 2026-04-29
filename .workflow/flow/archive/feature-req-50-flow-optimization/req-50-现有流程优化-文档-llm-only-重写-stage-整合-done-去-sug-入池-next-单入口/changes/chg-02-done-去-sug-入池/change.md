---
id: chg-02
title: done 阶段去掉 sug 入池职责
requirement: req-50
created_at: 2026-04-29
operation_type: change
---

# Change

## 1. Title

done 阶段去掉 sug 入池职责（O3）

## 2. Goal

把 done 阶段「Step 6: 输出回顾报告与建议转 suggest 池」中的 sug 入池职责完全移除（D4 = A）；done subagent 不再主动扫 `done-report.md` 改进建议、不再调 `create_suggestion`；用户保留主动通过 `harness suggest "<text>"` 入池的能力。

## 3. Requirement

- `req-50（现有流程优化：文档 LLM-only 重写 + stage 整合 + done 去 sug 入池 + next 单入口）`
- 关联 AC：AC-05

## 4. Scope

### Included

- `.workflow/context/roles/done.md`：
  - Step 6 标题改为「输出回顾报告」（删「与建议转 suggest 池」）。
  - 删除 Step 6 内「提取 `done-report.md` 中的改进建议，自动创建 suggest 文件」一行。
  - 删除「## 建议转 suggest 池」整段（约 10 行）。
  - 退出条件删除「`done-report.md` 中的改进建议已提取（如有）」一项。
  - 「完成前必须检查」第 1 项删除。
  - 「禁止的行为」第 3 项「不得遗漏 `done-report.md` 中的改进建议提取」删除。
  - 「允许的行为」「创建 suggest 文件到 `.workflow/flow/suggestions/`」改为「（可选）创建 suggest 文件——仅在用户显式调用 `harness suggest` 时」。
- `.workflow/context/experience/roles/done.md`（如存在 sug 入池相关经验段）：删除或标 `[废止 by req-50 / chg-02]`。
- `.workflow/context/checklists/review-checklist.md`（如有 done 检查项含 sug 入池）：删除对应 lint 项。
- `src/harness_workflow/workflow_helpers.py`：done 阶段相关 helper（如 `done_efficiency_aggregate` 等）保留；但若有 `auto_extract_suggestions_from_done_report` 类 helper，删除或标 deprecated。
- `harness suggest` CLI 入口本身不动（用户主动入口保留）。

### Excluded

- 不动 sug 池 schema（frontmatter 字段 / 状态机不变）。
- 不动 `harness suggest --create` / `--list` / `--apply` / `--delete` / `--archive` CLI 子命令。
- 不动 `done.md` 六层回顾框架本身（Context / Tools / Flow / State / Evaluation / Constraints 六层保留）。
- 不动「## 效率与成本」段（done 仍输出 token / 耗时聚合）。

## 5. Acceptance

- 覆盖 AC-05：
  - `grep -n "sug\|suggest\|建议转" .workflow/context/roles/done.md` 仅命中保留段（如「禁止的行为」更新版 / 「允许的行为」可选段），主动入池路径全删。
  - done subagent SOP 不再含「Step 6 自动提取」分支；落地后跑 dogfood req（chg-05）末尾确认 `.workflow/flow/suggestions/` 不出现新 sug 文件（无论 done-report.md 是否含改进建议段）。
  - 用户 `harness suggest "test sug"` 仍可创建 sug 文件（入口保留）。

## 6. Risks

- 风险：历史经验文件 / experience/ 含「done 阶段必入池」教训误导未来 agent。
  缓解：本 chg 同步扫 `experience/roles/done.md` 与 `experience/index.md`，删除 / 标废止；新经验沉淀到 `experience/roles/done.md` 说明「req-50 后 done 不主动入池」。
- 风险：用户回归"忘了入池"导致改进点遗失。
  缓解：done.md 退出条件加新一行「（可选提示）若回顾发现改进点，可手工 `harness suggest "<text>"` 入池」；属软提示不阻塞。
