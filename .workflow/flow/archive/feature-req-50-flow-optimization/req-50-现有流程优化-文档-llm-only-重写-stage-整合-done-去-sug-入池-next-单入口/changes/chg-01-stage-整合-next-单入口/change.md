---
id: chg-01
title: stage 整合（req_review + planning → analysis） + 删 ready_for_execution + next 单入口
requirement: req-50
created_at: 2026-04-29
operation_type: change
---

# Change

## 1. Title

stage 整合 + next 单入口（O2 + O4 + O5 联动）

## 2. Goal

把现有 `WORKFLOW_SEQUENCE` 中的 `requirement_review` + `planning` 合并为单一 `analysis` stage，删除空 stage `ready_for_execution`，移除 `harness next --execute` flag；以 `harness next` 单一入口覆盖所有 stage 流转。

## 3. Requirement

- `req-50（现有流程优化：文档 LLM-only 重写 + stage 整合 + done 去 sug 入池 + next 单入口）`
- 关联 AC：AC-03 / AC-04 / AC-06 / AC-07

## 4. Scope

### Included

- `src/harness_workflow/workflow_helpers.py`：`WORKFLOW_SEQUENCE` 改为 `["analysis", "executing", "testing", "acceptance", "done"]`；`workflow_next` 删除 `if current_stage == "ready_for_execution" and not execute` 分支；删除 `_NO_BRIEFING_STAGES` 中的 `ready_for_execution`。
- `src/harness_workflow/cli.py`：`next_parser` 移除 `--execute` flag；`if args.command == "next"` 分支删除 `cmd_args.append("--execute")`。
- `src/harness_workflow/ff_auto.py`：sequence 引用同步更新；ff 模式下 `analysis → executing` 自动跳（D3 = A 默认人工拍板，ff 跳）。
- `.workflow/context/role-model-map.yaml`：`stage_policies` 删除 `ready_for_execution`；新增 `analysis: { exit_decision: user }`；删除独立 `requirement_review` / `planning` policies，改为 alias 转向 `analysis`。
- `.workflow/context/index.md`：角色索引表的 `stages` 列同步更新（analyst 覆盖 stage 改为 `analysis`）；stage_policies 镜像表更新。
- `.workflow/context/roles/stage-role.md`：流转点豁免子条款引用更新（`requirement_review → planning` 改为 stage 内部子步骤）。
- `.workflow/context/roles/analyst.md`：覆盖 stage 改 `[analysis]`；SOP Part A / Part B 结构保留但开头说明改为「同 stage 内两阶段」。
- `.workflow/context/roles/harness-manager.md`：派发 / 流转引用 stage 名同步更新；删除 `--execute` 提示句。
- `.workflow/state/runtime.yaml`：本 req 自身（req-50）当前 stage 为 `requirement_review`（chg-01 落地后由 CLI 自然推进；不强行改写历史 stage）。
- `.workflow/flow/stages.md`：流转规则文档同步更新。

### Excluded

- 不动归档历史 req 的 `stage_timestamps` 旧字段（req-02 ~ req-49 保留 `requirement_review` / `planning` / `ready_for_execution` 字段，legacy 兼容）。
- 不动 `BUGFIX_SEQUENCE` 与 `SUGGESTION_SEQUENCE`（用户拍板范围不含）。
- 不动文档模板（O1 由 chg-03 / chg-04 处理）。

## 5. Acceptance

- 覆盖 AC-03：`grep -rn "requirement_review\|planning" src/ .workflow/context/role-model-map.yaml` 主路径不再命中（除 legacy alias）；`WORKFLOW_SEQUENCE` 等于 `["analysis", "executing", "testing", "acceptance", "done"]`。
- 覆盖 AC-04：`grep -rn "ready_for_execution" src/ | grep -v archive | grep -v legacy` 命中 = 0；`stage_policies` 无 `ready_for_execution` key。
- 覆盖 AC-06：`harness next --execute` 报 `unknown flag` 错误；CLI `next_parser` 不再注册 `--execute`。
- 覆盖 AC-07：`stage_policies.analysis.exit_decision == "user"`；ff 模式 e2e 跑通 `analysis → executing` 自动跳。

## 6. Risks

- 风险：归档历史 req（含 `requirement_review` / `planning` / `ready_for_execution` 时间戳）回放 / 引用断裂。
  缓解：role-model-map.yaml 保留 legacy alias `requirement-review` / `planning` / `ready_for_execution`，alias_of 指向 `analysis` 或为 deprecated；归档 yaml `stage_timestamps` 旧字段保留不迁移；`workflow_helpers.py` 加 legacy fallback：读到旧 stage 名时 stderr WARN 不 raise。
- 风险：`--execute` flag 移除后 README / experience 文档残留。
  缓解：本 chg grep 全仓库引用一并清理；release notes 高亮废止信息。
- 风险：ff 模式 auto-advance 链路坏掉。
  缓解：本 chg 包含 ff_auto.py 同步更新 + chg-05 dogfood 端到端验证。
