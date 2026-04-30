---
id: chg-05
title: "harness playbook-check 子命令"
req: req-55
created_at: 2026-04-30
---

## 1. 执行步骤

1. **读上下文**：读 chg-03 `domain_inference` + chg-04 AUTO marker helper + `validate_contract.py` 现有契约注册风格。
2. **写 `harness_playbook_check.py`**：实现 10 类 `check_*` 函数 + `main(args)` 聚合 dispatch。
3. **改 `cli.py`**：注册 `playbook-check` 子命令；加 `--root` / `--strict` / `--dry-run` flag。
4. **改 `validate_contract.py`**：注册新契约 `playbook-layout`，调本 chg helper。
5. **新增 pytest 用例 ≥ 7 条 + 健康仓库 1 条 + dogfood 1 条**。
6. **跑 pytest**：`pytest tests/test_playbook_check*.py -v`。
7. **dogfood 实跑**：tmpdir + 漂移 fixture + 健康 fixture，subprocess 双向断言。
8. **harness-workflow 自身仓 baseline check**：`python3 -m harness_workflow.cli playbook-check`，断言 exit 0。
9. **harness validate**：`harness validate --contract playbook-layout && harness validate --human-docs`。
10. **session-memory 留痕**：测试数字 + 各 check 函数命中数。

## 2. 产物

- `src/harness_workflow/tools/harness_playbook_check.py`（新增）
- `src/harness_workflow/cli.py`（注册子命令）
- `src/harness_workflow/validate_contract.py`（注册新契约）
- `tests/test_playbook_check.py`（新增，≥ 8 TC）
- `tests/test_playbook_check_dogfood.py`（新增，1 dogfood TC）

## 3. 依赖

- 上游：chg-03（playbook 子包：domain_inference）+ chg-04（AUTO marker helper）。
- 下游：CI 接入闸门；后续 req 可基于 check 结果触发自动 refresh / 通知。

## 4. 测试用例设计

> regression_scope: targeted
> 波及接口清单：
> - src/harness_workflow/tools/harness_playbook_check.py（新增，扫描路径 = `artifacts/project/playbooks/`，OQ-1=B）
> - src/harness_workflow/cli.py（注册子命令）
> - src/harness_workflow/validate_contract.py（注册新契约名 `playbook-layout`）
> - 复用：playbook/domain_inference.py + tools/harness_playbook_refresh.py
> - OQ-5 兜底：AUTO 区段漂移检测（路书只读软约束 + CI 兜底）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 dependency 漂移 fixture | 新 dep 未提及 architecture.md | exit ≠ 0 + stdout 含 'dependency drift' | AC-05.1 | P0 |
| TC-02 scripts 漂移 fixture | 新 script 未提及 runbook.md | exit ≠ 0 + stdout 含 'scripts drift' | AC-05.1 | P0 |
| TC-03 模块目录漂移 fixture | 新 src/modules/foo/ 无 domains/foo/ | exit ≠ 0 | AC-05.1 | P0 |
| TC-04 codemap 互引漂移 fixture | domains/auth/ 存在但 code-map.md 无登记 | exit ≠ 0 | AC-05.1 | P0 |
| TC-05 code.md 引用失效 fixture | code.md 引用 src/foo.ts 但文件不存在 | exit ≠ 0 | AC-05.1 | P0 |
| TC-06 README 依赖链接失效 fixture | "依赖: nonexistent" 链接失效 | exit ≠ 0 | AC-05.1 | P0 |
| TC-07 关键词为空 fixture | code-map.md 某领域关键词为空 | exit ≠ 0 + stdout 含 'empty keywords' | AC-05.1 | P0 |
| TC-08 健康仓库 exit 0 | 完整健康 fixture | exit 0 + stdout 含 'no drift detected' | AC-05.2 | P0 |
| TC-Dogfood-01 dogfood subprocess 实跑 | tmp_path 健康 fixture + subprocess.run | exit 0 + stdout / runtime / feedback 全断言 | AC-05.3 | P0 |
| TC-09 contract 注册可用 | `harness validate --contract playbook-layout` | exit 与 `playbook-check` 一致 | AC-05.4 | P0 |
| TC-10 自身仓 baseline | harness-workflow 仓根（chg-03/04 落地后）跑 check | exit 0 | AC-05.5 | P1 |
| TC-11 `--strict` flag | TODO ≥ 1 fixture | 默认 exit 0；`--strict` exit 1 | AC-05.6 | P0 |
| TC-12 OQ-5 兜底：AUTO 区段被改但未跑 refresh | fixture：手工编辑 `<!-- AUTO:STACK -->...<!-- /AUTO:STACK -->` 内容但保留 marker 完整 + 项目状态与区段不一致 | exit 1 + stdout 含 "AUTO segment drift detected"（路书只读软约束 + CI 兜底，OQ-5=A） | AC-05.1 / OQ-5 | P0 |
