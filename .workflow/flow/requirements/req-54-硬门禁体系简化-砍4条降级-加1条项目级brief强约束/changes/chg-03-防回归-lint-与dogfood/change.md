---
id: chg-03
title: "防回归-lint-与dogfood"
parent_req: req-54
operation_type: change
---

## Goal

为 chg-01 + chg-02 落地的文档改动写自动化防回归 lint，并在 fresh repo 跑 `harness validate --contract all` 全 PASS 自证（dogfood）。

## Scope

### In scope

- 新增测试文件 `tests/test_req54_hard_gate_simplify.py`（≥ 6 TC，覆盖 AC-09 + AC-10）：
  - TC-01：WORKFLOW.md 全局硬门禁段砍 2 条
  - TC-02：base-role.md 「## 硬门禁一」标题已改为「## 工具委派指导原则」+ 「## 硬门禁二」标题已改为「## 操作日志指导原则」
  - TC-03：base-role.md 「## 硬门禁八」段落存在 + 段内含 boilerplate 字面 + Step 7.6 / 7.6.1 字面
  - TC-04：harness-manager.md §3.6 块内含「硬门禁八」字面引用
  - TC-05：4 mirror 文件 diff -q 全 silent（subprocess 调用 diff，断言 returncode == 0）
  - TC-06：dogfood—subprocess 跑 `harness install --force-managed` + `harness validate --contract all`（tmp dir，fresh git init），exit 0
- TC-Dogfood-NN 必须含 sug-52 dogfood 必填字段（用例名 / tmpdir / 子进程命令 / stdout 断言 / runtime stage 断言（如适用）/ feedback.jsonl 事件数断言（若适用）/ 对应 AC / P0）。

### Out of scope

- 不动 src/ 实现源码（chg-01 / chg-02 已是文档改动，不需要 helper）
- 不引入新 contract 类型（即不向 `harness validate --contract` 注册新 contract，仅用现有 contract 跑全量 PASS）
- 不动其他 4 个 live 文件（chg-01 / chg-02 已处理）

## Acceptance

- AC-09 / AC-10（来自 req-54 requirement.md）
- pytest tests/test_req54_hard_gate_simplify.py -v 全 PASS（≥ 6 TC）
- 全 suite 不增 fail 数（基线 51 failed / 797 passed，由 req-53 done 阶段确定）

## Dependencies

- 上游：chg-01（4 文件落地）+ chg-02（boilerplate 完整化）
- 下游：testing / acceptance 阶段验收
