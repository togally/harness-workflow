---
id: chg-01
title: trivial 通道命令骨架（CLI + state machine + harness-manager 路由）
req: req-49（工作流轻量级通道：trivial 任务（几行代码）走简化流程）
trivial: false
---

# chg-01（trivial 通道命令骨架）

## 1. Goal

为 trivial 通道搭起 CLI 入口 + runtime state machine 骨架，让 `harness trivial "<title>"` 能创建 task_type=trivial 的工作项，runtime stage 按 `TRIVIAL_SEQUENCE = [trivial_define, executing, done]` 推进，与既有 4 类路径（req / bugfix / sug-direct / ff）并列。

## 2. Scope

### In-Scope

1. **CLI 入口**：在 `src/harness_workflow/cli.py` 增加 `harness trivial "<title>"` 子命令；choices 注册扩 `trivial`；title 参数与 `harness bugfix` 同形态（位置参数 + slug 化）。
2. **runtime.yaml task_type 扩枚举**：从 `[req, bugfix, sug, regression]` 扩到 `[req, bugfix, sug, regression, trivial]`；`workflow_helpers.py` 中 task_type 校验 helper 同步扩。
3. **TRIVIAL_SEQUENCE 常量**：在 `workflow_helpers.py` 新增 `TRIVIAL_SEQUENCE = ["trivial_define", "executing", "done"]`，与既有 `REQUIREMENT_SEQUENCE` / `BUGFIX_SEQUENCE` / `SUG_DIRECT_SEQUENCE` 并列；`get_sequence_for_task_type` 兼容新枚举。
4. **3 stage 状态机扩展**：runtime stage 流转 `trivial_define → executing → done`；`get_next_stage` / `validate_stage` / `is_terminal_stage` 全部扩 trivial 分支。
5. **harness-manager 路由表**：在 `.workflow/context/roles/harness-manager.md` §路由表 加 `harness trivial` → analyst → executing → done 派发链。
6. **`harness suggest --apply --trivial` flag**：扩 `harness suggest --apply <sug-id> --trivial`，把 sug 池建议作为 trivial 任务执行入口（替代默认 sug 直接处理路径）；`task_type` 在该路径写入为 `trivial`。
7. **create_trivial helper**：新增 `create_trivial(title)` helper，落 `.workflow/flow/requirements/{req-id}-{slug}/`（与 req 同 layout，复用既有 `create_requirement` 路径骨架，仅 task_type / sequence 不同）。

### Out-of-Scope

- trivial 准入判据（chg-02）；
- 工件模板压缩（chg-03）；
- trivial-guard 护栏 / 测试降级（chg-04）；
- dogfood + reviewer 加项（chg-05）。

## 3. Acceptance（对应 req-49 AC）

- AC-01（命令可用 + task_type 写入）；
- AC-02（TRIVIAL_SEQUENCE 全链路联通）；
- AC-06（`harness suggest --apply --trivial` flag 可用）；
- AC-09（硬门禁六 / 七 / 契约 7 在 CLI stdout / harness-manager briefing 全覆盖）。

## 4. Dependencies

- 无前置依赖（DAG 起点）。
- 后续 chg-02 / chg-03 / chg-04 / chg-05 全部依赖本 chg 的 task_type 枚举 + TRIVIAL_SEQUENCE 常量。

## 5. Risk

- **风险**：task_type 扩枚举可能漏改 `archive_requirement` / `validate_human_docs` 等下游 helper 的 switch case。**缓解**：grep `task_type ==` 全仓搜，逐一确认；单测 `test_task_type_enum_completeness` 覆盖。
- **风险**：harness-manager 路由表新增条目格式与既有不一致。**缓解**：参考 `harness suggest --apply` 路由实现，逐字段对齐。
